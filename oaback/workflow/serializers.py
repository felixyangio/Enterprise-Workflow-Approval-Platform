from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import WorkflowActionLog, WorkflowCategory, WorkflowRequest

User = get_user_model()


class WorkflowCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowCategory
        fields = ['id', 'name', 'code', 'description', 'field_schema', 'is_active', 'sort_order']


class UserBriefSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    email = serializers.EmailField()
    realname = serializers.CharField()
    department = serializers.SerializerMethodField()

    def get_department(self, user):
        try:
            dept = user.staff_profile.department
            if dept:
                return {'id': dept.id, 'name': dept.name}
        except Exception:
            pass
        return {'id': None, 'name': ''}


class WorkflowActionLogSerializer(serializers.ModelSerializer):
    actor = UserBriefSerializer(read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)

    class Meta:
        model = WorkflowActionLog
        fields = ['id', 'actor', 'action', 'action_display', 'comment', 'created_at']


class WorkflowRequestSerializer(serializers.ModelSerializer):
    category = WorkflowCategorySerializer(read_only=True)
    applicant = UserBriefSerializer(read_only=True)
    approver = UserBriefSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    logs = WorkflowActionLogSerializer(many=True, read_only=True)

    class Meta:
        model = WorkflowRequest
        fields = [
            'id', 'title', 'category', 'applicant', 'approver', 'status', 'status_display',
            'priority', 'priority_display', 'content', 'amount', 'start_date', 'end_date',
            'attachment_url', 'response_content', 'created_at', 'updated_at', 'logs'
        ]


class WorkflowRequestCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=120)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=WorkflowCategory.objects.filter(is_active=True),
        source='category'
    )
    approver_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='approver',
        required=False,
        allow_null=True,
        default=None
    )
    priority = serializers.ChoiceField(
        choices=[choice[0] for choice in WorkflowRequest.PRIORITY_CHOICES],
        default=WorkflowRequest.PRIORITY_NORMAL
    )
    content = serializers.CharField(required=False, allow_blank=True, default='')
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    start_date = serializers.DateField(required=False, allow_null=True)
    end_date = serializers.DateField(required=False, allow_null=True)
    attachment_url = serializers.URLField(required=False, allow_blank=True, default='')

    def validate(self, attrs):
        category = attrs['category']
        amount = attrs.get('amount')
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')

        if category.field_schema == WorkflowCategory.FIELD_AMOUNT:
            if amount is None:
                raise serializers.ValidationError({'amount': 'Amount is required for this request type.'})
            if amount <= Decimal('0'):
                raise serializers.ValidationError({'amount': 'Amount must be greater than 0.'})

        if category.field_schema == WorkflowCategory.FIELD_DATE_RANGE:
            if not start_date or not end_date:
                raise serializers.ValidationError({'date_range': 'Start date and end date are required.'})
            if start_date > end_date:
                raise serializers.ValidationError({'date_range': 'Start date cannot be later than end date.'})

        approver = attrs.get('approver')
        request = self.context.get('request')
        if approver and request and approver.pk == request.user.pk:
            raise serializers.ValidationError({'approver_id': 'Applicant cannot approve their own request.'})
        return attrs


class WorkflowDecisionSerializer(serializers.Serializer):
    comment = serializers.CharField(required=False, allow_blank=True, default='')
