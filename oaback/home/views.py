from django.db.models import Count
from django.db.models import Q
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from inform.models import Inform, InformRead
from staff.models import Department
from workflow.models import WorkflowRequest
from workflow.serializers import WorkflowRequestSerializer


class DepartmentStaffCountView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = (
            Department.objects
            .annotate(staff_count=Count('staffs'))
            .values('name', 'staff_count')
        )
        return Response(list(data))


class LatestInformView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        informs = Inform.objects.select_related('author').prefetch_related('departments').order_by('-create_time')
        if not request.user.is_superuser:
            try:
                user_dept = request.user.staff_profile.department
            except Exception:
                user_dept = None
            if user_dept:
                informs = informs.filter(Q(departments__isnull=True) | Q(departments=user_dept)).distinct()
            else:
                informs = informs.filter(departments__isnull=True)
        informs = informs[:10]
        result = []
        for inform in informs:
            reads = InformRead.objects.filter(inform=inform, reader=request.user)
            result.append({
                'id': inform.id,
                'title': inform.title,
                'author': {
                    'realname': inform.author.realname,
                },
                'create_time': inform.create_time,
                'reads': list(reads.values('id')),
            })
        return Response(result)


class LatestAbsentView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.is_superuser:
            requests = WorkflowRequest.objects.all()
        else:
            requests = WorkflowRequest.objects.filter(applicant=request.user)
        requests = (
            requests
            .select_related('category', 'applicant', 'approver')
            .prefetch_related('logs__actor')
            .order_by('-created_at')[:10]
        )
        return Response(WorkflowRequestSerializer(requests, many=True).data)


class WorkflowSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        mine = WorkflowRequest.objects.filter(applicant=request.user)
        if request.user.is_superuser:
            todo = WorkflowRequest.objects.filter(status=WorkflowRequest.STATUS_PENDING)
        else:
            todo = WorkflowRequest.objects.filter(approver=request.user, status=WorkflowRequest.STATUS_PENDING)

        return Response({
            'todo': todo.count(),
            'my_pending': mine.filter(status=WorkflowRequest.STATUS_PENDING).count(),
            'my_approved': mine.filter(status=WorkflowRequest.STATUS_APPROVED).count(),
            'my_rejected': mine.filter(status=WorkflowRequest.STATUS_REJECTED).count(),
            'total_visible': WorkflowRequest.objects.count() if request.user.is_superuser else mine.count(),
        })
