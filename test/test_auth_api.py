"""
test_auth_api.py
================
Authentication API tests, covering:
  - POST /auth/login     Login endpoint
  - POST /auth/resetpwd  Change password endpoint

How to run:
    cd test
    pytest test_auth_api.py -v
"""

import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()

LOGIN_URL = '/auth/login'
RESETPWD_URL = '/auth/resetpwd'


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client():
    """Return an unauthenticated DRF test client."""
    return APIClient()


@pytest.fixture
def normal_user(db):
    """Create a regular user with password 'test@Pass1'."""
    return User.objects.create_user(
        email='user@test.com',
        password='test@Pass1',
        realname='Regular User',
    )


@pytest.fixture
def auth_client(normal_user):
    """Return a DRF test client authenticated as the normal user (JWT)."""
    client = APIClient()
    resp = client.post(LOGIN_URL, {'email': 'user@test.com', 'password': 'test@Pass1'}, format='json')
    token = resp.data.get('token')
    client.credentials(HTTP_AUTHORIZATION=f'JWT {token}')
    return client


# ===========================================================================
# 1. Login endpoint tests  POST /auth/login
# ===========================================================================

@pytest.mark.django_db
class TestLoginView:
    """Tests for the login endpoint's various scenarios."""

    def test_login_success_returns_token(self, client, normal_user):
        """Correct email and password should return a JWT token and user info."""
        resp = client.post(LOGIN_URL, {
            'email': 'user@test.com',
            'password': 'test@Pass1',
        }, format='json')
        assert resp.status_code == 200
        assert 'token' in resp.data
        assert 'refresh' in resp.data
        assert 'user' in resp.data
        assert resp.data['user']['email'] == 'user@test.com'

    def test_login_wrong_password_returns_400(self, client, normal_user):
        """Wrong password should return 400 without leaking a token."""
        resp = client.post(LOGIN_URL, {
            'email': 'user@test.com',
            'password': 'wrongpassword',
        }, format='json')
        assert resp.status_code == 400
        assert 'token' not in resp.data

    def test_login_nonexistent_email_returns_400(self, client, db):
        """A non-existent email should return 400."""
        resp = client.post(LOGIN_URL, {
            'email': 'nobody@test.com',
            'password': 'somepassword',
        }, format='json')
        assert resp.status_code == 400

    def test_login_missing_fields_returns_400(self, client, db):
        """Missing required fields (email / password) should return 400."""
        resp = client.post(LOGIN_URL, {'email': 'user@test.com'}, format='json')
        assert resp.status_code == 400

    def test_login_inactive_user_returns_400(self, client, db):
        """Logging in with a deactivated account should return 400."""
        User.objects.create_user(
            email='inactive@test.com',
            password='pass1234',
            realname='Inactive User',
            is_active=False,
        )
        resp = client.post(LOGIN_URL, {
            'email': 'inactive@test.com',
            'password': 'pass1234',
        }, format='json')
        assert resp.status_code == 400

    def test_login_returns_user_info_fields(self, client, normal_user):
        """The user field in the login response should contain id, email, realname, is_superuser."""
        resp = client.post(LOGIN_URL, {
            'email': 'user@test.com',
            'password': 'test@Pass1',
        }, format='json')
        user_data = resp.data['user']
        for field in ('id', 'email', 'realname', 'is_superuser'):
            assert field in user_data


# ===========================================================================
# 2. Change password endpoint tests  POST /auth/resetpwd
# ===========================================================================

@pytest.mark.django_db
class TestResetPwdView:
    """Tests for the change password endpoint."""

    def test_reset_password_success(self, auth_client, normal_user):
        """Correct old password and matching new passwords should succeed."""
        resp = auth_client.post(RESETPWD_URL, {
            'oldpwd': 'test@Pass1',
            'pwd1': 'newPass@456',
            'pwd2': 'newPass@456',
        }, format='json')
        assert resp.status_code == 200
        # Verify the password has changed
        normal_user.refresh_from_db()
        assert normal_user.check_password('newPass@456')

    def test_reset_password_wrong_old_pwd_returns_400(self, auth_client):
        """Wrong old password should return 400, leaving the password unchanged."""
        resp = auth_client.post(RESETPWD_URL, {
            'oldpwd': 'wrongOldPwd',
            'pwd1': 'newPass@456',
            'pwd2': 'newPass@456',
        }, format='json')
        assert resp.status_code == 400

    def test_reset_password_mismatch_returns_400(self, auth_client):
        """Mismatched new passwords should return 400."""
        resp = auth_client.post(RESETPWD_URL, {
            'oldpwd': 'test@Pass1',
            'pwd1': 'newPass@456',
            'pwd2': 'different@789',
        }, format='json')
        assert resp.status_code == 400

    def test_reset_password_requires_auth(self, client):
        """Unauthenticated access to the change password endpoint should return 401."""
        resp = client.post(RESETPWD_URL, {
            'oldpwd': 'test@Pass1',
            'pwd1': 'newPass@456',
            'pwd2': 'newPass@456',
        }, format='json')
        assert resp.status_code == 401

    def test_reset_password_too_short_returns_400(self, auth_client):
        """A new password shorter than 6 characters should return 400 (serializer min_length validation)."""
        resp = auth_client.post(RESETPWD_URL, {
            'oldpwd': 'test@Pass1',
            'pwd1': '123',
            'pwd2': '123',
        }, format='json')
        assert resp.status_code == 400
