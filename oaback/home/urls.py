from django.urls import path
from .views import DepartmentStaffCountView, LatestInformView, LatestAbsentView, WorkflowSummaryView

urlpatterns = [
    path('department/staff/count', DepartmentStaffCountView.as_view()),
    path('latest/inform', LatestInformView.as_view()),
    path('latest/absent', LatestAbsentView.as_view()),
    path('latest/workflow', LatestAbsentView.as_view()),
    path('workflow/summary', WorkflowSummaryView.as_view()),
]
