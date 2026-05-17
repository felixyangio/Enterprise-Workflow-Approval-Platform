"""
test_inform_api.py
==================
Announcement management API tests, covering:
  - GET    /inform/inform        Get announcement list
  - POST   /inform/inform        Publish an announcement
  - GET    /inform/inform/{pk}   Get announcement detail
  - DELETE /inform/inform/{pk}   Delete an announcement
  - POST   /inform/inform/read   Mark an announcement as read

How to run:
    cd test
    pytest test_inform_api.py -v
"""

import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()

INFORM_URL = '/inform/inform'
INFORM_READ_URL = '/inform/inform/read'


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def normal_user(db):
    return User.objects.create_user(
        email='staff@inform.com', password='pass1234', realname='Staff A'
    )


@pytest.fixture
def another_user(db):
    return User.objects.create_user(
        email='staff2@inform.com', password='pass1234', realname='Staff B'
    )


@pytest.fixture
def superuser(db):
    return User.objects.create_superuser(
        email='admin@inform.com', password='admin1234', realname='Admin'
    )


def _token(email, password):
    c = APIClient()
    r = c.post('/auth/login', {'email': email, 'password': password}, format='json')
    return r.data.get('token')


@pytest.fixture
def user_client(normal_user):
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f'JWT {_token("staff@inform.com", "pass1234")}')
    return c


@pytest.fixture
def user2_client(another_user):
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f'JWT {_token("staff2@inform.com", "pass1234")}')
    return c


@pytest.fixture
def admin_client(superuser):
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f'JWT {_token("admin@inform.com", "admin1234")}')
    return c


@pytest.fixture
def public_inform(db, normal_user):
    """Create an announcement visible to all departments (empty departments means visible to everyone)."""
    from inform.models import Inform
    return Inform.objects.create(
        title='Company-wide Announcement',
        content='Attention all staff',
        author=normal_user,
    )


@pytest.fixture
def top_inform(db, superuser):
    """Create a pinned announcement."""
    from inform.models import Inform
    return Inform.objects.create(
        title='Pinned Important Announcement',
        content='Very important content',
        author=superuser,
        is_top=True,
    )


# ===========================================================================
# 1. Get announcement list  GET /inform/inform
# ===========================================================================

@pytest.mark.django_db
class TestInformViewGet:

    def test_list_informs_authenticated(self, user_client, public_inform):
        """An authenticated user can retrieve the announcement list."""
        resp = user_client.get(INFORM_URL)
        assert resp.status_code == 200
        assert 'items' in resp.data
        assert 'total' in resp.data
        assert resp.data['total'] >= 1

    def test_list_informs_unauthenticated_returns_401(self):
        c = APIClient()
        resp = c.get(INFORM_URL)
        assert resp.status_code == 401

    def test_pagination_default_page(self, user_client, public_inform):
        """Without a page param the default is page 1, response should have page=1."""
        resp = user_client.get(INFORM_URL)
        assert resp.data['page'] == 1

    def test_superuser_sees_all_informs(self, admin_client, public_inform, top_inform):
        """A superuser should see all announcements (including pinned ones)."""
        resp = admin_client.get(INFORM_URL)
        assert resp.status_code == 200
        assert resp.data['total'] >= 2

    def test_keyword_read_and_page_size_filters(self, user_client, normal_user, public_inform):
        from inform.models import Inform, InformRead

        unread = Inform.objects.create(
            title='Quarterly Security Notice',
            content='Security awareness update',
            author=normal_user,
        )
        InformRead.objects.create(inform=public_inform, reader=normal_user)

        keyword_resp = user_client.get(INFORM_URL, {'keyword': 'Security', 'size': 1})
        read_resp = user_client.get(INFORM_URL, {'read': 'read'})
        unread_resp = user_client.get(INFORM_URL, {'read': 'unread'})

        assert keyword_resp.status_code == 200
        assert keyword_resp.data['size'] == 1
        assert keyword_resp.data['items'][0]['id'] == unread.id
        assert public_inform.id in [item['id'] for item in read_resp.data['items']]
        assert unread.id in [item['id'] for item in unread_resp.data['items']]


# ===========================================================================
# 2. Publish announcement  POST /inform/inform
# ===========================================================================

@pytest.mark.django_db
class TestInformViewPost:

    def test_publish_inform_success(self, user_client):
        """An authenticated user can publish a company-wide announcement."""
        payload = {
            'title': 'New Announcement',
            'content': 'This is the new announcement content',
            'department_ids': [],
            'is_top': False,
        }
        resp = user_client.post(INFORM_URL, payload, format='json')
        assert resp.status_code == 201
        assert resp.data['title'] == 'New Announcement'

    def test_publish_inform_missing_title_returns_400(self, user_client):
        """Missing title field should return 400."""
        resp = user_client.post(INFORM_URL, {
            'content': 'Content only, no title',
        }, format='json')
        assert resp.status_code == 400

    def test_publish_inform_unauthenticated_returns_401(self):
        c = APIClient()
        resp = c.post(INFORM_URL, {'title': 'X', 'content': 'Y'}, format='json')
        assert resp.status_code == 401

    def test_publish_top_inform_as_admin(self, admin_client):
        """An admin can publish a pinned announcement."""
        resp = admin_client.post(INFORM_URL, {
            'title': 'Pinned Announcement',
            'content': 'Important notice',
            'department_ids': [],
            'is_top': True,
        }, format='json')
        assert resp.status_code == 201
        assert resp.data['is_top'] is True


# ===========================================================================
# 3. Get announcement detail  GET /inform/inform/{pk}
# ===========================================================================

@pytest.mark.django_db
class TestInformDetailViewGet:

    def test_get_inform_detail_success(self, user_client, public_inform):
        """An announcement detail can be retrieved by its ID."""
        resp = user_client.get(f'{INFORM_URL}/{public_inform.id}')
        assert resp.status_code == 200
        assert resp.data['id'] == public_inform.id
        assert resp.data['title'] == public_inform.title

    def test_get_nonexistent_inform_returns_404(self, user_client):
        """A non-existent ID should return 404."""
        resp = user_client.get(f'{INFORM_URL}/99999')
        assert resp.status_code == 404


# ===========================================================================
# 4. Delete announcement  DELETE /inform/inform/{pk}
# ===========================================================================

@pytest.mark.django_db
class TestInformDetailViewDelete:

    def test_delete_own_inform(self, user_client, public_inform):
        """The author can delete their own announcement."""
        resp = user_client.delete(f'{INFORM_URL}/{public_inform.id}')
        assert resp.status_code == 204

    def test_delete_others_inform_returns_404(self, user2_client, public_inform):
        """A non-author, non-admin deleting someone else's announcement should return 404."""
        resp = user2_client.delete(f'{INFORM_URL}/{public_inform.id}')
        assert resp.status_code == 404

    def test_admin_can_delete_any_inform(self, admin_client, public_inform):
        """An admin can delete any user's announcement."""
        resp = admin_client.delete(f'{INFORM_URL}/{public_inform.id}')
        assert resp.status_code == 204

    def test_delete_nonexistent_inform_returns_404(self, admin_client):
        resp = admin_client.delete(f'{INFORM_URL}/99999')
        assert resp.status_code == 404


# ===========================================================================
# 5. Mark as read  POST /inform/inform/read
# ===========================================================================

@pytest.mark.django_db
class TestInformReadView:

    def test_mark_inform_read_success(self, user_client, public_inform):
        """A user can mark an announcement as read."""
        resp = user_client.post(INFORM_READ_URL, {
            'inform_pk': public_inform.id,
        }, format='json')
        assert resp.status_code in (200, 201)

    def test_mark_inform_read_twice_is_idempotent(self, user_client, public_inform):
        """Marking an announcement as read twice should not raise an error (idempotent operation)."""
        user_client.post(INFORM_READ_URL, {'inform_pk': public_inform.id}, format='json')
        resp = user_client.post(INFORM_READ_URL, {'inform_pk': public_inform.id}, format='json')
        assert resp.status_code in (200, 201)

    def test_mark_inform_read_unauthenticated_returns_401(self, public_inform):
        c = APIClient()
        resp = c.post(INFORM_READ_URL, {'inform_pk': public_inform.id}, format='json')
        assert resp.status_code == 401
