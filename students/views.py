from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.conf import settings
from django.db.models import Avg
import sys
import os
import json

from .models import Student, SubjectAttendance, StudentMark


# =====================================
# ML MODULE PATH CONFIG
# =====================================
BASE_DIR = settings.BASE_DIR
ML_DIR = os.path.join(BASE_DIR, "ml")

if ML_DIR not in sys.path:
    sys.path.append(ML_DIR)

try:
    from risk_prediction_model import predict_risk
except Exception:
    def predict_risk(**kwargs):
        return "LOW"


# =====================================
# REPORTLAB IMPORTS (PDF)
# =====================================
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import A4


# ==================================================
# LOGIN PAGE
# ==================================================
def student_login(request):

    if request.user.is_authenticated:
        if hasattr(request.user, "student_profile"):
            return redirect(
                "students:student_dashboard",
                student_id=request.user.student_profile.student_id
            )
        elif request.user.is_staff:
            return redirect("/admin/")

    if request.method == "POST":
        login_type = request.POST.get("login_type")
        username = request.POST.get("student_id") or request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if login_type == "student":
            if user and hasattr(user, "student_profile"):
                login(request, user)
                request.session.cycle_key()
                return redirect(
                    "students:student_dashboard",
                    student_id=user.student_profile.student_id
                )
            messages.error(request, "Invalid Student ID or Password")

        elif login_type == "admin":
            if user and user.is_staff:
                login(request, user)
                request.session.cycle_key()
                return redirect("/admin/")
            messages.error(request, "Invalid Admin Credentials")

    return render(request, "students/login.html")


# ==================================================
# FORGOT PASSWORD
# ==================================================
def simple_forgot_password(request):
    return render(request, "students/forgot_password.html")


# ==================================================
# STUDENT DASHBOARD
# ==================================================
@login_required(login_url="students:student_login")
def student_dashboard(request, student_id):

    student = get_object_or_404(Student, student_id=student_id)

    # Security Check
    if not request.user.is_staff:
        if not hasattr(request.user, "student_profile"):
            return redirect("students:student_login")

        if request.user.student_profile.student_id != student_id:
            return redirect(
                "students:student_dashboard",
                student_id=request.user.student_profile.student_id
            )

    # ================= OVERALL ATTENDANCE =================
    attendance = float(student.attendance_percentage or 0)
    remaining = round(max(0, 100 - attendance), 2)

    # ================= SUBJECT-WISE ATTENDANCE =================
    subject_attendance_qs = SubjectAttendance.objects.filter(student=student)

    subject_attendance_data = []
    subject_labels = []
    subject_data = []

    for record in subject_attendance_qs:
        percentage = float(record.attendance_percentage or 0)

        subject_attendance_data.append({
            "subject": record.subject.name,
            "lectures_conducted": record.lectures_conducted,
            "lectures_attended": record.lectures_attended,
            "percentage": percentage
        })

        subject_labels.append(record.subject.name)
        subject_data.append(percentage)

    # ================= MARKS =================
    marks_qs = StudentMark.objects.filter(student=student)

    subjects = []
    failed_subjects = []
    weak_subjects = []
    chart_labels = []
    chart_data = []
    class_avg_data = []

    for mark in marks_qs:
        percentage = float(mark.percentage or 0)

        obj = {
            "name": mark.subject.name,
            "exam": mark.exam.name,
            "obtained": mark.marks_obtained,
            "total": mark.total_marks,
            "percentage": percentage
        }

        subjects.append(obj)

        label = f"{mark.subject.name} ({mark.exam.name})"
        chart_labels.append(label)
        chart_data.append(percentage)

        # 🔥 CLASS AVERAGE CALCULATION
        class_avg = StudentMark.objects.filter(
            subject=mark.subject,
            exam=mark.exam
        ).aggregate(Avg("percentage"))["percentage__avg"] or 0

        class_avg_data.append(round(float(class_avg), 2))

        if percentage < 30:
            failed_subjects.append(obj)
        elif percentage < 40:
            weak_subjects.append(obj)

    # ================= WEAKEST SUBJECT =================
    weakest_subject = min(subjects, key=lambda x: x["percentage"]) if subjects else None

    # ================= AVERAGE MARKS =================
    avg_marks = marks_qs.aggregate(Avg("percentage"))["percentage__avg"]
    avg_marks = round(avg_marks, 2) if avg_marks else 0

    # ================= ML Prediction =================
    try:
        predicted_risk = str(predict_risk(
            attendance=attendance,
            avg_marks=avg_marks,
            failed_subjects=len(failed_subjects),
            weak_subjects=len(weak_subjects)
        ))
    except Exception:
        predicted_risk = "LOW"

    if predicted_risk == "HIGH":
        remarks = [
            "Student is at HIGH academic risk",
            "Low attendance or failed subjects detected",
            "Immediate intervention required",
            "Counseling recommended"
        ]
    elif predicted_risk == "MEDIUM":
        remarks = [
            "Average performance",
            "Needs improvement in some subjects",
            "Regular monitoring advised"
        ]
    else:
        remarks = [
            "Good performance",
            "Attendance and academics stable"
        ]

    return render(request, "students/dashboard.html", {
        "student": student,
        "attendance": attendance,
        "remaining": remaining,

        # Attendance
        "subject_attendance": subject_attendance_data,
        "subject_labels": json.dumps(subject_labels),
        "subject_data": json.dumps(subject_data),

        # Marks
        "subjects": subjects,
        "failed_subjects": failed_subjects,
        "weak_subjects": weak_subjects,
        "average_marks": avg_marks,
        "risk_level": predicted_risk,

        # Charts
        "chart_labels": json.dumps(chart_labels),
        "chart_data": json.dumps(chart_data),
        "class_avg_data": json.dumps(class_avg_data),

        # Extra Insights
        "weakest_subject": weakest_subject,
        "remarks": remarks,
    })

# ==================================================
# EXPORT PDF
# ==================================================
@login_required(login_url="students:student_login")
def export_pdf(request, student_id):

    student = get_object_or_404(Student, student_id=student_id)

    if not request.user.is_staff:
        if not hasattr(request.user, "student_profile") or \
           request.user.student_profile.student_id != student_id:
            return redirect("students:student_login")

    marks_qs = StudentMark.objects.filter(student=student)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{student.student_id}_Report.pdf"'

    doc = SimpleDocTemplate(response, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    # ================= TITLE =================
    elements.append(Paragraph("SMART EWS - STUDENT PERFORMANCE REPORT", styles["Heading1"]))
    elements.append(Spacer(1, 20))

    # ================= STUDENT INFO =================
    elements.append(Paragraph(f"Name: {student.full_name}", styles["Normal"]))
    elements.append(Paragraph(f"Student ID: {student.student_id}", styles["Normal"]))
    elements.append(Paragraph(f"Department: {student.department}", styles["Normal"]))
    elements.append(Paragraph(f"Year: {student.year}", styles["Normal"]))
    elements.append(Spacer(1, 15))

    elements.append(Paragraph(f"Attendance: {student.attendance_percentage}%", styles["Normal"]))
    elements.append(Spacer(1, 20))

    # ================= MARKS TABLE =================
    data = [["Subject", "Exam", "Obtained", "Total", "Percentage"]]

    subject_percentages = []

    for mark in marks_qs:
        percentage = float(mark.percentage or 0)

        subject_percentages.append({
            "subject": mark.subject.name,
            "exam": mark.exam.name,
            "percentage": percentage
        })

        data.append([
            mark.subject.name,
            mark.exam.name,
            mark.marks_obtained,
            mark.total_marks,
            f"{percentage}%"
        ])

    table = Table(data, colWidths=[1.2 * inch] * 5)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ALIGN', (2, 1), (-1, -1), 'CENTER'),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 25))

    # ================= PERFORMANCE ANALYSIS =================
    elements.append(Paragraph("Performance Analysis", styles["Heading2"]))
    elements.append(Spacer(1, 10))

    avg_marks = 0
    if subject_percentages:
        avg_marks = sum([s["percentage"] for s in subject_percentages]) / len(subject_percentages)

    weakest_subject = min(subject_percentages, key=lambda x: x["percentage"]) if subject_percentages else None

    if weakest_subject:
        elements.append(Paragraph(
            f"Weakest Subject: {weakest_subject['subject']} ({weakest_subject['exam']}) - {weakest_subject['percentage']}%",
            styles["Normal"]
        ))

    elements.append(Paragraph(f"Average Marks: {round(avg_marks,2)}%", styles["Normal"]))
    elements.append(Spacer(1, 15))

    # ================= STUDY TIMETABLE =================
    elements.append(Paragraph("Suggested Study Timetable", styles["Heading2"]))
    elements.append(Spacer(1, 10))

    timetable_data = [["Subject", "Current %", "Suggested Study Time"]]

    for sub in subject_percentages:

        if sub["percentage"] < 60:
            hours = "3 hours/day"
        elif sub["percentage"] < 75:
            hours = "2 hours/day"
        else:
            hours = "1 hour/day (revision)"

        timetable_data.append([
            f"{sub['subject']} ({sub['exam']})",
            f"{sub['percentage']}%",
            hours
        ])

    timetable_table = Table(timetable_data, colWidths=[2 * inch, 1.5 * inch, 2 * inch])
    timetable_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
    ]))

    elements.append(timetable_table)
    elements.append(Spacer(1, 20))

    # ================= RECOMMENDATIONS =================
    elements.append(Paragraph("Recommendations", styles["Heading2"]))
    elements.append(Spacer(1, 10))

    recommendations = [
        "Focus more on weak subjects.",
        "Solve previous year question papers.",
        "Maintain regular attendance.",
        "Follow the suggested study timetable for better performance."
    ]

    for r in recommendations:
        elements.append(Paragraph(f"- {r}", styles["Normal"]))

    elements.append(Spacer(1, 20))

    # ================= PERFORMANCE RATING =================
    elements.append(Paragraph("Overall Performance Rating", styles["Heading2"]))
    elements.append(Spacer(1, 10))

    if avg_marks >= 90:
        rating = "Excellent ⭐⭐⭐⭐⭐"
    elif avg_marks >= 75:
        rating = "Good ⭐⭐⭐⭐"
    elif avg_marks >= 60:
        rating = "Average ⭐⭐⭐"
    else:
        rating = "Needs Improvement ⭐⭐"

    elements.append(Paragraph(rating, styles["Normal"]))

    # ================= BUILD PDF =================
    doc.build(elements)

    return response

# ==================================================
# LOGOUT
# ==================================================
def user_logout(request):
    logout(request)
    request.session.flush()
    return redirect("students:student_login")