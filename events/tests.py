from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Booking, Event, Payment, Ticket, TicketCategory


class BaseTestCase(TestCase):
    def setUp(self):
        self.organizer = User.objects.create_user('organizer', password='str0ngpass!')
        self.event = Event.objects.create(
            organizer=self.organizer,
            title='Douala Tech Summit',
            venue='Akwa Palace',
            city='Douala',
            starts_at=timezone.now() + timedelta(days=7),
        )
        self.free_category = TicketCategory.objects.create(
            event=self.event, name='Free access', price=Decimal('0'), quantity=50
        )
        self.vip_category = TicketCategory.objects.create(
            event=self.event, name='VIP', price=Decimal('10000'), quantity=10
        )

    def book(self, category, quantity=1):
        return self.client.post(
            reverse('booking_create', args=[self.event.slug]),
            {
                'category': category.pk,
                'full_name': 'Ada Ngono',
                'email': 'ada@example.com',
                'phone': '677123456',
                'quantity': quantity,
            },
        )


class EventModelTests(BaseTestCase):
    def test_slug_is_generated_and_unique(self):
        other = Event.objects.create(
            organizer=self.organizer,
            title='Douala Tech Summit',
            venue='Hilton',
            city='Yaounde',
            starts_at=timezone.now() + timedelta(days=8),
        )
        self.assertEqual(self.event.slug, 'douala-tech-summit')
        self.assertNotEqual(other.slug, self.event.slug)

    def test_event_is_not_free_when_a_paid_category_exists(self):
        self.assertFalse(self.event.is_free)
        self.vip_category.delete()
        self.assertTrue(self.event.is_free)

    def test_capacity_and_remaining_tickets(self):
        self.assertEqual(self.event.capacity, 60)
        booking = Booking.objects.create(
            event=self.event,
            category=self.free_category,
            full_name='Ada',
            email='a@example.com',
            phone='677000000',
            quantity=2,
        )
        booking.issue_tickets()
        self.assertEqual(self.event.tickets_issued, 2)
        self.assertEqual(self.event.tickets_remaining, 58)


class FreeBookingTests(BaseTestCase):
    def test_free_booking_issues_tickets_immediately(self):
        response = self.book(self.free_category, quantity=2)
        booking = Booking.objects.get()
        self.assertRedirects(response, booking.get_absolute_url())
        self.assertEqual(booking.status, Booking.Status.CONFIRMED)
        self.assertEqual(booking.tickets.count(), 2)
        self.assertEqual(len({t.code for t in booking.tickets.all()}), 2)

    def test_cannot_book_more_than_remaining_tickets(self):
        response = self.book(self.vip_category, quantity=11)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Booking.objects.count(), 0)

    def test_invalid_phone_number_is_rejected(self):
        response = self.client.post(
            reverse('booking_create', args=[self.event.slug]),
            {
                'category': self.free_category.pk,
                'full_name': 'Ada',
                'email': 'ada@example.com',
                'phone': '12345',
                'quantity': 1,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Booking.objects.count(), 0)


class PaidBookingTests(BaseTestCase):
    def test_paid_booking_requires_payment_before_tickets(self):
        response = self.book(self.vip_category, quantity=2)
        booking = Booking.objects.get()
        self.assertRedirects(
            response, reverse('payment_checkout', args=[booking.reference])
        )
        self.assertEqual(booking.status, Booking.Status.PENDING)
        self.assertEqual(booking.tickets.count(), 0)
        self.assertEqual(booking.total_amount, Decimal('20000'))

    def test_mobile_money_payment_confirms_booking(self):
        self.book(self.vip_category, quantity=2)
        booking = Booking.objects.get()
        response = self.client.post(
            reverse('payment_checkout', args=[booking.reference]),
            {'provider': Payment.Provider.MTN, 'phone_number': '677123456'},
        )
        booking.refresh_from_db()
        payment = booking.payment
        self.assertRedirects(response, booking.get_absolute_url())
        self.assertEqual(payment.status, Payment.Status.SUCCESSFUL)
        self.assertEqual(payment.amount, Decimal('20000'))
        self.assertTrue(payment.transaction_reference)
        self.assertEqual(booking.status, Booking.Status.CONFIRMED)
        self.assertEqual(booking.tickets.count(), 2)

    def test_orange_money_is_supported(self):
        self.book(self.vip_category)
        booking = Booking.objects.get()
        self.client.post(
            reverse('payment_checkout', args=[booking.reference]),
            {'provider': Payment.Provider.ORANGE, 'phone_number': '699123456'},
        )
        self.assertEqual(booking.payment.provider, Payment.Provider.ORANGE)
        self.assertEqual(self.event.revenue, Decimal('10000'))

    def test_payment_page_redirects_once_confirmed(self):
        self.book(self.vip_category)
        booking = Booking.objects.get()
        self.client.post(
            reverse('payment_checkout', args=[booking.reference]),
            {'provider': Payment.Provider.MTN, 'phone_number': '677123456'},
        )
        response = self.client.get(
            reverse('payment_checkout', args=[booking.reference])
        )
        self.assertRedirects(response, booking.get_absolute_url())
        self.assertEqual(booking.tickets.count(), 1)


class TicketTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.book(self.free_category)
        self.ticket = Ticket.objects.get()

    def test_qr_code_image_is_served(self):
        response = self.client.get(reverse('ticket_qr', args=[self.ticket.code]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/png')
        self.assertTrue(response.content.startswith(b'\x89PNG'))

    def test_ticket_detail_is_reachable(self):
        response = self.client.get(reverse('ticket_detail', args=[self.ticket.code]))
        self.assertContains(response, self.ticket.holder_name)


class CheckInTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.book(self.free_category)
        self.ticket = Ticket.objects.get()
        self.scan_url = reverse('scan_api', args=[self.event.slug])

    def scan(self, code):
        return self.client.post(self.scan_url, {'code': str(code)})

    def test_scanner_requires_login(self):
        response = self.scan(self.ticket.code)
        self.assertEqual(response.status_code, 302)

    def test_ticket_can_only_be_used_once(self):
        self.client.force_login(self.organizer)
        first = self.scan(self.ticket.code).json()
        second = self.scan(self.ticket.code).json()
        self.assertEqual(first['status'], 'valid')
        self.assertEqual(second['status'], 'already_used')
        self.ticket.refresh_from_db()
        self.assertTrue(self.ticket.is_checked_in)
        self.assertEqual(self.ticket.checked_in_by, self.organizer)
        self.assertEqual(self.event.tickets_checked_in, 1)

    def test_qr_url_payload_is_accepted(self):
        self.client.force_login(self.organizer)
        payload = f'http://testserver/scan/{self.ticket.code}/'
        self.assertEqual(self.scan(payload).json()['status'], 'valid')

    def test_unknown_code_is_rejected(self):
        self.client.force_login(self.organizer)
        self.assertEqual(self.scan('not-a-ticket').json()['status'], 'invalid')

    def test_ticket_of_another_event_is_rejected(self):
        other_event = Event.objects.create(
            organizer=self.organizer,
            title='Buea Music Night',
            venue='Mountain Hotel',
            city='Buea',
            starts_at=timezone.now() + timedelta(days=3),
        )
        TicketCategory.objects.create(
            event=other_event, name='Standard', price=Decimal('0'), quantity=5
        )
        self.client.force_login(self.organizer)
        response = self.client.post(
            reverse('scan_api', args=[other_event.slug]), {'code': str(self.ticket.code)}
        )
        self.assertEqual(response.json()['status'], 'wrong_event')
        self.ticket.refresh_from_db()
        self.assertFalse(self.ticket.is_checked_in)

    def test_another_organizer_cannot_scan(self):
        intruder = User.objects.create_user('intruder', password='str0ngpass!')
        self.client.force_login(intruder)
        response = self.scan(self.ticket.code)
        self.assertEqual(response.status_code, 404)
        self.ticket.refresh_from_db()
        self.assertFalse(self.ticket.is_checked_in)

    def test_scan_landing_page_does_not_check_in_on_get(self):
        self.client.force_login(self.organizer)
        response = self.client.get(reverse('scan_ticket', args=[self.ticket.code]))
        self.assertEqual(response.status_code, 200)
        self.ticket.refresh_from_db()
        self.assertFalse(self.ticket.is_checked_in)
        self.client.post(reverse('scan_ticket', args=[self.ticket.code]))
        self.ticket.refresh_from_db()
        self.assertTrue(self.ticket.is_checked_in)


class OrganizerDashboardTests(BaseTestCase):
    def test_dashboard_requires_login(self):
        response = self.client.get(reverse('organizer_dashboard'))
        self.assertEqual(response.status_code, 302)

    def test_dashboard_reports_attendance_and_revenue(self):
        self.book(self.vip_category, quantity=2)
        booking = Booking.objects.get()
        self.client.post(
            reverse('payment_checkout', args=[booking.reference]),
            {'provider': Payment.Provider.MTN, 'phone_number': '677123456'},
        )
        self.client.force_login(self.organizer)
        self.client.post(
            reverse('scan_api', args=[self.event.slug]),
            {'code': str(booking.tickets.first().code)},
        )
        response = self.client.get(reverse('organizer_dashboard'))
        self.assertEqual(response.context['totals']['tickets'], 2)
        self.assertEqual(response.context['totals']['attended'], 1)
        self.assertEqual(response.context['totals']['attendance_rate'], 50.0)
        self.assertEqual(response.context['totals']['revenue'], Decimal('20000'))

    def test_statistics_page_is_private_to_the_organizer(self):
        intruder = User.objects.create_user('intruder2', password='str0ngpass!')
        self.client.force_login(intruder)
        response = self.client.get(
            reverse('event_statistics', args=[self.event.slug])
        )
        self.assertEqual(response.status_code, 404)

    def test_event_creation_with_categories(self):
        self.client.force_login(self.organizer)
        starts_at = (timezone.now() + timedelta(days=20)).strftime('%Y-%m-%dT%H:%M')
        response = self.client.post(
            reverse('event_create'),
            {
                'title': 'Yaounde Startup Fair',
                'description': 'Meet founders',
                'venue': 'Palais des Congres',
                'city': 'Yaounde',
                'starts_at': starts_at,
                'ends_at': '',
                'cover_image_url': '',
                'is_published': 'on',
                'categories-TOTAL_FORMS': '2',
                'categories-INITIAL_FORMS': '0',
                'categories-MIN_NUM_FORMS': '1',
                'categories-MAX_NUM_FORMS': '1000',
                'categories-0-name': 'Free',
                'categories-0-description': '',
                'categories-0-price': '0',
                'categories-0-quantity': '100',
                'categories-1-name': 'VIP',
                'categories-1-description': 'Front row',
                'categories-1-price': '15000',
                'categories-1-quantity': '20',
            },
        )
        event = Event.objects.get(title='Yaounde Startup Fair')
        self.assertRedirects(response, reverse('event_statistics', args=[event.slug]))
        self.assertEqual(event.categories.count(), 2)
        self.assertEqual(event.capacity, 120)


class PageRenderTests(BaseTestCase):
    def test_public_pages_render(self):
        for url in [
            reverse('event_list'),
            reverse('event_detail', args=[self.event.slug]),
            reverse('booking_create', args=[self.event.slug]),
            reverse('login'),
            reverse('signup'),
        ]:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_organizer_pages_render(self):
        self.book(self.free_category)
        self.client.force_login(self.organizer)
        for url in [
            reverse('organizer_dashboard'),
            reverse('event_create'),
            reverse('event_update', args=[self.event.slug]),
            reverse('event_statistics', args=[self.event.slug]),
            reverse('event_attendees', args=[self.event.slug]),
            reverse('scanner', args=[self.event.slug]),
            reverse('scan_ticket', args=[Ticket.objects.get().code]),
        ]:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_payment_page_renders(self):
        self.book(self.vip_category)
        booking = Booking.objects.get()
        response = self.client.get(
            reverse('payment_checkout', args=[booking.reference])
        )
        self.assertContains(response, 'Orange Money')
