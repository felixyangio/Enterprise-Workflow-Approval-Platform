from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from staff.models import Department, Staff
from workflow.models import WorkflowActionLog, WorkflowCategory, WorkflowRequest


class Command(BaseCommand):
    help = 'Seed departments, demo users, workflow categories, and sample workflow requests.'

    def handle(self, *args, **options):
        User = get_user_model()

        admin = User.objects.filter(is_superuser=True).first()
        if not admin:
            admin = User.objects.create_superuser(
                email='admin@example.com',
                password='Admin@123456',
                realname='System Administrator',
            )
            self.stdout.write(self.style.SUCCESS('Created demo admin: admin@example.com / Admin@123456'))

        departments = [
            ('Administration', 'Company operations and employee service'),
            ('Human Resources', 'Recruiting, onboarding, and policy support'),
            ('Finance', 'Budget, reimbursement, and procurement review'),
            ('Engineering', 'Product and platform delivery'),
        ]
        dept_map = {}
        for name, intro in departments:
            dept, _ = Department.objects.get_or_create(name=name, defaults={'intro': intro})
            dept_map[name] = dept

        Staff.objects.get_or_create(user=admin, defaults={'department': dept_map['Administration'], 'uid': 'A0001'})

        demo_user, created = User.objects.get_or_create(
            email='employee@example.com',
            defaults={'realname': 'Demo Employee'}
        )
        if created:
            demo_user.set_password('Employee@123456')
            demo_user.save()
            self.stdout.write(self.style.SUCCESS('Created demo employee: employee@example.com / Employee@123456'))
        Staff.objects.get_or_create(user=demo_user, defaults={'department': dept_map['Engineering'], 'uid': 'E0001'})

        categories = [
            ('Leave Request', 'leave', 'Request paid leave, sick leave, or personal leave.', 'date_range', 10),
            ('Overtime Request', 'overtime', 'Request approval for overtime work.', 'date_range', 20),
            ('Expense Reimbursement', 'expense', 'Request reimbursement for business expenses.', 'amount', 30),
            ('Purchase Request', 'purchase', 'Request approval for office or project purchases.', 'amount', 40),
            ('Remote Work Request', 'remote-work', 'Request approval to work remotely.', 'date_range', 50),
        ]
        category_map = {}
        for name, code, description, field_schema, sort_order in categories:
            category, _ = WorkflowCategory.objects.update_or_create(
                code=code,
                defaults={
                    'name': name,
                    'description': description,
                    'field_schema': field_schema,
                    'sort_order': sort_order,
                    'is_active': True,
                }
            )
            category_map[code] = category

        request, created = WorkflowRequest.objects.get_or_create(
            title='Demo remote work request',
            applicant=demo_user,
            defaults={
                'category': category_map['remote-work'],
                'approver': admin,
                'status': WorkflowRequest.STATUS_PENDING,
                'priority': WorkflowRequest.PRIORITY_NORMAL,
                'content': 'Work from home to focus on release documentation.',
                'start_date': '2026-06-01',
                'end_date': '2026-06-02',
            }
        )
        if created:
            WorkflowActionLog.objects.create(
                request=request,
                actor=demo_user,
                action=WorkflowActionLog.ACTION_SUBMIT,
                comment='Seed sample request.',
            )

        self.stdout.write(self.style.SUCCESS('Workflow seed data is ready.'))
