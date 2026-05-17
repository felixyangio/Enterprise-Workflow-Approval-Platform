# Enterprise Workflow Approval Platform

This project is a full-stack employee workflow approval platform built with Vue 3, Element Plus, Django, Django REST Framework, and JWT authentication.

It started as an OA-style employee system and now focuses on a more realistic enterprise scenario: employees submit workflow requests, administrators or assigned approvers process them, and every action is recorded in an approval timeline.

## Core Modules

| Module | Description |
|---|---|
| Authentication | JWT login and password reset |
| Employee Management | Departments, employees, and employee status |
| Workflow Center | Leave, overtime, reimbursement, purchase, and remote-work requests |
| Approval Todo | Pending approvals, approve/reject actions, and audit comments |
| Announcements | Department-scoped company notifications with read tracking |
| Dashboard | Approval todo count, personal request status, announcements, and staff charts |

## Tech Stack

| Layer | Stack |
|---|---|
| Frontend | Vue 3, Vite, Element Plus, Pinia, ECharts |
| Backend | Django 6, Django REST Framework, Simple JWT |
| Database | SQLite for development |

## Backend Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r oaback/requirements.txt
cd oaback
python manage.py migrate
python manage.py seed_workflow
python manage.py runserver
```

Backend runs at `http://127.0.0.1:8000`.

Demo accounts created by `seed_workflow` when missing:

| Role | Email | Password |
|---|---|---|
| Admin | `admin@example.com` | `Admin@123456` |
| Employee | `employee@example.com` | `Employee@123456` |

## Frontend Setup

```bash
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`.

Development environment variables:

```env
VITE_BASE_URL=http://127.0.0.1:8000
VITE_APP_TITLE="Enterprise Workflow Approval Platform"
```

## Workflow API

| Method | Path | Description |
|---|---|---|
| GET | `/workflow/categories` | List active workflow request types |
| GET | `/workflow/requests?scope=mine\|todo\|all` | List requests by visibility scope |
| POST | `/workflow/requests` | Submit a workflow request |
| GET | `/workflow/requests/<id>` | Request detail with approval logs |
| PUT | `/workflow/requests/<id>/approve` | Approve a pending request |
| PUT | `/workflow/requests/<id>/reject` | Reject a pending request |
| PUT | `/workflow/requests/<id>/withdraw` | Withdraw own pending request |
| GET | `/workflow/requests/<id>/logs` | Approval action timeline |
| GET | `/workflow/summary` | Workflow dashboard metrics |

Legacy `/absent/*` APIs still exist for compatibility, but new screens use `/workflow/*`.

## Workflow Rules

- Employees can create workflow requests and view their own requests.
- Employees can withdraw only their own `pending` requests.
- Approvers and superusers can approve or reject `pending` requests.
- Applicants cannot approve their own requests.
- Every submit, approve, reject, and withdraw action creates a `WorkflowActionLog`.
- Date-range request types require `start_date` and `end_date`.
- Amount request types require a positive `amount`.

## Tests

```bash
cd test
pytest
```

The test suite covers authentication, announcements, legacy leave APIs, and the new workflow API.

## Notes

- `oafront/` is a historical duplicate of the frontend. The root `src/` frontend is the active implementation.
- Use `seed_workflow` after migrating a fresh database to create realistic demo data.
