from django.urls import path

from .views import (
    WorkflowApproveView,
    WorkflowCategoryView,
    WorkflowRejectView,
    WorkflowRequestDetailView,
    WorkflowRequestLogsView,
    WorkflowRequestView,
    WorkflowSummaryView,
    WorkflowWithdrawView,
)

urlpatterns = [
    path('categories', WorkflowCategoryView.as_view()),
    path('requests', WorkflowRequestView.as_view()),
    path('requests/<int:pk>', WorkflowRequestDetailView.as_view()),
    path('requests/<int:pk>/logs', WorkflowRequestLogsView.as_view()),
    path('requests/<int:pk>/approve', WorkflowApproveView.as_view()),
    path('requests/<int:pk>/reject', WorkflowRejectView.as_view()),
    path('requests/<int:pk>/withdraw', WorkflowWithdrawView.as_view()),
    path('summary', WorkflowSummaryView.as_view()),
]
