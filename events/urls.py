from django.urls import path

from . import views

urlpatterns = [
    path('', views.event_list, name='event_list'),
    path('signup/', views.organizer_signup, name='signup'),
    # Organizer area
    path('dashboard/', views.organizer_dashboard, name='organizer_dashboard'),
    path('dashboard/events/new/', views.event_create, name='event_create'),
    path('dashboard/events/<slug:slug>/edit/', views.event_update, name='event_update'),
    path(
        'dashboard/events/<slug:slug>/stats/',
        views.event_statistics,
        name='event_statistics',
    ),
    path(
        'dashboard/events/<slug:slug>/attendees/',
        views.event_attendees,
        name='event_attendees',
    ),
    path('dashboard/events/<slug:slug>/scan/', views.scanner, name='scanner'),
    path('dashboard/events/<slug:slug>/scan/api/', views.scan_api, name='scan_api'),
    path('scan/<uuid:code>/', views.scan_ticket, name='scan_ticket'),
    # Attendee area
    path('events/<slug:slug>/', views.event_detail, name='event_detail'),
    path('events/<slug:slug>/book/', views.booking_create, name='booking_create'),
    path(
        'bookings/<uuid:reference>/pay/',
        views.payment_checkout,
        name='payment_checkout',
    ),
    path('bookings/<uuid:reference>/', views.booking_detail, name='booking_detail'),
    path('tickets/<uuid:code>/', views.ticket_detail, name='ticket_detail'),
    path('tickets/<uuid:code>/qr.png', views.ticket_qr, name='ticket_qr'),
]
