# EventLink CM

EventLink CM is a Django web application that lets organizers advertise their events and
lets attendees book tickets — free or paid — and receive a personalised, single-use QR
code ticket. Paid tickets are settled with **MTN Mobile Money** or **Orange Money**, and
organizers scan tickets at the gate to collect attendance and follow a live statistics
board.

## Features

**For attendees**
- Browse and search published events (title, city, venue, description).
- Book a ticket in the category of their choice; a price of `0 XAF` means the ticket is free.
- Free tickets are issued instantly, paid tickets go through a mobile money checkout
  (MTN MoMo / Orange Money).
- Every ticket is delivered as a digital ticket with its own personalised QR code.

**For organizers**
- Create and edit events with as many ticket categories (and prices) as needed.
- Built-in QR scanner page (camera based, with a manual code entry fallback) to check
  attendees in.
- A ticket can only be accepted **once** — a second scan is reported as "already used",
  which blocks re-used or shared tickets.
- Attendance list per event and a statistics board: capacity, tickets issued, checked-in
  count, attendance rate, revenue and mobile money breakdown per operator.

## Project layout

```
eventpass/            Project configuration (settings, root URLconf, WSGI/ASGI)
events/
├── models.py         Event, TicketCategory, Booking, Payment, Ticket
├── forms.py          Event/category, booking, mobile money and scan forms
├── views.py          Attendee flows, organizer dashboard, scanner & check-in API
├── urls.py           Application routes
├── admin.py          Admin registration
├── tests.py          Test suite
└── templates/        HTML templates (Tailwind CSS via CDN)
```

## Getting started

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Then open <http://127.0.0.1:8000/>. Create an organizer account from **Sign up**, publish
an event with its ticket categories, and share the public event page with your audience.

### Configuration

| Environment variable | Purpose | Default |
| --- | --- | --- |
| `DJANGO_SECRET_KEY` | Secret key used for signing | insecure development key |
| `DJANGO_DEBUG` | `1` enables debug mode, `0` disables it | `1` |
| `DJANGO_ALLOWED_HOSTS` | Comma separated list of allowed hosts | localhost only |

Set all three when deploying.

## Mobile money

`events/views.py` creates a `Payment` record for the chosen operator and confirms it
immediately, which is the sandbox behaviour. To go live, call the MTN MoMo Collection API
or the Orange Money Web Payment API where the payment is created, and call
`payment.mark_successful()` from the operator callback — the tickets are only issued once
that method runs.

## Running the tests

```bash
python manage.py test
```
