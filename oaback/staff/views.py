import csv
import json

from django.http import HttpResponse
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from datetime import date

from .models import Department, Staff
from .serializers import DepartmentSerializer, StaffSerializer, AddStaffSerializer


class DepartmentView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        departments = Department.objects.all()
        serializer = DepartmentSerializer(departments, many=True)
        return Response(serializer.data)


class StaffView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        page = int(request.query_params.get('page', 1))
        size = int(request.query_params.get('size', 10))
        queryset = Staff.objects.select_related('user', 'department').all()
        # Filter params
        keyword = request.query_params.get('realname') or request.query_params.get('keyword')
        if keyword:
            queryset = queryset.filter(user__realname__icontains=keyword)
        dept_id = request.query_params.get('department_id') or request.query_params.get('department')
        if dept_id:
            queryset = queryset.filter(department_id=dept_id)
        status_val = request.query_params.get('status')
        if status_val is not None and status_val != '':
            queryset = queryset.filter(status=status_val)
        date_start = request.query_params.get('date_joined_0') or request.query_params.get('date_joined[0]')
        date_end = request.query_params.get('date_joined_1') or request.query_params.get('date_joined[1]')
        if not date_start:
            date_list = request.query_params.getlist('date_joined[]') or request.query_params.getlist('date_joined')
            if len(date_list) >= 2:
                date_start, date_end = date_list[0], date_list[1]
            elif len(date_list) == 1:
                date_start = date_list[0]
        if date_start:
            queryset = queryset.filter(join_date__gte=date_start)
        if date_end:
            queryset = queryset.filter(join_date__lte=date_end)
        total = queryset.count()
        start = (page - 1) * size
        staffs = queryset[start:start + size]
        serializer = StaffSerializer(staffs, many=True)
        return Response({'total': total, 'page': page, 'items': serializer.data})

    def post(self, request):
        if not request.user.is_superuser:
            return Response({'detail': 'Permission denied. Only superusers can add employees.'}, status=status.HTTP_403_FORBIDDEN)
        serializer = AddStaffSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        from authapp.models import User
        user = User.objects.create_user(
            email=data['email'],
            password=data['password'],
            realname=data['realname'],
        )
        staff = Staff.objects.create(user=user, department=data.get('department'), join_date=date.today())
        return Response(StaffSerializer(staff).data, status=status.HTTP_201_CREATED)


class StaffDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, staff_id):
        if not request.user.is_superuser:
            return Response({'detail': 'Permission denied. Only superusers can update employee status.'}, status=status.HTTP_403_FORBIDDEN)
        try:
            staff = Staff.objects.get(pk=staff_id)
        except Staff.DoesNotExist:
            return Response({'detail': 'Staff not found'}, status=status.HTTP_404_NOT_FOUND)
        new_status = request.data.get('status')
        if new_status is not None:
            staff.status = new_status
            staff.save()
        return Response(StaffSerializer(staff).data)

    def delete(self, request, staff_id):
        if not request.user.is_superuser:
            return Response({'detail': 'Permission denied. Only superusers can delete employees.'}, status=status.HTTP_403_FORBIDDEN)
        try:
            staff = Staff.objects.get(pk=staff_id)
        except Staff.DoesNotExist:
            return Response({'detail': 'Staff not found'}, status=status.HTTP_404_NOT_FOUND)
        staff.user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class StaffDownloadView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_superuser:
            return Response({'detail': 'Permission denied. Only superusers can export employees.'}, status=status.HTTP_403_FORBIDDEN)

        queryset = Staff.objects.select_related('user', 'department').all().order_by('id')
        raw_pks = request.query_params.get('pks')
        if raw_pks:
            try:
                pks = json.loads(raw_pks)
            except json.JSONDecodeError:
                pks = [pk for pk in raw_pks.split(',') if pk]
            queryset = queryset.filter(pk__in=pks)

        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="employees.csv"'
        writer = csv.writer(response)
        writer.writerow(['Name', 'Email', 'Department', 'Status', 'Join Date'])
        status_labels = dict(Staff.STATUS_CHOICES)
        for staff in queryset:
            writer.writerow([
                staff.user.realname,
                staff.user.email,
                staff.department.name if staff.department else '',
                status_labels.get(staff.status, staff.status),
                staff.join_date.isoformat() if staff.join_date else '',
            ])
        return response
