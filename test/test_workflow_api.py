import pytest
from uuid import uuid4
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from workflow.models import WorkflowActionLog, WorkflowCategory, WorkflowRequest

User = get_user_model()

CATEGORIES_URL = '/workflow/categories'
REQUESTS_URL = '/workflow/requests'


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        email='workflow-admin@test.com',
        password='admin1234',
        realname='Workflow Admin',
    )


@pytest.fixture
def normal_user(db):
    return User.objects.create_user(
        email='workflow-user@test.com',
        password='pass1234',
        realname='Workflow User',
    )


@pytest.fixture
def other_user(db):
    return User.objects.create_user(
        email='workflow-other@test.com',
        password='pass1234',
        realname='Other User',
    )


@pytest.fixture
def leave_category(db):
    suffix = uuid4().hex[:8]
    return WorkflowCategory.objects.create(
        name=f'Leave Request {suffix}',
        code=f'leave-test-{suffix}',
        field_schema=WorkflowCategory.FIELD_DATE_RANGE,
    )


@pytest.fixture
def expense_category(db):
    suffix = uuid4().hex[:8]
    return WorkflowCategory.objects.create(
        name=f'Expense Reimbursement {suffix}',
        code=f'expense-test-{suffix}',
        field_schema=WorkflowCategory.FIELD_AMOUNT,
    )


def authenticated_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
class TestWorkflowApi:
    def test_get_categories_requires_auth(self):
        response = APIClient().get(CATEGORIES_URL)
        assert response.status_code == 401

    def test_create_date_range_request(self, normal_user, admin_user, leave_category):
        client = authenticated_client(normal_user)
        response = client.post(REQUESTS_URL, {
            'title': 'Annual leave',
            'category_id': leave_category.id,
            'approver_id': admin_user.id,
            'start_date': '2026-06-01',
            'end_date': '2026-06-03',
            'content': 'Family trip',
        }, format='json')

        assert response.status_code == 201
        assert response.data['status'] == WorkflowRequest.STATUS_PENDING
        assert WorkflowActionLog.objects.filter(
            request_id=response.data['id'],
            action=WorkflowActionLog.ACTION_SUBMIT,
        ).exists()

    def test_create_amount_request_requires_amount(self, normal_user, admin_user, expense_category):
        client = authenticated_client(normal_user)
        response = client.post(REQUESTS_URL, {
            'title': 'Taxi reimbursement',
            'category_id': expense_category.id,
            'approver_id': admin_user.id,
            'content': 'Client visit taxi',
        }, format='json')

        assert response.status_code == 400

    def test_scopes_return_expected_requests(self, normal_user, admin_user, other_user, leave_category):
        own_request = WorkflowRequest.objects.create(
            title='Mine',
            category=leave_category,
            applicant=normal_user,
            approver=admin_user,
            start_date='2026-06-01',
            end_date='2026-06-02',
        )
        WorkflowRequest.objects.create(
            title='Other',
            category=leave_category,
            applicant=other_user,
            approver=admin_user,
            start_date='2026-06-01',
            end_date='2026-06-02',
        )

        user_response = authenticated_client(normal_user).get(REQUESTS_URL, {'scope': 'mine'})
        admin_response = authenticated_client(admin_user).get(REQUESTS_URL, {'scope': 'todo'})

        assert user_response.status_code == 200
        assert [item['id'] for item in user_response.data['items']] == [own_request.id]
        assert admin_response.status_code == 200
        assert admin_response.data['total'] == 2

    def test_approve_reject_and_withdraw_transitions(self, normal_user, admin_user, leave_category):
        request = WorkflowRequest.objects.create(
            title='Remote work',
            category=leave_category,
            applicant=normal_user,
            approver=admin_user,
            start_date='2026-06-01',
            end_date='2026-06-02',
        )

        approve_response = authenticated_client(admin_user).put(
            f'{REQUESTS_URL}/{request.id}/approve',
            {'comment': 'Approved'},
            format='json',
        )
        assert approve_response.status_code == 200
        assert approve_response.data['status'] == WorkflowRequest.STATUS_APPROVED

        second_response = authenticated_client(admin_user).put(
            f'{REQUESTS_URL}/{request.id}/reject',
            {'comment': 'Too late'},
            format='json',
        )
        assert second_response.status_code == 400

        withdraw_request = WorkflowRequest.objects.create(
            title='Leave',
            category=leave_category,
            applicant=normal_user,
            approver=admin_user,
            start_date='2026-06-03',
            end_date='2026-06-04',
        )
        withdraw_response = authenticated_client(normal_user).put(
            f'{REQUESTS_URL}/{withdraw_request.id}/withdraw',
            {'comment': 'No longer needed'},
            format='json',
        )
        assert withdraw_response.status_code == 200
        assert withdraw_response.data['status'] == WorkflowRequest.STATUS_WITHDRAWN

    def test_non_approver_and_self_approval_are_blocked(self, normal_user, admin_user, other_user, leave_category):
        request = WorkflowRequest.objects.create(
            title='Purchase',
            category=leave_category,
            applicant=normal_user,
            approver=admin_user,
            start_date='2026-06-01',
            end_date='2026-06-02',
        )

        other_response = authenticated_client(other_user).put(
            f'{REQUESTS_URL}/{request.id}/approve',
            {'comment': 'I approve'},
            format='json',
        )
        applicant_response = authenticated_client(normal_user).put(
            f'{REQUESTS_URL}/{request.id}/approve',
            {'comment': 'I approve myself'},
            format='json',
        )

        assert other_response.status_code == 403
        assert applicant_response.status_code == 403

    def test_summary_includes_status_breakdown(self, normal_user, admin_user, leave_category):
        WorkflowRequest.objects.create(
            title='Pending leave',
            category=leave_category,
            applicant=normal_user,
            approver=admin_user,
            start_date='2026-06-01',
            end_date='2026-06-02',
        )
        WorkflowRequest.objects.create(
            title='Approved leave',
            category=leave_category,
            applicant=normal_user,
            approver=admin_user,
            status=WorkflowRequest.STATUS_APPROVED,
            start_date='2026-06-03',
            end_date='2026-06-04',
        )

        response = authenticated_client(normal_user).get('/workflow/summary')

        assert response.status_code == 200
        by_status = {item['status']: item['count'] for item in response.data['by_status']}
        assert by_status[WorkflowRequest.STATUS_PENDING] == 1
        assert by_status[WorkflowRequest.STATUS_APPROVED] == 1
        assert response.data['my_pending'] == 1
