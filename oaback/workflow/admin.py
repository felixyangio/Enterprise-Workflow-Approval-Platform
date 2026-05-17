from django.contrib import admin

from .models import WorkflowActionLog, WorkflowCategory, WorkflowRequest


@admin.register(WorkflowCategory)
class WorkflowCategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'code', 'field_schema', 'is_active', 'sort_order']
    list_filter = ['field_schema', 'is_active']
    search_fields = ['name', 'code']


@admin.register(WorkflowRequest)
class WorkflowRequestAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'category', 'applicant', 'approver', 'status', 'priority', 'created_at']
    list_filter = ['status', 'priority', 'category']
    search_fields = ['title', 'applicant__realname', 'applicant__email', 'approver__realname']
    date_hierarchy = 'created_at'


@admin.register(WorkflowActionLog)
class WorkflowActionLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'request', 'actor', 'action', 'created_at']
    list_filter = ['action']
    search_fields = ['request__title', 'actor__realname', 'actor__email']
