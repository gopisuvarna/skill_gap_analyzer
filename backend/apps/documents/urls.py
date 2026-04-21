from django.urls import path
from .views import ResumeUploadView, latest_resume_roles

urlpatterns = [
    path("", ResumeUploadView.as_view(), name="resume-upload"),
    path("latest-roles/", latest_resume_roles, name="latest-resume-roles"),
]