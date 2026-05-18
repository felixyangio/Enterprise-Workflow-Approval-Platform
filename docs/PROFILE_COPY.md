# Portfolio Copy

Use this file as source material for LinkedIn, resume bullets, GitHub profile, project reports, and interview explanations.

## One-Line Pitch

Built and deployed a full-stack enterprise workflow approval platform with Vue 3, Django REST Framework, JWT authentication, role-based approvals, audit timelines, dashboards, file uploads, tests, and Docker/Nginx production deployment.

## GitHub Repository Description

Full-stack enterprise workflow approval platform built with Vue 3, Element Plus, Django REST Framework, JWT, ECharts, pytest, Docker Compose, Nginx, and Gunicorn.

Suggested GitHub topics:

```text
vue3, django, django-rest-framework, element-plus, jwt-auth, workflow, approval-system, admin-dashboard, docker-compose, nginx, gunicorn, pytest
```

Suggested GitHub About text:

```text
Enterprise workflow approval platform with role-based request processing, notifications, staff management, dashboard analytics, automated tests, and Dockerized deployment.
```

## LinkedIn Featured Project

Title:

```text
Enterprise Workflow Approval Platform
```

Description:

```text
Designed, implemented, tested, and deployed a full-stack enterprise workflow approval platform using Vue 3, Element Plus, Django REST Framework, JWT authentication, Docker Compose, Nginx, and Gunicorn.

The platform supports employee request submission, approver review workflows, approval/rejection audit timelines, department-scoped announcements, staff management, CSV export, file uploads, and dashboard analytics. I also added automated pytest coverage for authentication, workflow APIs, announcements, staff export, and model behavior, then packaged the project with a production-oriented Docker/Nginx deployment.
```

## LinkedIn Post Draft

```text
I recently completed and deployed a full-stack Enterprise Workflow Approval Platform.

The project simulates a realistic OA/admin workflow system where employees submit requests, approvers review and process them, and every action is recorded in an audit timeline.

Highlights:
- Vue 3 + Element Plus admin UI with responsive layouts
- Django REST Framework backend with JWT authentication
- Role-based workflow permissions and approval logic
- Notifications with department targeting and read tracking
- Staff management with CSV export
- Dashboard metrics and ECharts visualization
- File upload support for workflow attachments
- pytest coverage for API and model behavior
- Docker Compose deployment with Nginx + Gunicorn

This project helped me strengthen practical full-stack engineering skills across frontend UX, REST API design, authentication, testing, and deployment.
```

## Resume Bullets

Choose 3-5 depending on space:

```text
- Built a full-stack enterprise workflow approval platform using Vue 3, Element Plus, Django REST Framework, and JWT authentication, covering request submission, approval processing, announcements, staff management, and dashboard analytics.
- Designed role-based workflow logic for employees, approvers, and superusers, including pending/approved/rejected/withdrawn states and immutable approval action logs for auditability.
- Implemented production-oriented deployment with Docker Compose, Nginx reverse proxy, Gunicorn, static/media file handling, and environment-based Django security settings.
- Developed automated pytest coverage for authentication, workflow APIs, notification filtering, staff CSV export, and model behavior, maintaining a 77-test passing suite.
- Improved admin UX with searchable/filterable tables, status tags, responsive forms, file upload support, empty/loading states, and dashboard visualizations using ECharts.
```

## Short Resume Version

```text
Enterprise Workflow Approval Platform | Vue 3, Django REST Framework, JWT, Docker
- Built a full-stack OA/admin platform for workflow requests, approval processing, announcements, staff management, and dashboard analytics.
- Implemented role-based permissions, audit timelines, file uploads, CSV export, pytest API coverage, and Docker/Nginx/Gunicorn deployment.
```

## Interview Explanation

Use this structure:

```text
The project began as an OA-style employee system, but I refactored it into a more realistic enterprise workflow approval platform.

On the frontend, I used Vue 3, Element Plus, Pinia, Vue Router, and ECharts to build a dashboard-style admin interface with reusable layout components, searchable tables, responsive filters, and polished login/workflow screens.

On the backend, I used Django REST Framework and Simple JWT to build authenticated APIs for workflow requests, notifications, staff management, file uploads, and dashboard summaries. The most important domain logic is the workflow approval lifecycle: employees can submit and withdraw pending requests, approvers can approve or reject, applicants cannot approve their own requests, and every state-changing action creates an audit log.

For quality and deployment, I added pytest coverage for the main APIs and model behavior, then Dockerized the system with Nginx serving the Vue build and reverse-proxying /api requests to Django running under Gunicorn.
```

## What To Emphasize By Role

Frontend-focused roles:

```text
Responsive Vue 3 admin UI, Element Plus component composition, route guards, Pinia auth state, ECharts dashboard, form validation, upload UX, loading/empty states, and production build integration.
```

Backend-focused roles:

```text
Django REST Framework API design, JWT auth, workflow domain rules, permission checks, audit logs, file upload handling, CSV export, filtering/pagination, pytest coverage, and production settings.
```

Full-stack roles:

```text
End-to-end delivery from UI polish and REST API implementation to testing, Docker deployment, Nginx reverse proxy, Gunicorn runtime, and environment-based production configuration.
```

## Suggested Screenshots To Add Later

Add these to `docs/screenshots/` and reference them from README:

```text
login.png
dashboard.png
workflow-list.png
workflow-detail.png
notification-list.png
staff-management.png
```

Recommended GitHub README section after screenshots are available:

```markdown
## Screenshots

![Login](docs/screenshots/login.png)
![Dashboard](docs/screenshots/dashboard.png)
![Workflow Detail](docs/screenshots/workflow-detail.png)
```
