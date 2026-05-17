import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


DEFAULT_CATEGORIES = [
    ('Leave Request', 'leave', 'Request paid leave, sick leave, or personal leave.', 'date_range', 10),
    ('Overtime Request', 'overtime', 'Request approval for overtime work.', 'date_range', 20),
    ('Expense Reimbursement', 'expense', 'Request reimbursement for business expenses.', 'amount', 30),
    ('Purchase Request', 'purchase', 'Request approval for office or project purchases.', 'amount', 40),
    ('Remote Work Request', 'remote-work', 'Request approval to work remotely.', 'date_range', 50),
]


def seed_categories(apps, schema_editor):
    WorkflowCategory = apps.get_model('workflow', 'WorkflowCategory')
    for name, code, description, field_schema, sort_order in DEFAULT_CATEGORIES:
        WorkflowCategory.objects.get_or_create(
            code=code,
            defaults={
                'name': name,
                'description': description,
                'field_schema': field_schema,
                'sort_order': sort_order,
            }
        )


def copy_absents(apps, schema_editor):
    WorkflowCategory = apps.get_model('workflow', 'WorkflowCategory')
    WorkflowRequest = apps.get_model('workflow', 'WorkflowRequest')
    WorkflowActionLog = apps.get_model('workflow', 'WorkflowActionLog')
    Absent = apps.get_model('absent', 'Absent')

    leave_category, _ = WorkflowCategory.objects.get_or_create(
        code='leave',
        defaults={
            'name': 'Leave Request',
            'description': 'Request paid leave, sick leave, or personal leave.',
            'field_schema': 'date_range',
            'sort_order': 10,
        }
    )
    status_map = {
        1: 'pending',
        2: 'approved',
        0: 'rejected',
    }
    action_map = {
        'pending': 'submit',
        'approved': 'approve',
        'rejected': 'reject',
    }

    for absent in Absent.objects.all():
        workflow_request, created = WorkflowRequest.objects.get_or_create(
            title=absent.title or 'Leave Request',
            applicant_id=absent.applicant_id,
            created_at=absent.create_time,
            defaults={
                'category': leave_category,
                'approver_id': absent.responder_id,
                'status': status_map.get(absent.status, 'pending'),
                'priority': 'normal',
                'content': absent.request_content or '',
                'start_date': absent.start_date,
                'end_date': absent.end_date,
                'response_content': absent.response_content or '',
                'updated_at': absent.create_time,
            }
        )
        if created:
            WorkflowActionLog.objects.create(
                request=workflow_request,
                actor_id=absent.applicant_id,
                action='submit',
                comment='Migrated from legacy leave request.',
                created_at=absent.create_time,
            )
            final_action = action_map.get(workflow_request.status)
            if final_action and final_action != 'submit':
                WorkflowActionLog.objects.create(
                    request=workflow_request,
                    actor_id=absent.responder_id,
                    action=final_action,
                    comment=absent.response_content or '',
                    created_at=absent.create_time,
                )


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('absent', '0002_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='WorkflowCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True, verbose_name='Category Name')),
                ('code', models.SlugField(max_length=50, unique=True, verbose_name='Code')),
                ('description', models.CharField(blank=True, default='', max_length=255, verbose_name='Description')),
                ('field_schema', models.CharField(choices=[('date_range', 'Date Range'), ('amount', 'Amount'), ('text', 'Text Only')], default='text', max_length=30, verbose_name='Field Schema')),
                ('is_active', models.BooleanField(default=True, verbose_name='Active')),
                ('sort_order', models.PositiveSmallIntegerField(default=0, verbose_name='Sort Order')),
            ],
            options={
                'verbose_name': 'Workflow Category',
                'verbose_name_plural': 'Workflow Category',
                'ordering': ['sort_order', 'id'],
            },
        ),
        migrations.CreateModel(
            name='WorkflowRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=120, verbose_name='Title')),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('withdrawn', 'Withdrawn')], db_index=True, default='pending', max_length=20, verbose_name='Status')),
                ('priority', models.CharField(choices=[('low', 'Low'), ('normal', 'Normal'), ('high', 'High'), ('urgent', 'Urgent')], default='normal', max_length=20, verbose_name='Priority')),
                ('content', models.TextField(blank=True, default='', verbose_name='Request Content')),
                ('amount', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Amount')),
                ('start_date', models.DateField(blank=True, null=True, verbose_name='Start Date')),
                ('end_date', models.DateField(blank=True, null=True, verbose_name='End Date')),
                ('attachment_url', models.URLField(blank=True, default='', verbose_name='Attachment URL')),
                ('response_content', models.TextField(blank=True, default='', verbose_name='Latest Response')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated At')),
                ('applicant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='workflow_requests', to=settings.AUTH_USER_MODEL, verbose_name='Applicant')),
                ('approver', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='workflow_todos', to=settings.AUTH_USER_MODEL, verbose_name='Approver')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='requests', to='workflow.workflowcategory', verbose_name='Category')),
            ],
            options={
                'verbose_name': 'Workflow Request',
                'verbose_name_plural': 'Workflow Request',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='WorkflowActionLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(choices=[('submit', 'Submitted'), ('approve', 'Approved'), ('reject', 'Rejected'), ('withdraw', 'Withdrawn')], max_length=20, verbose_name='Action')),
                ('comment', models.TextField(blank=True, default='', verbose_name='Comment')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('actor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='workflow_actions', to=settings.AUTH_USER_MODEL, verbose_name='Actor')),
                ('request', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='logs', to='workflow.workflowrequest', verbose_name='Workflow Request')),
            ],
            options={
                'verbose_name': 'Workflow Action Log',
                'verbose_name_plural': 'Workflow Action Log',
                'ordering': ['created_at', 'id'],
            },
        ),
        migrations.AddIndex(
            model_name='workflowrequest',
            index=models.Index(fields=['status', '-created_at'], name='workflow_wo_status_0f2f28_idx'),
        ),
        migrations.AddIndex(
            model_name='workflowrequest',
            index=models.Index(fields=['applicant', '-created_at'], name='workflow_wo_applica_c3894a_idx'),
        ),
        migrations.AddIndex(
            model_name='workflowrequest',
            index=models.Index(fields=['approver', 'status'], name='workflow_wo_approve_f7461b_idx'),
        ),
        migrations.RunPython(seed_categories, migrations.RunPython.noop),
        migrations.RunPython(copy_absents, migrations.RunPython.noop),
    ]
