# MediDelivery

A simple Django-based online medicine ordering and delivery application built for college demonstration and learning purposes.

## Features

- Browse medicines with images and details
- Session-based shopping cart (add/inc/dec/remove)
- Checkout with Cash-on-Delivery (COD) or Razorpay integration
- Order tracking for customers
- Admin portal to view orders and assign delivery staff
- Delivery portal for delivery staff to update order status (strict progression)

## Technology Stack

- Python 3.x
- Django
- SQLite (development)
- Razorpay (payment gateway)
- HTML/CSS (Django templates)

## Quickstart (development)

1. Clone the repository

```bash
git clone <repo-url>
cd medicine_delivery
```

2. Create and activate a virtual environment

Windows (PowerShell):

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

3. Install dependencies

```bash
pip install -r requirements.txt
```

4. Create `.env` in project root with Razorpay test keys (example provided in repository):

```text
RAZORPAY_KEY_ID=rzp_test_...
RAZORPAY_KEY_SECRET=...
```

5. Apply migrations and create a superuser

```bash
python manage.py migrate
python manage.py createsuperuser
```

6. Run the development server

```bash
python manage.py runserver
```

Open `http://127.0.0.1:8000/` in your browser.

## Project Layout (important files)

- `config/` — Django project settings and URL routing
- `core/` — Main app: models, views, templates, static
- `delivery/` — Delivery user flows and templates
- `adminapp/` — Admin portal and assign-delivery flows
- `report/` — Generated project reports (HTML / Markdown / PDF)

## Payments

The project uses Razorpay for payments. Test keys are included in `.env` for demo; do NOT commit production keys. In production, verify Razorpay signatures/webhooks on the server side.

## Notes & Recommendations

- Move `SECRET_KEY` and all secrets to environment variables for production.
- Set `DEBUG = False` and configure `ALLOWED_HOSTS` before deploying.
- Use PostgreSQL and a proper media/static hosting (S3 + CDN) for production.
- Add unit tests for cart and checkout flows and for role-based access decorators.

## Report & Documentation

An interactive project report with flowcharts and diagrams is available in the `report/` folder:

- `report/MediDelivery_Detailed_Report.md`
- `report/MediDelivery_Report.md`
- `report/MediDelivery_Report.html`

Open the Markdown files in a Mermaid-capable renderer (VS Code + Mermaid Preview or GitHub) or open the HTML in a browser.

## License

This repository is for educational purposes. Update license as needed.

## Contact

For questions, contact the author or project maintainer.
