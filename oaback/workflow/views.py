from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import WorkflowActionLog, WorkflowCategory, WorkflowRequest
from .serializers import (
    WorkflowActionLogSerializer,
    WorkflowCategorySerializer,
    WorkflowDecisionSerializer,
    WorkflowRequestCreateSerializer,
    WorkflowRequestSerializer,
)

User = get_user_model()


def get_default_approver(user):
    return (
        User.objects
        .filter(is_superuser=True, is_active=True)
        .exclude(pk=user.pk)
        .first()
    )


def can_view_request(user, workflow_request):
    return (
        user.is_superuser
        or workflow_request.applicant_id == user.id
        or workflow_request.approver_id == user.id
    )


def create_log(workflow_request, actor, action, comment=''):
    return WorkflowActionLog.objects.create(
        request=workflow_request,
        actor=actor,
        action=action,
        comment=comment or '',
    )


class WorkflowCategoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        categories = WorkflowCategory.objects.filter(is_active=True)
        return Response(WorkflowCategorySerializer(categories, many=True).data)


class WorkflowRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        scope = request.query_params.get('scope', 'mine')
        page = max(int(request.query_params.get('page', 1)), 1)
        size = min(max(int(request.query_params.get('size', 10)), 1), 100)
        queryset = (
            WorkflowRequest.objects
            .select_related('category', 'applicant', 'approver')
            .prefetch_related('logs__actor')
            .all()
        )

        if scope == 'mine':
            queryset = queryset.filter(applicant=request.user)
        elif scope == 'todo':
            if request.user.is_superuser:
                queryset = queryset.filter(status=WorkflowRequest.STATUS_PENDING)
            else:
                queryset = queryset.filter(approver=request.user, status=WorkflowRequest.STATUS_PENDING)
        elif scope == 'all':
            if not request.user.is_superuser:
                raise PermissionDenied('Only superusers can view all workflow requests.')
        else:
            return Response({'detail': 'Invalid scope'}, status=status.HTTP_400_BAD_REQUEST)

        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        category_id = request.query_params.get('category') or request.query_params.get('category_id')
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        keyword = request.query_params.get('keyword') or request.query_params.get('title')
        if keyword:
            queryset = queryset.filter(
                Q(title__icontains=keyword)
                | Q(applicant__realname__icontains=keyword)
                | Q(applicant__email__icontains=keyword)
            )

        total = queryset.count()
        start = (page - 1) * size
        items = queryset[start:start + size]
        return Response({
            'total': total,
            'count': total,
            'page': page,
            'size': size,
            'items': WorkflowRequestSerializer(items, many=True).data,
            'results': WorkflowRequestSerializer(items, many=True).data,
        })

    def post(self, request):
        serializer = WorkflowRequestCreateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        approver = data.get('approver') or get_default_approver(request.user)
        workflow_request = WorkflowRequest.objects.create(
            title=data['title'],
            category=data['category'],
            applicant=request.user,
            approver=approver,
            priority=data.get('priority', WorkflowRequest.PRIORITY_NORMAL),
            content=data.get('content', ''),
            amount=data.get('amount'),
            start_date=data.get('start_date'),
            end_date=data.get('end_date'),
            attachment_url=data.get('attachment_url', ''),
        )
        create_log(workflow_request, request.user, WorkflowActionLog.ACTION_SUBMIT, 'Request submitted')
        return Response(WorkflowRequestSerializer(workflow_request).data, status=status.HTTP_201_CREATED)


class WorkflowRequestDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, request, pk):
        try:
            workflow_request = (
                WorkflowRequest.objects
                .select_related('category', 'applicant', 'approver')
                .prefetch_related('logs__actor')
                .get(pk=pk)
            )
        except WorkflowRequest.DoesNotExist:
            return None
        if not can_view_request(request.user, workflow_request):
            raise PermissionDenied('You do not have permission to access this request.')
        return workflow_request

    def get(self, request, pk):
        workflow_request = self.get_object(request, pk)
        if not workflow_request:
            return Response({'detail': 'Workflow request not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(WorkflowRequestSerializer(workflow_request).data)


class WorkflowRequestLogsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            workflow_request = WorkflowRequest.objects.get(pk=pk)
        except WorkflowRequest.DoesNotExist:
            return Response({'detail': 'Workflow request not found'}, status=status.HTTP_404_NOT_FOUND)
        if not can_view_request(request.user, workflow_request):
            raise PermissionDenied('You do not have permission to access this request.')
        logs = WorkflowActionLog.objects.select_related('actor').filter(request=workflow_request)
        return Response(WorkflowActionLogSerializer(logs, many=True).data)


class WorkflowRequestActionView(APIView):
    permission_classes = [IsAuthenticated]
    action = None

    def put(self, request, pk):
        try:
            workflow_request = WorkflowRequest.objects.select_related('applicant', 'approver').get(pk=pk)
        except WorkflowRequest.DoesNotExist:
            return Response({'detail': 'Workflow request not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = WorkflowDecisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comment = serializer.validated_data.get('comment', '')

        if self.action == WorkflowActionLog.ACTION_WITHDRAW:
            if workflow_request.applicant_id != request.user.id:
                raise PermissionDenied('Only the applicant can withdraw this request.')
            if workflow_request.status != WorkflowRequest.STATUS_PENDING:
                return Response({'detail': 'Only pending requests can be withdrawn.'}, status=status.HTTP_400_BAD_REQUEST)
            workflow_request.status = WorkflowRequest.STATUS_WITHDRAWN
            workflow_request.response_content = comment
            workflow_request.save(update_fields=['status', 'response_content', 'updated_at'])
            create_log(workflow_request, request.user, WorkflowActionLog.ACTION_WITHDRAW, comment)
            return Response(WorkflowRequestSerializer(workflow_request).data)

        if workflow_request.status != WorkflowRequest.STATUS_PENDING:
            return Response({'detail': 'Only pending requests can be processed.'}, status=status.HTTP_400_BAD_REQUEST)
        if workflow_request.applicant_id == request.user.id:
            raise PermissionDenied('Applicant cannot approve their own request.')
        if not request.user.is_superuser and workflow_request.approver_id != request.user.id:
            raise PermissionDenied('Only the approver can process this request.')

        if self.action == WorkflowActionLog.ACTION_APPROVE:
            workflow_request.status = WorkflowRequest.STATUS_APPROVED
            log_action = WorkflowActionLog.ACTION_APPROVE
        elif self.action == WorkflowActionLog.ACTION_REJECT:
            workflow_request.status = WorkflowRequest.STATUS_REJECTED
            log_action = WorkflowActionLog.ACTION_REJECT
        else:
            return Response({'detail': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)

        workflow_request.response_content = comment
        workflow_request.save(update_fields=['status', 'response_content', 'updated_at'])
        create_log(workflow_request, request.user, log_action, comment)
        return Response(WorkflowRequestSerializer(workflow_request).data)


class WorkflowApproveView(WorkflowRequestActionView):
    action = WorkflowActionLog.ACTION_APPROVE


class WorkflowRejectView(WorkflowRequestActionView):
    action = WorkflowActionLog.ACTION_REJECT


class WorkflowWithdrawView(WorkflowRequestActionView):
    action = WorkflowActionLog.ACTION_WITHDRAW


class WorkflowSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        mine = WorkflowRequest.objects.filter(applicant=request.user)
        if request.user.is_superuser:
            todo = WorkflowRequest.objects.filter(status=WorkflowRequest.STATUS_PENDING)
        else:
            todo = WorkflowRequest.objects.filter(approver=request.user, status=WorkflowRequest.STATUS_PENDING)
        by_category = (
            WorkflowRequest.objects
            .values('category__name')
            .annotate(count=Count('id'))
            .order_by('category__name')
        )
        visible_requests = WorkflowRequest.objects.all() if request.user.is_superuser else mine
        by_status_counts = {
            row['status']: row['count']
            for row in visible_requests.values('status').annotate(count=Count('id'))
        }
        return Response({
            'my_pending': mine.filter(status=WorkflowRequest.STATUS_PENDING).count(),
            'my_approved': mine.filter(status=WorkflowRequest.STATUS_APPROVED).count(),
            'todo': todo.count(),
            'total': WorkflowRequest.objects.count() if request.user.is_superuser else mine.count(),
            'by_category': [{'name': row['category__name'], 'count': row['count']} for row in by_category],
            'by_status': [
                {
                    'status': status_value,
                    'label': status_label,
                    'count': by_status_counts.get(status_value, 0),
                }
                for status_value, status_label in WorkflowRequest.STATUS_CHOICES
            ],
        })
