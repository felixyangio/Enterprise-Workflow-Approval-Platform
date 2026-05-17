"""
test_models.py
==============
Unit tests for core business models, covering:
  - authapp.User / UserManager
  - staff.Department / Staff
  - absent.AbsentType / Absent
  - inform.Inform / InformRead

How to run:
    cd test
    pytest test_models.py -v
"""

import datetime
import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


# ---------------------------------------------------------------------------
# Fixtures (shared test data factories)
# ---------------------------------------------------------------------------

@pytest.fixture
def make_user(db):
    """Factory function: quickly create a regular user."""
    def _make(email='test@example.com', password='pass1234', realname='Test User', **kwargs):
        return User.objects.create_user(email=email, password=password, realname=realname, **kwargs)
    return _make


@pytest.fixture
def make_superuser(db):
    """Factory function: quickly create a superuser."""
    def _make(email='admin@example.com', password='admin1234', realname='Admin', **kwargs):
        return User.objects.create_superuser(email=email, password=password, realname=realname, **kwargs)
    return _make


@pytest.fixture
def department(db):
    """Create a test department."""
    from staff.models import Department
    return Department.objects.create(name='Engineering', intro='Responsible for product R&D')


@pytest.fixture
def absent_type(db):
    """Create a leave type."""
    from absent.models import AbsentType
    return AbsentType.objects.create(name='Annual Leave')


# ===========================================================================
# 1. authapp.User model tests
# ===========================================================================

@pytest.mark.django_db
class TestUserModel:
    """Tests for the custom user model's basic behaviors."""

    def test_create_user_success(self, make_user):
        """A regular user should be created successfully with a hashed password."""
        user = make_user(email='alice@example.com', password='securePass1', realname='Alice')
        assert user.pk is not None
        assert user.email == 'alice@example.com'
        assert user.realname == 'Alice'
        # Password must be hashed, not equal to the plain text
        assert user.password != 'securePass1'
        assert user.check_password('securePass1')

    def test_create_user_missing_email_raises(self):
        """Creating a user without an email should raise ValueError."""
        with pytest.raises(ValueError, match='Email cannot be empty'):
            User.objects.create_user(email='', password='pass1234', realname='Bob')

    def test_create_superuser_flags(self, make_superuser):
        """Superuser should have is_staff=True and is_superuser=True."""
        admin = make_superuser()
        assert admin.is_staff is True
        assert admin.is_superuser is True

    def test_user_str_representation(self, make_user):
        """User __str__ should contain the user's name and email."""
        user = make_user(email='bob@example.com', realname='Bob')
        assert 'Bob' in str(user)
        assert 'bob@example.com' in str(user)

    def test_user_is_active_by_default(self, make_user):
        """A newly created user should be active by default."""
        user = make_user(email='carol@example.com')
        assert user.is_active is True

    def test_email_is_unique(self, make_user, db):
        """Two users cannot share the same email."""
        from django.db import IntegrityError
        make_user(email='dup@example.com')
        with pytest.raises(IntegrityError):
            User.objects.create_user(email='dup@example.com', password='p', realname='Dup')


# ===========================================================================
# 2. staff.Department / Staff model tests
# ===========================================================================

@pytest.mark.django_db
class TestDepartmentModel:
    """Tests for the Department model."""

    def test_create_department(self, db):
        from staff.models import Department
        dept = Department.objects.create(name='HR Department', intro='Responsible for recruitment')
        assert dept.pk is not None
        assert str(dept) == 'HR Department'

    def test_department_intro_optional(self, db):
        from staff.models import Department
        dept = Department.objects.create(name='Finance Department')
        assert dept.intro == ''  # blank/default=''


@pytest.mark.django_db
class TestStaffModel:
    """Tests for the Staff model."""

    def test_create_staff_with_department(self, make_user, department):
        from staff.models import Staff
        user = make_user(email='dave@example.com', realname='Dave')
        staff = Staff.objects.create(user=user, department=department, uid='EMP001')
        assert staff.pk is not None
        assert staff.department == department
        assert staff.status == Staff.STATUS_ACTIVE  # Default status should be active

    def test_staff_str_representation(self, make_user, department):
        from staff.models import Staff
        user = make_user(email='eve@example.com', realname='Eve')
        staff = Staff.objects.create(user=user, department=department)
        # __str__ should contain user info
        assert str(staff)

    def test_staff_default_status_is_active(self, make_user):
        from staff.models import Staff
        user = make_user(email='frank@example.com', realname='Frank')
        staff = Staff.objects.create(user=user)
        assert staff.status == Staff.STATUS_ACTIVE

    def test_staff_status_choices(self):
        from staff.models import Staff
        codes = [choice[0] for choice in Staff.STATUS_CHOICES]
        assert Staff.STATUS_ACTIVE in codes
        assert Staff.STATUS_INACTIVE in codes
        assert Staff.STATUS_LOCKED in codes


# ===========================================================================
# 3. absent.AbsentType / Absent model tests
# ===========================================================================

@pytest.mark.django_db
class TestAbsentTypeModel:
    """Tests for the AbsentType model."""

    def test_create_absent_type(self, db):
        from absent.models import AbsentType
        atype = AbsentType.objects.create(name='Sick Leave')
        assert atype.pk is not None
        assert str(atype) == 'Sick Leave'


@pytest.mark.django_db
class TestAbsentModel:
    """Tests for the core business logic of the Absent model."""

    def test_create_absent_default_status_pending(self, make_user, absent_type):
        """A newly created leave request should have pending status."""
        from absent.models import Absent
        applicant = make_user(email='g@example.com', realname='G')
        absent = Absent.objects.create(
            title='Annual Leave Request',
            applicant=applicant,
            absent_type=absent_type,
            start_date=datetime.date(2026, 4, 1),
            end_date=datetime.date(2026, 4, 3),
        )
        assert absent.status == Absent.STATUS_PENDING

    def test_absent_str_representation(self, make_user, absent_type):
        from absent.models import Absent
        applicant = make_user(email='h@example.com', realname='H')
        absent = Absent.objects.create(
            applicant=applicant,
            absent_type=absent_type,
            start_date=datetime.date(2026, 4, 1),
            end_date=datetime.date(2026, 4, 2),
        )
        result = str(absent)
        assert result  # should not be empty

    def test_absent_status_constants(self):
        from absent.models import Absent
        assert Absent.STATUS_PENDING == 1
        assert Absent.STATUS_APPROVED == 2
        assert Absent.STATUS_REJECTED == 0

    def test_absent_ordering_is_by_create_time_desc(self, make_user, absent_type):
        """Leave requests should be ordered by creation time descending."""
        from absent.models import Absent
        assert Absent._meta.ordering == ['-create_time']


# ===========================================================================
# 4. inform.Inform / InformRead model tests
# ===========================================================================

@pytest.mark.django_db
class TestInformModel:
    """Tests for the Inform model."""

    def test_create_inform(self, make_user):
        from inform.models import Inform
        author = make_user(email='j@example.com', realname='J')
        inform = Inform.objects.create(
            title='Test Announcement',
            content='This is test announcement content',
            author=author,
        )
        assert inform.pk is not None
        assert str(inform) == 'Test Announcement'

    def test_inform_is_top_default_false(self, make_user):
        from inform.models import Inform
        author = make_user(email='k@example.com', realname='K')
        inform = Inform.objects.create(title='Regular Announcement', content='Content', author=author)
        assert inform.is_top is False

    def test_inform_with_departments(self, make_user, department):
        """An announcement can be associated with multiple departments (visibility control)."""
        from inform.models import Inform
        author = make_user(email='l@example.com', realname='L')
        inform = Inform.objects.create(title='Department Announcement', content='Visible to Engineering only', author=author)
        inform.departments.add(department)
        assert department in inform.departments.all()

    def test_inform_ordering_top_first(self, make_user):
        """Pinned announcements should appear before regular ones."""
        from inform.models import Inform
        author = make_user(email='m@example.com', realname='M')
        normal = Inform.objects.create(title='Regular', content='Content', author=author, is_top=False)
        top = Inform.objects.create(title='Pinned', content='Content', author=author, is_top=True)
        informs = list(Inform.objects.all())
        assert informs[0].pk == top.pk


@pytest.mark.django_db
class TestInformReadModel:
    """Tests for the InformRead model."""

    def test_create_read_record(self, make_user):
        from inform.models import Inform, InformRead
        author = make_user(email='n@example.com', realname='N')
        reader = make_user(email='o@example.com', realname='O')
        inform = Inform.objects.create(title='Readable Announcement', content='Content', author=author)
        record = InformRead.objects.create(inform=inform, reader=reader)
        assert record.pk is not None

    def test_read_record_unique_together(self, make_user):
        """A user can only have one read record per announcement (unique constraint)."""
        from django.db import IntegrityError
        from inform.models import Inform, InformRead
        author = make_user(email='p@example.com', realname='P')
        reader = make_user(email='q@example.com', realname='Q')
        inform = Inform.objects.create(title='Unique Read Test', content='Content', author=author)
        InformRead.objects.create(inform=inform, reader=reader)
        with pytest.raises(IntegrityError):
            InformRead.objects.create(inform=inform, reader=reader)
