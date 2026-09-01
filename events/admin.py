from django.contrib import admin

from .models import Booking, Event, Payment, Ticket, TicketCategory


class TicketCategoryInline(admin.TabularInline):
    model = TicketCategory
    extra = 1


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'city', 'starts_at', 'organizer', 'is_published')
    list_filter = ('is_published', 'city')
    search_fields = ('title', 'venue', 'city')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [TicketCategoryInline]


@admin.register(TicketCategory)
class TicketCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'event', 'price', 'quantity')
    list_filter = ('event',)


class TicketInline(admin.TabularInline):
    model = Ticket
    extra = 0
    readonly_fields = ('code', 'is_checked_in', 'checked_in_at', 'checked_in_by')


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('reference', 'full_name', 'event', 'category', 'quantity', 'status')
    list_filter = ('status', 'event')
    search_fields = ('full_name', 'email', 'phone', 'reference')
    inlines = [TicketInline]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('booking', 'provider', 'amount', 'status', 'transaction_reference')
    list_filter = ('provider', 'status')


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('code', 'holder_name', 'booking', 'is_checked_in', 'checked_in_at')
    list_filter = ('is_checked_in', 'booking__event')
    search_fields = ('code', 'holder_name')
