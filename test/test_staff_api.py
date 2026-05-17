import csv
import io

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from staff.models import Department, Staff

User = get_user_model()


def authenticated_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        email='staff-admin@test.com',
        password='admin1234',
        realname='Staff Admin',
    )


@pytest.fixture
def normal_user(db):
    return User.objects.create_user(
        email='staff-user@test.com',
        password='pass1234',
        realname='Staff User',
    )


@pytest.fixture
def department(db):
    return Department.objects.create(name='Engineering')


@pytest.mark.django_db
class TestStaffDownloadApi:
    def test_download_requires_superuser(self, normal_user):
        response = authenticated_client(normal_user).get('/staff/download')

        assert response.status_code == 403

    def test_download_selected_staff_as_csv(self, admin_user, department):
        exported_user = User.objects.create_user(
            email='exported@test.com',
            password='pass1234',
            realname='Exported User',
        )
        skipped_user = User.objects.create_user(
            email='skipped@test.com',
            password='pass1234',
            realname='Skipped User',
        )
        exported = Staff.objects.create(user=exported_user, department=department)
        Staff.objects.create(user=skipped_user, department=department)

        response = authenticated_client(admin_user).get('/staff/download', {'pks': f'[{exported.id}]'})

        assert response.status_code == 200
        assert response['Content-Type'].startswith('text/csv')
        rows = list(csv.reader(io.StringIO(response.content.decode('utf-8'))))
        assert rows[0] == ['Name', 'Email', 'Department', 'Status', 'Join Date']
        assert rows[1][0:4] == ['Exported User', 'exported@test.com', 'Engineering', 'Active']
        assert len(rows) == 2
