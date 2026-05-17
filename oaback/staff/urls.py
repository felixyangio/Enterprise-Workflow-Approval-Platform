from django.urls import path
from .views import DepartmentView, StaffDownloadView, StaffView, StaffDetailView

urlpatterns = [
    path('departments', DepartmentView.as_view()),
    path('download', StaffDownloadView.as_view()),
    path('staff', StaffView.as_view()),
    path('staff/<int:staff_id>', StaffDetailView.as_view()),
]
