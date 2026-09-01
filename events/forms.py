import re

from django import forms
from django.forms import inlineformset_factory
from django.utils import timezone

from .models import Booking, Event, Payment, TicketCategory

MAX_TICKETS_PER_BOOKING = 10

# Cameroonian mobile numbers: 9 local digits, optionally prefixed by +237/237.
CAMEROON_PHONE_RE = re.compile(r'^(?:\+?237)?6\d{8}$')


def normalize_phone(value):
    """Strip spaces/dashes from a phone number so it can be validated."""
    return re.sub(r'[\s\-().]', '', value or '')


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            'title',
            'description',
            'venue',
            'city',
            'starts_at',
            'ends_at',
            'cover_image_url',
            'is_published',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'starts_at': forms.DateTimeInput(
                attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'
            ),
            'ends_at': forms.DateTimeInput(
                attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name == 'is_published':
                continue
            field.widget.attrs.setdefault(
                'class',
                'w-full rounded-lg border border-slate-300 px-3 py-2 '
                'focus:border-emerald-500 focus:outline-none',
            )

    def clean(self):
        cleaned = super().clean()
        starts_at = cleaned.get('starts_at')
        ends_at = cleaned.get('ends_at')
        if starts_at and ends_at and ends_at < starts_at:
            self.add_error('ends_at', 'The end time must come after the start time.')
        return cleaned


TicketCategoryFormSet = inlineformset_factory(
    Event,
    TicketCategory,
    fields=['name', 'description', 'price', 'quantity'],
    extra=3,
    can_delete=True,
    min_num=1,
    validate_min=True,
)


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['category', 'full_name', 'email', 'phone', 'quantity']

    def __init__(self, *args, event=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.event = event
        if event is not None:
            self.fields['category'].queryset = event.categories.all()
        self.fields['quantity'].min_value = 1
        self.fields['quantity'].widget.attrs.update(
            {'min': 1, 'max': MAX_TICKETS_PER_BOOKING}
        )
        for field in self.fields.values():
            field.widget.attrs.setdefault(
                'class',
                'w-full rounded-lg border border-slate-300 px-3 py-2 '
                'focus:border-emerald-500 focus:outline-none',
            )

    def clean_phone(self):
        phone = normalize_phone(self.cleaned_data['phone'])
        if not CAMEROON_PHONE_RE.match(phone):
            raise forms.ValidationError(
                'Enter a valid Cameroonian mobile number, e.g. 6XXXXXXXX.'
            )
        return phone

    def clean_quantity(self):
        quantity = self.cleaned_data['quantity']
        if quantity < 1:
            raise forms.ValidationError('You must book at least one ticket.')
        if quantity > MAX_TICKETS_PER_BOOKING:
            raise forms.ValidationError(
                f'You can book at most {MAX_TICKETS_PER_BOOKING} tickets at a time.'
            )
        return quantity

    def clean(self):
        cleaned = super().clean()
        category = cleaned.get('category')
        quantity = cleaned.get('quantity')
        if self.event and self.event.is_past:
            raise forms.ValidationError('This event has already taken place.')
        if category and quantity and quantity > category.tickets_remaining:
            self.add_error(
                'quantity',
                f'Only {category.tickets_remaining} ticket(s) left in this category.',
            )
        return cleaned


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['provider', 'phone_number']
        widgets = {'provider': forms.RadioSelect}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['provider'].choices = Payment.Provider.choices
        self.fields['phone_number'].widget.attrs.update(
            {
                'placeholder': '6XXXXXXXX',
                'class': 'w-full rounded-lg border border-slate-300 px-3 py-2 '
                'focus:border-emerald-500 focus:outline-none',
            }
        )

    def clean_phone_number(self):
        phone = normalize_phone(self.cleaned_data['phone_number'])
        if not CAMEROON_PHONE_RE.match(phone):
            raise forms.ValidationError(
                'Enter the mobile money number in the format 6XXXXXXXX.'
            )
        return phone


class TicketScanForm(forms.Form):
    """Manual entry fallback for the organizer scanner."""

    code = forms.CharField(
        label='Ticket code',
        max_length=200,
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Paste or scan the ticket code',
                'autofocus': 'autofocus',
                'class': 'w-full rounded-lg border border-slate-300 px-3 py-2',
            }
        ),
    )


def upcoming_events_queryset(queryset):
    return queryset.filter(is_published=True, starts_at__gte=timezone.now())
