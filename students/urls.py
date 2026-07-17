from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views

app_name = "students"

urlpatterns = [

    # ==========================================
    # AUTHENTICATION
    # ==========================================

    # Login
    path(
        "",
        views.student_login,
        name="student_login"
    ),

    # Logout
    path(
        "logout/",
        views.user_logout,
        name="logout"
    ),

    # Forgot Password (Simple Page)
    path(
        "forgot-password/",
        views.simple_forgot_password,
        name="simple_forgot_password"
    ),

    # Change Password
    path(
        "change-password/",
        auth_views.PasswordChangeView.as_view(
            template_name="students/change_password.html",
            success_url=reverse_lazy("students:password_change_done"),
        ),
        name="change_password",
    ),

    path(
        "change-password-done/",
        auth_views.PasswordChangeDoneView.as_view(
            template_name="students/change_password_done.html",
        ),
        name="password_change_done",
    ),

    # ==========================================
    # STUDENT AREA
    # ==========================================

    # Dashboard
    path(
        "student/<str:student_id>/",
        views.student_dashboard,
        name="student_dashboard",
    ),

    # Export PDF
    path(
        "student/<str:student_id>/export-pdf/",
        views.export_pdf,
        name="export_pdf",
    ),
]