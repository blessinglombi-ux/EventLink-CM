import io
import re
import uuid

import qrcode
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction
from django.db.models import Count, Prefetch, Q, Sum
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import (
    BookingForm,
    EventForm,
    PaymentForm,
    TicketCategoryFormSet,
    TicketScanForm,
)
from .models import Booking, Event, Payment, Ticket, TicketCategory

UUID_RE = re.compile(
    r'[0-9a-f]{8}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{12}',
    re.IGNORECASE,
)


def extract_ticket_code(raw_value):
    """Return the ticket UUID contained in a scanned payload, or None.

    The QR code encodes a check-in URL, but organizers may also paste the bare
    code, so both forms are accepted.
    """
    match = UUID_RE.search(raw_value or '')
    if not match:
        return None
    try:
        return uuid.UUID(match.group(0))
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Public (attendee) views
# ---------------------------------------------------------------------------


def event_list(request):
    query = request.GET.get('q', '').strip()
    events = (
        Event.objects.filter(is_published=True)
        .select_related('organizer')
        .prefetch_related('categories')
    )
    if query:
        events = events.filter(
            Q(title__icontains=query)
            | Q(city__icontains=query)
            | Q(venue__icontains=query)
            | Q(description__icontains=query)
        )
    upcoming = events.filter(starts_at__gte=timezone.now())
    past = events.filter(starts_at__lt=timezone.now()).order_by('-starts_at')[:6]
    return render(
        request,
        'events/event_list.html',
        {'events': upcoming, 'past_events': past, 'query': query},
    )


def event_detail(request, slug):
    event = get_object_or_404(
        Event.objects.select_related('organizer').prefetch_related('categories'),
        slug=slug,
    )
    if not event.is_published and event.organizer_id != request.user.id:
        raise Http404('Event not available')
    return render(request, 'events/event_detail.html', {'event': event})


def booking_create(request, slug):
    event = get_object_or_404(
        Event.objects.prefetch_related('categories'), slug=slug, is_published=True
    )
    if request.method == 'POST':
        form = BookingForm(request.POST, event=event)
        if form.is_valid():
            with transaction.atomic():
                category = TicketCategory.objects.select_for_update().get(
                    pk=form.cleaned_data['category'].pk
                )
                quantity = form.cleaned_data['quantity']
                if quantity > category.tickets_remaining:
                    form.add_error(
                        'quantity',
                        f'Only {category.tickets_remaining} ticket(s) left in this '
                        'category.',
                    )
                else:
                    booking = form.save(commit=False)
                    booking.event = event
                    booking.category = category
                    booking.save()
                    if booking.is_free:
                        booking.issue_tickets()
                        messages.success(
                            request,
                            'Your free ticket(s) have been issued. '
                            'Keep the QR code safe, it can only be used once.',
                        )
                        return redirect('booking_detail', reference=booking.reference)
                    return redirect('payment_checkout', reference=booking.reference)
    else:
        form = BookingForm(event=event)
    return render(
        request, 'events/booking_create.html', {'event': event, 'form': form}
    )


def payment_checkout(request, reference):
    booking = get_object_or_404(
        Booking.objects.select_related('event', 'category'), reference=reference
    )
    if booking.status == Booking.Status.CONFIRMED:
        return redirect('booking_detail', reference=booking.reference)
    if booking.is_free:
        booking.issue_tickets()
        return redirect('booking_detail', reference=booking.reference)

    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment, _ = Payment.objects.get_or_create(
                booking=booking,
                defaults={
                    'provider': form.cleaned_data['provider'],
                    'phone_number': form.cleaned_data['phone_number'],
                    'amount': booking.total_amount,
                },
            )
            payment.provider = form.cleaned_data['provider']
            payment.phone_number = form.cleaned_data['phone_number']
            payment.amount = booking.total_amount
            payment.save()
            # A real deployment plugs the MTN MoMo / Orange Money collection API
            # in here; the sandbox confirms the collection immediately.
            payment.mark_successful()
            messages.success(
                request,
                f'Payment of {payment.amount} XAF confirmed via '
                f'{payment.get_provider_display()}.',
            )
            return redirect('booking_detail', reference=booking.reference)
    else:
        form = PaymentForm(initial={'phone_number': booking.phone})
    return render(
        request, 'events/payment_checkout.html', {'booking': booking, 'form': form}
    )


def booking_detail(request, reference):
    booking = get_object_or_404(
        Booking.objects.select_related('event', 'category').prefetch_related('tickets'),
        reference=reference,
    )
    return render(request, 'events/booking_detail.html', {'booking': booking})


def ticket_detail(request, code):
    ticket = get_object_or_404(
        Ticket.objects.select_related('booking__event', 'booking__category'), code=code
    )
    return render(request, 'events/ticket_detail.html', {'ticket': ticket})


def ticket_qr(request, code):
    """Render the personalised, single-use QR code of a ticket as a PNG."""
    ticket = get_object_or_404(Ticket, code=code)
    target = request.build_absolute_uri(reverse('scan_ticket', args=[ticket.code]))
    image = qrcode.make(target)
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    response = HttpResponse(buffer.getvalue(), content_type='image/png')
    response['Cache-Control'] = 'no-store'
    return response


# ---------------------------------------------------------------------------
# Organizer views
# ---------------------------------------------------------------------------


def organizer_signup(request):
    if request.user.is_authenticated:
        return redirect('organizer_dashboard')
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Welcome to EventLink CM!')
            return redirect('organizer_dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})


@login_required
def organizer_dashboard(request):
    events = (
        Event.objects.filter(organizer=request.user)
        .prefetch_related('categories')
        .annotate(
            issued=Count('bookings__tickets', distinct=True),
            attended=Count(
                'bookings__tickets',
                filter=Q(bookings__tickets__is_checked_in=True),
                distinct=True,
            ),
        )
    )
    revenue = (
        Payment.objects.filter(
            booking__event__organizer=request.user,
            status=Payment.Status.SUCCESSFUL,
        ).aggregate(total=Sum('amount'))['total']
        or 0
    )
    totals = {
        'events': events.count(),
        'tickets': sum(event.issued for event in events),
        'attended': sum(event.attended for event in events),
        'revenue': revenue,
    }
    totals['attendance_rate'] = (
        round(totals['attended'] / totals['tickets'] * 100, 1)
        if totals['tickets']
        else 0
    )
    return render(
        request,
        'events/organizer_dashboard.html',
        {'events': events, 'totals': totals},
    )


@login_required
def event_create(request):
    if request.method == 'POST':
        form = EventForm(request.POST)
        formset = TicketCategoryFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                event = form.save(commit=False)
                event.organizer = request.user
                event.save()
                formset.instance = event
                formset.save()
            messages.success(request, 'Event published successfully.')
            return redirect('event_statistics', slug=event.slug)
    else:
        form = EventForm()
        formset = TicketCategoryFormSet()
    return render(
        request,
        'events/event_form.html',
        {'form': form, 'formset': formset, 'is_create': True},
    )


@login_required
def event_update(request, slug):
    event = get_object_or_404(Event, slug=slug, organizer=request.user)
    if request.method == 'POST':
        form = EventForm(request.POST, instance=event)
        formset = TicketCategoryFormSet(request.POST, instance=event)
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                form.save()
                formset.save()
            messages.success(request, 'Event updated.')
            return redirect('event_statistics', slug=event.slug)
    else:
        form = EventForm(instance=event)
        formset = TicketCategoryFormSet(instance=event)
    return render(
        request,
        'events/event_form.html',
        {'form': form, 'formset': formset, 'event': event, 'is_create': False},
    )


@login_required
def event_statistics(request, slug):
    event = get_object_or_404(
        Event.objects.prefetch_related(
            Prefetch('categories', queryset=TicketCategory.objects.all())
        ),
        slug=slug,
        organizer=request.user,
    )
    categories = []
    for category in event.categories.all():
        issued = category.tickets_issued
        attended = Ticket.objects.filter(
            booking__category=category, is_checked_in=True
        ).count()
        categories.append(
            {
                'category': category,
                'issued': issued,
                'attended': attended,
                'remaining': category.tickets_remaining,
                'revenue': category.price * issued,
                'attendance_rate': round(attended / issued * 100, 1) if issued else 0,
            }
        )
    payments = (
        Payment.objects.filter(
            booking__event=event, status=Payment.Status.SUCCESSFUL
        )
        .values('provider')
        .annotate(total=Sum('amount'), count=Count('id'))
    )
    recent_tickets = (
        Ticket.objects.filter(booking__event=event, is_checked_in=True)
        .select_related('booking')
        .order_by('-checked_in_at')[:10]
    )
    return render(
        request,
        'events/event_statistics.html',
        {
            'event': event,
            'category_stats': categories,
            'payment_breakdown': payments,
            'recent_check_ins': recent_tickets,
        },
    )


@login_required
def event_attendees(request, slug):
    event = get_object_or_404(Event, slug=slug, organizer=request.user)
    tickets = (
        Ticket.objects.filter(booking__event=event)
        .select_related('booking', 'booking__category')
        .order_by('-created_at')
    )
    return render(
        request,
        'events/event_attendees.html',
        {'event': event, 'tickets': tickets},
    )


@login_required
def scanner(request, slug):
    """Camera based scanner page with a manual code entry fallback."""
    event = get_object_or_404(Event, slug=slug, organizer=request.user)
    form = TicketScanForm()
    result = None
    if request.method == 'POST':
        form = TicketScanForm(request.POST)
        if form.is_valid():
            result = _check_in_payload(request, event, form.cleaned_data['code'])
            messages.info(request, result['message'])
            form = TicketScanForm()
    return render(
        request,
        'events/scanner.html',
        {'event': event, 'form': form, 'result': result},
    )


def _check_in_payload(request, event, raw_code):
    """Validate a scanned code against an event and consume the ticket."""
    code = extract_ticket_code(raw_code)
    if code is None:
        return {'status': 'invalid', 'message': 'Unreadable ticket code.'}
    ticket = (
        Ticket.objects.select_related('booking', 'booking__category')
        .filter(code=code)
        .first()
    )
    if ticket is None:
        return {'status': 'invalid', 'message': 'This ticket does not exist.'}
    if ticket.booking.event_id != event.id:
        return {
            'status': 'wrong_event',
            'message': 'This ticket belongs to a different event.',
        }
    if ticket.booking.status != Booking.Status.CONFIRMED:
        return {'status': 'invalid', 'message': 'This booking is not confirmed.'}
    if not ticket.check_in(request.user):
        return {
            'status': 'already_used',
            'message': (
                f'Ticket already used on '
                f'{timezone.localtime(ticket.checked_in_at):%d %b %Y %H:%M}.'
            ),
            'ticket': ticket,
        }
    return {
        'status': 'valid',
        'message': f'Welcome {ticket.holder_name}! Check-in successful.',
        'ticket': ticket,
    }


@login_required
@require_POST
def scan_api(request, slug):
    """JSON endpoint used by the in-browser QR scanner."""
    event = get_object_or_404(Event, slug=slug, organizer=request.user)
    result = _check_in_payload(request, event, request.POST.get('code', ''))
    ticket = result.get('ticket')
    return JsonResponse(
        {
            'status': result['status'],
            'message': result['message'],
            'holder_name': ticket.holder_name if ticket else '',
            'category': ticket.booking.category.name if ticket else '',
            'checked_in': event.tickets_checked_in,
            'issued': event.tickets_issued,
        }
    )


@login_required
def scan_ticket(request, code):
    """Landing page reached when an organizer opens a ticket QR code."""
    ticket = get_object_or_404(
        Ticket.objects.select_related('booking__event', 'booking__category'), code=code
    )
    event = ticket.booking.event
    if event.organizer_id != request.user.id:
        raise Http404('Ticket not available')
    result = None
    if request.method == 'POST':
        result = _check_in_payload(request, event, str(ticket.code))
    return render(
        request,
        'events/scan_result.html',
        {'ticket': ticket, 'event': event, 'result': result},
    )
