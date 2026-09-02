import uuid
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify


class Event(models.Model):
    """An event advertised by an organizer."""

    organizer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='events',
    )
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField(blank=True)
    venue = models.CharField(max_length=200)
    city = models.CharField(max_length=100)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField(null=True, blank=True)
    cover_image_url = models.URLField(blank=True)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['starts_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)[:200] or 'event'
            slug = base
            counter = 2
            while Event.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base}-{counter}'
                counter += 1
            self.slug = slug
        return super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('event_detail', args=[self.slug])

    @property
    def is_free(self):
        """True when every ticket category of the event costs nothing."""
        prices = [category.price for category in self.categories.all()]
        return bool(prices) and all(price == Decimal('0') for price in prices)

    @property
    def is_past(self):
        reference = self.ends_at or self.starts_at
        return reference < timezone.now()

    @property
    def lowest_price(self):
        prices = [category.price for category in self.categories.all()]
        return min(prices) if prices else None

    @property
    def capacity(self):
        return sum(category.quantity for category in self.categories.all())

    @property
    def tickets_issued(self):
        return Ticket.objects.filter(booking__event=self).count()

    @property
    def tickets_checked_in(self):
        return Ticket.objects.filter(booking__event=self, is_checked_in=True).count()

    @property
    def tickets_remaining(self):
        return max(self.capacity - self.tickets_issued, 0)

    @property
    def attendance_rate(self):
        issued = self.tickets_issued
        if not issued:
            return 0
        return round(self.tickets_checked_in / issued * 100, 1)

    @property
    def revenue(self):
        total = Payment.objects.filter(
            booking__event=self, status=Payment.Status.SUCCESSFUL
        ).aggregate(total=models.Sum('amount'))['total']
        return total or Decimal('0')


class TicketCategory(models.Model):
    """A ticket type for an event. A price of 0 means the ticket is free."""

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=255, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0'))
    quantity = models.PositiveIntegerField(default=100)

    class Meta:
        ordering = ['price', 'name']
        unique_together = ('event', 'name')
        verbose_name_plural = 'ticket categories'

    def __str__(self):
        return f'{self.event.title} - {self.name}'

    @property
    def is_free(self):
        return self.price == Decimal('0')

    @property
    def tickets_issued(self):
        return Ticket.objects.filter(booking__category=self).count()

    @property
    def tickets_remaining(self):
        return max(self.quantity - self.tickets_issued, 0)

    @property
    def is_sold_out(self):
        return self.tickets_remaining == 0


class Booking(models.Model):
    """A reservation made by an attendee for one or more tickets."""

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending payment'
        CONFIRMED = 'confirmed', 'Confirmed'
        CANCELLED = 'cancelled', 'Cancelled'

    reference = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='bookings')
    category = models.ForeignKey(
        TicketCategory, on_delete=models.CASCADE, related_name='bookings'
    )
    full_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    quantity = models.PositiveIntegerField(default=1)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.full_name} - {self.event.title}'

    def get_absolute_url(self):
        return reverse('booking_detail', args=[self.reference])

    @property
    def total_amount(self):
        return self.category.price * self.quantity

    @property
    def is_free(self):
        return self.total_amount == Decimal('0')

    def issue_tickets(self):
        """Create the digital tickets for this booking (idempotent)."""
        missing = self.quantity - self.tickets.count()
        for _ in range(max(missing, 0)):
            Ticket.objects.create(booking=self, holder_name=self.full_name)
        if self.status != self.Status.CONFIRMED:
            self.status = self.Status.CONFIRMED
            self.save(update_fields=['status'])
        return self.tickets.all()


class Payment(models.Model):
    """A mobile money payment attached to a booking."""

    class Provider(models.TextChoices):
        MTN = 'mtn', 'MTN Mobile Money'
        ORANGE = 'orange', 'Orange Money'

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        SUCCESSFUL = 'successful', 'Successful'
        FAILED = 'failed', 'Failed'

    booking = models.OneToOneField(
        Booking, on_delete=models.CASCADE, related_name='payment'
    )
    provider = models.CharField(max_length=20, choices=Provider.choices)
    phone_number = models.CharField(max_length=20)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    transaction_reference = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.get_provider_display()} - {self.amount} ({self.status})'

    def mark_successful(self, transaction_reference=''):
        """Confirm the payment and release the digital tickets."""
        self.status = self.Status.SUCCESSFUL
        self.transaction_reference = (
            transaction_reference or uuid.uuid4().hex[:12].upper()
        )
        self.save(update_fields=['status', 'transaction_reference', 'updated_at'])
        self.booking.issue_tickets()
        return self


class Ticket(models.Model):
    """A single-use digital ticket identified by a unique QR code."""

    code = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    booking = models.ForeignKey(
        Booking, on_delete=models.CASCADE, related_name='tickets'
    )
    holder_name = models.CharField(max_length=150)
    is_checked_in = models.BooleanField(default=False)
    checked_in_at = models.DateTimeField(null=True, blank=True)
    checked_in_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='checked_in_tickets',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'Ticket {self.code}'

    def get_absolute_url(self):
        return reverse('ticket_detail', args=[self.code])

    @property
    def event(self):
        return self.booking.event

    def check_in(self, user=None):
        """Consume the ticket. Returns True only on the first successful scan.

        The update is performed as a single conditional query so that two
        simultaneous scans of the same QR code can never both succeed.
        """
        scanned_at = timezone.now()
        scanned_by = user if user is not None and user.is_authenticated else None
        updated = Ticket.objects.filter(pk=self.pk, is_checked_in=False).update(
            is_checked_in=True, checked_in_at=scanned_at, checked_in_by=scanned_by
        )
        self.refresh_from_db()
        return bool(updated)
