from django.conf import settings
from django.db import models


class WorkflowCategory(models.Model):
    FIELD_DATE_RANGE = 'date_range'
    FIELD_AMOUNT = 'amount'
    FIELD_TEXT = 'text'
    FIELD_CHOICES = [
        (FIELD_DATE_RANGE, 'Date Range'),
        (FIELD_AMOUNT, 'Amount'),
        (FIELD_TEXT, 'Text Only'),
    ]

    name = models.CharField(max_length=100, unique=True, verbose_name='Category Name')
    code = models.SlugField(max_length=50, unique=True, verbose_name='Code')
    description = models.CharField(max_length=255, blank=True, default='', verbose_name='Description')
    field_schema = models.CharField(
        max_length=30,
        choices=FIELD_CHOICES,
        default=FIELD_TEXT,
        verbose_name='Field Schema'
    )
    is_active = models.BooleanField(default=True, verbose_name='Active')
    sort_order = models.PositiveSmallIntegerField(default=0, verbose_name='Sort Order')

    class Meta:
        verbose_name = 'Workflow Category'
        verbose_name_plural = verbose_name
        ordering = ['sort_order', 'id']

    def __str__(self):
        return self.name


class WorkflowRequest(models.Model):
    STATUS_DRAFT = 'draft'
    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_WITHDRAWN = 'withdrawn'
    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_WITHDRAWN, 'Withdrawn'),
    ]

    PRIORITY_LOW = 'low'
    PRIORITY_NORMAL = 'normal'
    PRIORITY_HIGH = 'high'
    PRIORITY_URGENT = 'urgent'
    PRIORITY_CHOICES = [
        (PRIORITY_LOW, 'Low'),
        (PRIORITY_NORMAL, 'Normal'),
        (PRIORITY_HIGH, 'High'),
        (PRIORITY_URGENT, 'Urgent'),
    ]

    title = models.CharField(max_length=120, verbose_name='Title')
    category = models.ForeignKey(
        WorkflowCategory,
        on_delete=models.PROTECT,
        related_name='requests',
        verbose_name='Category'
    )
    applicant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='workflow_requests',
        verbose_name='Applicant'
    )
    approver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='workflow_todos',
        verbose_name='Approver'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True,
        verbose_name='Status'
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default=PRIORITY_NORMAL,
        verbose_name='Priority'
    )
    content = models.TextField(blank=True, default='', verbose_name='Request Content')
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Amount'
    )
    start_date = models.DateField(null=True, blank=True, verbose_name='Start Date')
    end_date = models.DateField(null=True, blank=True, verbose_name='End Date')
    attachment_url = models.URLField(blank=True, default='', verbose_name='Attachment URL')
    response_content = models.TextField(blank=True, default='', verbose_name='Latest Response')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created At')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Updated At')

    class Meta:
        verbose_name = 'Workflow Request'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['applicant', '-created_at']),
            models.Index(fields=['approver', 'status']),
        ]

    def __str__(self):
        return f'{self.title} ({self.get_status_display()})'


class WorkflowActionLog(models.Model):
    ACTION_SUBMIT = 'submit'
    ACTION_APPROVE = 'approve'
    ACTION_REJECT = 'reject'
    ACTION_WITHDRAW = 'withdraw'
    ACTION_CHOICES = [
        (ACTION_SUBMIT, 'Submitted'),
        (ACTION_APPROVE, 'Approved'),
        (ACTION_REJECT, 'Rejected'),
        (ACTION_WITHDRAW, 'Withdrawn'),
    ]

    request = models.ForeignKey(
        WorkflowRequest,
        on_delete=models.CASCADE,
        related_name='logs',
        verbose_name='Workflow Request'
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='workflow_actions',
        verbose_name='Actor'
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, verbose_name='Action')
    comment = models.TextField(blank=True, default='', verbose_name='Comment')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created At')

    class Meta:
        verbose_name = 'Workflow Action Log'
        verbose_name_plural = verbose_name
        ordering = ['created_at', 'id']

    def __str__(self):
        actor = self.actor.realname if self.actor else 'System'
        return f'{actor} {self.action} {self.request_id}'
