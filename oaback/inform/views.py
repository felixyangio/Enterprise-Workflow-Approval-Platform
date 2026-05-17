from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from django.db.models import Q

from .models import Inform, InformRead
from .serializers import InformSerializer, PublishInformSerializer

import os
import uuid
from django.conf import settings
from django.core.files.storage import default_storage


class InformView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        page = max(int(request.query_params.get('page', 1)), 1)
        size = min(max(int(request.query_params.get('size', 10)), 1), 100)
        queryset = (
            Inform.objects
            .select_related('author')
            .prefetch_related('departments', 'read_records')
            .order_by('-is_top', '-create_time', '-id')
        )
        if not request.user.is_superuser:
            # Show only: public notifications OR notifications targeted at user's department
            try:
                user_dept = request.user.staff_profile.department
            except Exception:
                user_dept = None
            if user_dept:
                queryset = queryset.filter(
                    Q(departments__isnull=True) | Q(departments=user_dept)
                ).distinct()
            else:
                queryset = queryset.filter(departments__isnull=True)

        keyword = request.query_params.get('keyword') or request.query_params.get('title')
        if keyword:
            queryset = queryset.filter(
                Q(title__icontains=keyword)
                | Q(content__icontains=keyword)
                | Q(author__realname__icontains=keyword)
                | Q(author__email__icontains=keyword)
            ).distinct()

        read_filter = request.query_params.get('read')
        if read_filter in ('read', 'true', '1'):
            queryset = queryset.filter(read_records__reader=request.user).distinct()
        elif read_filter in ('unread', 'false', '0'):
            queryset = queryset.exclude(read_records__reader=request.user)

        total = queryset.count()
        start = (page - 1) * size
        items = queryset[start:start + size]
        serializer = InformSerializer(items, many=True, context={'request': request})
        return Response({'total': total, 'page': page, 'size': size, 'items': serializer.data})

    def post(self, request):
        serializer = PublishInformSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        dept_ids = [d for d in data.get('department_ids', []) if d != 0]
        # Non-superusers can only target their own department or All
        if not request.user.is_superuser and dept_ids:
            try:
                user_dept_id = request.user.staff_profile.department_id
            except Exception:
                user_dept_id = None
            if user_dept_id is None or any(d != user_dept_id for d in dept_ids):
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied('You can only publish to your own department or All Departments.')
        inform = Inform.objects.create(
            title=data['title'],
            content=data['content'],
            is_top=data.get('is_top', False),
            author=request.user,
        )
        if dept_ids:
            from staff.models import Department
            depts = Department.objects.filter(id__in=dept_ids)
            inform.departments.set(depts)
        return Response(InformSerializer(inform, context={'request': request}).data,
                        status=status.HTTP_201_CREATED)


class InformDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            inform = Inform.objects.get(pk=pk)
        except Inform.DoesNotExist:
            return Response({'detail': 'Announcement not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(InformSerializer(inform, context={'request': request}).data)

    def delete(self, request, pk):
        if request.user.is_superuser:
            try:
                inform = Inform.objects.get(pk=pk)
            except Inform.DoesNotExist:
                return Response({'detail': 'Announcement not found'}, status=status.HTTP_404_NOT_FOUND)
        else:
            try:
                inform = Inform.objects.get(pk=pk, author=request.user)
            except Inform.DoesNotExist:
                return Response({'detail': 'Announcement not found or forbidden'}, status=status.HTTP_404_NOT_FOUND)
        inform.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class InformReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        inform_pk = request.data.get('inform_pk')
        try:
            inform = Inform.objects.get(pk=inform_pk)
        except Inform.DoesNotExist:
            return Response({'detail': 'Announcement not found'}, status=status.HTTP_404_NOT_FOUND)
        InformRead.objects.get_or_create(inform=inform, reader=request.user)
        return Response({'detail': 'Marked as read'})


class ImageUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        file = request.FILES.get('image')
        if not file:
            return Response({'errno': 1, 'message': 'No image provided'}, status=status.HTTP_400_BAD_REQUEST)
        if file.size > 25 * 1024 * 1024:
            return Response({'errno': 1, 'message': 'File size exceeds 25MB'}, status=status.HTTP_400_BAD_REQUEST)
        ext = os.path.splitext(file.name)[1].lower()
        filename = f'images/{uuid.uuid4().hex}{ext}'
        saved_path = default_storage.save(filename, file)
        url = settings.MEDIA_URL + saved_path
        return Response({
            'errno': 0,
            'data': [{'url': url, 'alt': file.name, 'href': url}]
        })


class FileUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        file = request.FILES.get('file')
        if not file:
            return Response({'errno': 1, 'message': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        if file.size > 25 * 1024 * 1024:
            return Response({'errno': 1, 'message': 'File size exceeds 25MB'}, status=status.HTTP_400_BAD_REQUEST)
        ext = os.path.splitext(file.name)[1].lower()
        filename = f'attachments/{uuid.uuid4().hex}{ext}'
        saved_path = default_storage.save(filename, file)
        url = settings.MEDIA_URL + saved_path
        return Response({
            'errno': 0,
            'data': {'url': url, 'name': file.name}
        })
