🎟️ EventLink CM
Connecting Events with Participants
EventLink CM is a web-based event management and digital ticketing platform designed to connect event organizers with event participants through one centralized system.

The platform allows organizers to create and manage events, configure free or paid tickets, monitor registrations, verify participants using QR codes, record attendance and analyze event performance.

Participants can discover events, register or purchase tickets, access their digital QR tickets and keep track of their attendance history.

⸻
📌 Table of Contents
* Project Overview
* Problem Statement
* Objectives
* Main Features
* User Roles
* System Workflow
* Technology Stack
* Project Structure
* Database
* Payment System
* QR Code System
* Attendance System
* Statistics and Reports
* Multilingual Support
* Security
* Installation
* Configuration
* Running the Application
* Testing
* Git Branching Strategy
* Development Methodology
* Future Improvements
* Contributors
* License

⸻
📖 Project Overview
EventLink CM provides a digital environment where event organizers and participants can interact before, during and after an event.

For Organizers
Organizers can:
* Create an account
* Create events
* Upload event posters
* Add event information
* Configure ticket types
* Create free tickets
* Create paid tickets
* Monitor ticket sales
* View registered participants
* Scan QR tickets
* Verify tickets
* Prevent duplicate ticket usage
* Record attendance
* View event statistics
* Generate attendance reports
* Analyze event performance

For Participants
Participants can:
* Create an account
* Login securely
* Discover events
* Search for events
* View event details
* Register for free events
* Purchase paid tickets
* Select a supported payment method
* Receive digital tickets
* Access QR codes
* View ticket status
* View attendance status
* View previous event participation

⸻
❗ Problem Statement
Managing events manually can create several challenges for organizers and participants.

Traditional event management can involve:

* Manual registration
* Paper tickets
* Difficult attendance tracking
* Fake or duplicated tickets
* Difficult payment tracking
* Poor participant management
* Limited event statistics
* Time-consuming reporting

EventLink CM addresses these problems by providing a centralized digital platform for event management, ticketing, payments, QR verification and reporting.

⸻
🎯 Objectives
The main objective of EventLink CM is to create a reliable platform that links event organizers with participants.

Specific objectives include:

1. Allow organizers to create and manage events.
2. Allow participants to discover available events.
3. Provide free and paid ticket options.
4. Provide digital tickets.
5. Generate unique QR codes for tickets.
6. Verify tickets at event entrances.
7. Prevent duplicate ticket usage.
8. Record participant attendance automatically.
9. Support MTN Mobile Money and Orange Money payment integration.
10. Provide organizers with event statistics.
11. Generate useful attendance and ticket reports.
12. Support English and French.
13. Provide a responsive interface for mobile and desktop users.

⸻

🚀 Main Features

1. User Authentication
The application supports:
* Participant registration
* Organizer registration
* Login
* Logout
* Password hashing
* Role-based access
* User profiles

⸻
2. Event Management
Organizers can create events containing:
* Event name
* Description
* Category
* Event poster
* Date
* Start time
* End time
* Venue
* Address
* Capacity

⸻

3. Event Discovery
Participants can:
* Browse events
* Search events
* View event details
* View event posters
* View available tickets
* Filter events

⸻
4. Ticket Management
Organizers can create multiple ticket categories.

Example:
Regular Ticket
Price: 5,000 FCFA
Quantity: 100
VIP Ticket
Price: 10,000 FCFA
Quantity: 50
Student Ticket
Price: FREE
Quantity: 100

The system keeps track of:
* Ticket quantity
* Tickets sold
* Remaining tickets
* Ticket status
* Participant ownership

⸻
💳 Payment System
EventLink CM is designed to support mobile-money payments commonly used in Cameroon.

Supported providers:

* MTN Mobile Money
* Orange Money

The system uses a payment service architecture so that each provider can have its own implementation.

PaymentService
      │
      ├── MTNPaymentService
      │
      ├── OrangePaymentService
      │
      └── MockPaymentService

Development Mode

During development, the project can use:

PAYMENT_MODE=mock
This allows developers to test successful, failed and pending payment scenarios without using real money.

Production
Real payment processing must use the official provider APIs, credentials and callback/webhook verification mechanisms.

Payment credentials must never be stored directly in source code.

⸻
📱 QR Code System
Every valid ticket receives a unique QR code.

The QR code represents a secure ticket token.

Example workflow:

Participant purchases ticket
          ↓
Ticket created
          ↓
Unique token generated
          ↓
QR code generated
          ↓
QR displayed to participant
          ↓
Organizer scans QR
          ↓
Backend validates token
          ↓
Ticket accepted/rejected

The QR code should not contain unnecessary sensitive participant information.

⸻
🔐 Ticket Verification
When an organizer scans a ticket, the system checks:

1. Does the QR token exist?
2. Is the ticket valid?
3. Does the ticket belong to the organizer’s event?
4. Is payment confirmed where payment is required?
5. Has the ticket already been used?
6. Has the ticket been cancelled?

If everything is valid:

VALID TICKET
Attendance Recorded

If the ticket was previously scanned:

TICKET ALREADY USED

If the ticket does not exist:

INVALID TICKET

⸻

👥 Attendance System
Once a valid ticket is scanned, EventLink CM records:

* Participant
* Event
* Ticket number
* Organizer/scanner
* Date
* Time
* Attendance status

Example:
Participant: John Doe
Ticket: ELCM-A1B2C3
Event: Tech Conference 2026
Status: PRESENT
Scan Time: 10:42 AM

A ticket cannot be successfully checked in more than once.

⸻

📊 Statistics and Reports
Organizers can monitor event performance.

The dashboard can display:

* Total events
* Total registrations
* Tickets sold
* Remaining tickets
* Participants attended
* No-shows
* Attendance percentage
* Revenue

Attendance Rate
Attendance Rate =
(Attended Participants / Registered Participants) × 100

These statistics can help organizers understand event performance and improve future events.

⸻

📑 Reports
The system supports event reports such as:

Attendance Report
Participant
Email
Ticket Number
Ticket Type
Attendance Status
Scan Time

Ticket Report
Ticket Type
Quantity
Tickets Sold
Tickets Remaining

Event Performance
Registrations
Attendance
No-Shows
Attendance Rate
Revenue

CSV export is supported, with PDF reporting planned/available depending on the deployment configuration.

⸻

🌍 Multilingual Support

EventLink CM is designed to support two languages:

🇬🇧 English

🇫🇷 Français

The language system should cover:

* Navigation
* Buttons
* Forms
* Dashboard
* Notifications
* Ticket status
* Payment status
* Error messages
* Reports

Suggested translation structure:

translations/
├── en.json
└── fr.json

⸻

👤 User Roles
EventLink CM has three main roles.

Participant
Can:

* Browse events
* Register
* Purchase tickets
* View tickets
* View QR codes
* View attendance history

Organizer
Can:

* Create events
* Manage tickets
* Monitor participants
* Scan tickets
* Record attendance
* View statistics
* Generate reports

Administrator
Can:

* Manage users
* Manage organizers
* Monitor events
* Monitor transactions
* View system statistics
* Moderate platform content

⸻
🔄 System Workflow
Participant Workflow

Visit EventLink CM
       ↓
Create Account
       ↓
Login
       ↓
Browse Events
       ↓
Select Event
       ↓
Select Ticket
       ↓
Free OR Paid
       ↓
Payment if required
       ↓
Ticket Generated
       ↓
QR Code Generated
       ↓
Attend Event
       ↓
QR Scanned
       ↓
Attendance Recorded

⸻
Organizer Workflow
Create Organizer Account
          ↓
Login
          ↓
Organizer Dashboard
          ↓
Create Event
          ↓
Upload Poster
          ↓
Configure Tickets
          ↓
Publish Event
          ↓
Participants Register/Purchase
          ↓
Monitor Tickets
          ↓
Scan QR Codes
          ↓
Record Attendance
          ↓
View Statistics
          ↓
Generate Report

⸻
🛠️ Technology Stack

Frontend
* HTML5
* CSS3
* JavaScript
* Bootstrap

Backend
* Python
* Flask
* Flask-SQLAlchemy
* Flask-Login
* Flask-Bcrypt

Database
* MySQL
* PyMySQL

QR Code
* Python qrcode
* Browser-based QR scanner

Testing
* Pytest

Version Control
* Git
* GitHub

⸻
📁 Project Structure
eventlink_cm/
│
├── app/
│   ├── __init__.py
│   ├── models.py
│   ├── services.py
│   ├── decorators.py
│   │
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── public.py
│   │   ├── organizer.py
│   │   ├── participant.py
│   │   ├── scanner.py
│   │   ├── admin.py
│   │   └── api.py
│   │
│   ├── templates/
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── events.html
│   │   ├── event_detail.html
│   │   ├── auth/
│   │   ├── organizer/
│   │   ├── participant/
│   │   └── admin/
│   │
│   └── static/
│       ├── css/
│       ├── js/
│       └── uploads/
│
├── tests/
│
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
├── run.py
└── README.md

⸻
🗄️ Database
The application uses MySQL.
Main entities include:

User
 │
 ├── Organizer
 │       │
 │       └── Event
 │             │
 │             ├── TicketType
 │             │
 │             └── Ticket
 │                    │
 │                    ├── Payment
 │                    │
 │                    └── Attendance
 │
 ├── Notifications
 │
 └── Audit Logs

Main tables:
* users
* organizers
* events
* event_images
* ticket_types
* tickets
* payments
* attendance
* notifications
* audit_logs

⸻
🔒 Security

Security is an important part of EventLink CM.

The application should implement:

* Password hashing
* Authentication
* Role-based authorization
* Input validation
* SQL injection protection
* XSS protection
* CSRF protection
* Secure sessions
* Secure QR tokens
* File upload validation
* Payment verification
* Environment variables
* Error handling
* Audit logging

Never store passwords as plain text.

Never place payment API secrets inside frontend JavaScript.

Never trust payment success messages sent only from the browser.

⸻
💻 Installation

1. Clone the project

git clone YOUR_REPOSITORY_URL

Then:

cd eventlink_cm

⸻
2. Create a virtual environment

Windows

python -m venv .venv
.venv\Scripts\activate

Linux/macOS

python3 -m venv .venv
source .venv/bin/activate

⸻
3. Install dependencies

pip install -r requirements.txt

⸻
4. Create MySQL Database

Open MySQL:

CREATE DATABASE eventlink_cm
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

⸻
5. Configure Environment Variables
Copy:

.env.example

to:

.env

Configure:

SECRET_KEY=your-secret-key
DATABASE_URL=mysql+pymysql://root:password@localhost/eventlink_cm
PAYMENT_MODE=mock

Replace the database username and password with your own MySQL credentials.

⸻
▶️ Running the Application
Start Flask:

python run.py

The application should become available at:

http://127.0.0.1:5000

Open the address in your browser.

⸻

🧪 Testing
Run all tests:

pytest

The project follows the principles of Test-Driven Development (TDD).
The development cycle is:

RED
 ↓
Write failing test
 ↓
GREEN
 ↓
Implement minimum code
 ↓
REFACTOR
 ↓
Improve implementation

⸻
🌿 Git Branching Strategy
The project uses Git branches to keep development organized.

main
 │
 └── develop
       │
       ├── feature/project-setup
       ├── feature/auth
       ├── feature/events
       ├── feature/tickets
       ├── feature/payments
       ├── feature/qr
       ├── feature/attendance
       ├── feature/reports
       ├── feature/i18n
       ├── feature/admin
       ├── feature/security
       └── feature/testing

Main
Contains stable production-ready code.

Develop
Contains integrated development work.

Feature Branches
Each feature is developed independently.

Example:
git checkout develop
git checkout -b feature/events

After development:

git add .
git commit -m "Add event management"
git push origin feature/events

Then create a Pull Request into develop.

⸻
🏃 Development Methodology
EventLink CM follows:

SDLC

Planning
   ↓
Requirements Analysis
   ↓
System Design
   ↓
Implementation
   ↓
Testing
   ↓
Deployment
   ↓
Maintenance

Scrum
Development can be divided into sprints:

Sprint 1
Project foundation

Sprint 2
Authentication

Sprint 3
Event management

Sprint 4
Ticketing

Sprint 5
Payments

Sprint 6
QR scanning and attendance

Sprint 7
Statistics and reports

Sprint 8
Administration, security and final testing

⸻
🧩 Object-Oriented Design
The backend uses service-oriented classes where appropriate.

For example:

PaymentService
       │
       ├── MTNPaymentService
       │
       ├── OrangePaymentService
       │
       └── MockPaymentService

This allows different payment providers to implement the same payment operations while keeping the rest of the application independent from a specific provider.

⸻
📱 Responsive Design
EventLink CM is designed for:

* Smartphones
* Tablets
* Laptops
* Desktop computers

The interface should prioritize a mobile-friendly experience because participants and organizers may primarily access the platform from mobile devices.

⸻
🔮 Future Improvements
Possible future versions can include:

* Real-time notifications
* Email ticket delivery
* SMS notifications
* Advanced event recommendations
* Google Maps integration
* Event sharing
* Organizer verification
* Event reviews and ratings
* Discount codes
* Promotional tickets
* Multiple organizers per event
* Refund management
* Wallet system
* Advanced financial reports
* Cloud image storage
* Progressive Web App (PWA)
* Mobile applications
* Advanced fraud detection
* Real-time event dashboards

⸻
⚠️ Production Considerations
Before deploying EventLink CM to production:

* Change all development secrets.
* Configure production MySQL.
* Configure HTTPS.
* Configure production payment APIs.
* Verify payment callbacks/webhooks.
* Configure secure file storage.
* Disable Flask debug mode.
* Configure proper logging.
* Add CSRF protection to all applicable forms.
* Configure backups.
* Test QR validation under real event conditions.
* Perform security testing.
* Test payment failure and timeout scenarios.
* Never use mock payments in production.

⸻
👨‍💻 Contributors

Project: EventLink CM
Purpose: Event management and participant connection platform

Primary Technologies:

HTML
CSS
JavaScript
Python
Flask
MySQL

⸻
📄 License

This project can be released under an appropriate open-source or academic project license.

For an academic submission, the project ownership and licensing terms should follow the requirements of the institution or project supervisor.

⸻
⭐ EventLink CM

Connect Events. Empower Organizers. Simplify Participation.

EventLink CM brings event discovery, registration, digital ticketing, mobile payments, QR verification, attendance tracking and event analytics together in one platform.

        ORGANIZERS
             │
             │
             ▼
       ┌─────────────┐
       │ EventLink CM│
       └─────────────┘
             ▲
             │
             │
        PARTICIPANTS
Create Events ←→ Discover Events
Manage Tickets ←→ Buy Tickets
Scan QR Codes ←→ Receive QR Codes
Track Attendance ←→ Attend Events
View Statistics ←→ View History
