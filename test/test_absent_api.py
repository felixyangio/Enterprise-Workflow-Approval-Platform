"""
test_absent_api.py
==================
Leave management API tests, covering:
  - GET  /absent/type        Get leave type list
  - GET  /absent/responder   Get default approver
  - GET  /absent/absent      Get leave request list
  - POST /absent/absent      Submit a leave request
  - PUT  /absent/absent/{id} Approve/reject a leave request

How to run:
    cd test
    pytest test_absent_api.py -v
"""

import datetime
import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()

ABSENT_TYPE_URL = '/absent/type'
RESPONDER_URL = '/absent/responder'
ABSENT_URL = '/absent/absent'


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def absent_type(db):
    from absent.models import AbsentType
    return AbsentType.objects.create(name='Annual Leave')


@pytest.fixture
def normal_user(db):
    return User.objects.create_user(
        email='staff@test.com', password='pass1234', realname='Staff Member'
    )


@pytest.fixture
def superuser(db):
    return User.objects.create_superuser(
        email='admin@test.com', password='admin1234', realname='Admin'
    )


def _get_token(email, password):
    c = APIClient()
    resp = c.post('/auth/login', {'email': email, 'password': password}, format='json')
    return resp.data.get('token')


@pytest.fixture
def user_client(normal_user):
    """APIClient authenticated as the normal user."""
    client = APIClient()
    token = _get_token('staff@test.com', 'pass1234')
    client.credentials(HTTP_AUTHORIZATION=f'JWT {token}')
    return client


@pytest.fixture
def admin_client(superuser):
    """APIClient authenticated as the superuser."""
    client = APIClient()
    token = _get_token('admin@test.com', 'admin1234')
    client.credentials(HTTP_AUTHORIZATION=f'JWT {token}')
    return client


@pytest.fixture
def absent(db, normal_user, superuser, absent_type):
    """A leave request with pending status."""
    from absent.models import Absent
    return Absent.objects.create(
        title='Test Leave Request',
        applicant=normal_user,
        responder=superuser,
        absent_type=absent_type,
        start_date=datetime.date(2026, 5, 1),
        end_date=datetime.date(2026, 5, 3),
        request_content='Family reasons',
    )


# ===========================================================================
# 1. Leave type endpoint tests  GET /absent/type
# ===========================================================================

@pytest.mark.django_db
class TestAbsentTypeView:

    def test_get_absent_types_authenticated(self, user_client, absent_type):
        """An authenticated user can retrieve the leave type list."""
        resp = user_client.get(ABSENT_TYPE_URL)
        assert resp.status_code == 200
        assert isinstance(resp.data, list)
        names = [item['name'] for item in resp.data]
        assert 'Annual Leave' in names

    def test_get_absent_types_unauthenticated_returns_401(self):
        """Unauthenticated access should return 401."""
        client = APIClient()
        resp = client.get(ABSENT_TYPE_URL)
        assert resp.status_code == 401


# ===========================================================================
# 2. Default approver endpoint tests  GET /absent/responder
# ===========================================================================

@pytest.mark.django_db
class TestResponderView:

    def test_get_responder_returns_superuser(self, user_client, superuser):
        """Should return the superuser as the default approver."""
        resp = user_client.get(RESPONDER_URL)
        assert resp.status_code == 200
        # The returned id should be the superuser's
        assert resp.data.get('id') == superuser.id

    def test_get_responder_unauthenticated_returns_401(self):
        client = APIClient()
        resp = client.get(RESPONDER_URL)
        assert resp.status_code == 401


# ===========================================================================
# 3. Leave request list  GET /absent/absent
# ===========================================================================

@pytest.mark.django_db
class TestAbsentViewGet:

    def test_get_my_absents(self, user_client, absent):
        """A regular user retrieves their own leave request list by default."""
        resp = user_client.get(ABSENT_URL)
        assert resp.status_code == 200
        assert 'count' in resp.data
        assert 'results' in resp.data
        assert resp.data['count'] >= 1

    def test_get_all_absents_as_admin(self, admin_client, absent):
        """A superuser can retrieve all requests using who=all."""
        resp = admin_client.get(ABSENT_URL, {'who': 'all'})
        assert resp.status_code == 200
        assert resp.data['count'] >= 1

    def test_get_absents_unauthenticated_returns_401(self):
        client = APIClient()
        resp = client.get(ABSENT_URL)
        assert resp.status_code == 401

    def test_pagination_page_param(self, user_client, normal_user, absent_type):
        """The page pagination parameter should work correctly."""
        resp = user_client.get(ABSENT_URL, {'page': 1})
        assert resp.status_code == 200


# ===========================================================================
# 4. Submit leave request  POST /absent/absent
# ===========================================================================

@pytest.mark.django_db
class TestAbsentViewPost:

    def test_apply_absent_success(self, user_client, absent_type, superuser):
        """Filling in all required fields should successfully create a pending leave request."""
        payload = {
            'title': 'Annual Leave Request',
            'absent_type_id': absent_type.id,
            'responder_id': superuser.id,
            'start_date': '2026-06-01',
            'end_date': '2026-06-05',
            'request_content': 'Need some rest',
        }
        resp = user_client.post(ABSENT_URL, payload, format='json')
        assert resp.status_code == 201
        assert resp.data['status'] == 1   # STATUS_PENDING = 1
        assert resp.data['title'] == 'Annual Leave Request'

    def test_apply_absent_missing_required_fields_returns_400(self, user_client):
        """Missing required fields (e.g. start_date) should return 400."""
        resp = user_client.post(ABSENT_URL, {
            'title': 'Incomplete Request',
        }, format='json')
        assert resp.status_code == 400

    def test_apply_absent_unauthenticated_returns_401(self, absent_type, superuser):
        client = APIClient()
        resp = client.post(ABSENT_URL, {
            'absent_type_id': absent_type.id,
            'start_date': '2026-06-01',
            'end_date': '2026-06-03',
        }, format='json')
        assert resp.status_code == 401


# ===========================================================================
# 5. Approve/reject leave request  PUT /absent/absent/{id}
# ===========================================================================

@pytest.mark.django_db
class TestAbsentDetailView:

    def test_approve_absent_as_admin(self, admin_client, absent):
        """A superuser can approve a leave request."""
        url = f'{ABSENT_URL}/{absent.id}'
        resp = admin_client.put(url, {
            'status': 2,                  # STATUS_APPROVED
            'response_content': 'Approved',
        }, format='json')
        assert resp.status_code == 200
        assert resp.data['status'] == 2

    def test_reject_absent_as_admin(self, admin_client, absent):
        """A superuser can reject a leave request."""
        url = f'{ABSENT_URL}/{absent.id}'
        resp = admin_client.put(url, {
            'status': 0,                  # STATUS_REJECTED
            'response_content': 'Rejected',
        }, format='json')
        assert resp.status_code == 200
        assert resp.data['status'] == 0

    def test_approve_absent_twice_returns_400(self, admin_client, absent):
        """An already-processed request cannot be approved again; should return 400."""
        url = f'{ABSENT_URL}/{absent.id}'
        admin_client.put(url, {'status': 2, 'response_content': 'Approved'}, format='json')
        # Submit again
        resp = admin_client.put(url, {'status': 0, 'response_content': 'Rejected'}, format='json')
        assert resp.status_code == 400

    def test_approve_absent_not_found_returns_404(self, admin_client):
        """A non-existent request ID should return 404."""
        resp = admin_client.put(f'{ABSENT_URL}/99999', {
            'status': 2, 'response_content': 'Approved'
        }, format='json')
        assert resp.status_code == 404

    def test_normal_user_cannot_approve_others_absent(self, user_client, absent):
        """A regular user is not the approver, so they cannot approve others' requests; should return 404."""
        # The absent's responder is superuser, while user_client is a regular user
        url = f'{ABSENT_URL}/{absent.id}'
        resp = user_client.put(url, {
            'status': 2,
            'response_content': 'I approve this',
        }, format='json')
        # A regular user cannot see requests not assigned to them, returns 404
        assert resp.status_code == 404
