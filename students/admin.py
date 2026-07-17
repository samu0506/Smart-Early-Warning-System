from django.contrib import admin
from django.contrib.auth.models import User
from django.db.models import Avg
from django import forms

from .models import (
    Student,
    Subject,
    SubjectAttendance,
    StudentMark,
    ExamType
)

# ==================================================
# ATTENDANCE VALIDATION FORM
# ==================================================
class SubjectAttendanceForm(forms.ModelForm):

    class Meta:
        model = SubjectAttendance
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        conducted = cleaned_data.get("lectures_conducted")
        attended = cleaned_data.get("lectures_attended")

        if conducted is not None and attended is not None:
            if attended > conducted:
                raise forms.ValidationError(
                    "Lectures attended cannot be greater than lectures conducted."
                )

        return cleaned_data


# ==================================================
# MARKS VALIDATION FORM
# ==================================================
class StudentMarkForm(forms.ModelForm):

    class Meta:
        model = StudentMark
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        total = cleaned_data.get("total_marks")
        obtained = cleaned_data.get("marks_obtained")

        if total is not None and obtained is not None:
            if obtained > total:
                raise forms.ValidationError(
                    "Marks obtained cannot be greater than total marks."
                )

        return cleaned_data


# ==================================================
# SUBJECT ATTENDANCE INLINE
# ==================================================
class SubjectAttendanceInline(admin.TabularInline):
    model = SubjectAttendance
    form = SubjectAttendanceForm
    extra = 1

    fields = (
        "subject",
        "lectures_conducted",
        "lectures_attended",
        "attendance_percentage",
    )

    readonly_fields = ("attendance_percentage",)

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):

        if db_field.name == "subject":

            student_id = request.resolver_match.kwargs.get("object_id")

            if student_id:
                student = Student.objects.get(id=student_id)

                kwargs["queryset"] = Subject.objects.filter(
                    department=student.department,
                    semester=student.semester
                )

            formfield = super().formfield_for_foreignkey(db_field, request, **kwargs)

            # REMOVE + VIEW + EDIT ICONS
            formfield.widget.can_add_related = False
            formfield.widget.can_change_related = False
            formfield.widget.can_view_related = False

            return formfield

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


# ==================================================
# STUDENT MARK INLINE
# ==================================================
class StudentMarkInline(admin.TabularInline):
    model = StudentMark
    form = StudentMarkForm
    extra = 1

    fields = (
        "subject",
        "exam",
        "marks_obtained",
        "total_marks",
        "percentage",
    )

    readonly_fields = ("percentage",)

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):

        if db_field.name == "subject":

            student_id = request.resolver_match.kwargs.get("object_id")

            if student_id:
                student = Student.objects.get(id=student_id)

                kwargs["queryset"] = Subject.objects.filter(
                    department=student.department,
                    semester=student.semester
                )

            formfield = super().formfield_for_foreignkey(db_field, request, **kwargs)

            # REMOVE + VIEW + EDIT ICONS
            formfield.widget.can_add_related = False
            formfield.widget.can_change_related = False
            formfield.widget.can_view_related = False

            return formfield

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


# ==================================================
# STUDENT ADMIN
# ==================================================
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):

    inlines = [SubjectAttendanceInline, StudentMarkInline]

    list_display = (
        "student_id",
        "full_name",
        "department",
        "year",
        "semester",
        "attendance_percentage",
        "get_average_marks",
        "risk_level",
    )

    readonly_fields = (
        "attendance_percentage",
        "risk_level",
    )

    fieldsets = (
        ("Student Information", {
            "fields": (
                "student_id",
                "full_name",
                "department",
                "year",
                "semester",
                "section",
            )
        }),

        ("Attendance Summary", {
            "fields": (
                "attendance_percentage",
            )
        }),

        ("Risk Analysis", {
            "fields": (
                "risk_level",
            )
        }),
    )

    # AUTO CREATE USER
    def save_model(self, request, obj, form, change):

        if not obj.user:
            user, created = User.objects.get_or_create(
                username=obj.student_id
            )

            if created:
                user.set_password("student123")
                user.save()

            obj.user = user

        super().save_model(request, obj, form, change)

    # CALCULATE AVERAGE MARKS
    def get_average_marks(self, obj):

        avg = StudentMark.objects.filter(student=obj).aggregate(
            Avg("percentage")
        )["percentage__avg"]

        return round(avg, 2) if avg else 0

    get_average_marks.short_description = "Average Marks (%)"


# ==================================================
# STUDENT MARK ADMIN
# ==================================================
@admin.register(StudentMark)
class StudentMarkAdmin(admin.ModelAdmin):

    list_display = (
        "student",
        "subject",
        "exam",
        "marks_obtained",
        "total_marks",
        "percentage",
    )

    list_filter = ("exam", "subject")

    search_fields = ("student__student_id",)


# ==================================================
# SUBJECT ADMIN
# ==================================================
@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):

    list_display = (
        "code",
        "name",
        "department",
        "semester",
        "pass_marks",
    )

    search_fields = (
        "code",
        "name",
    )


# ==================================================
# EXAM TYPE ADMIN
# ==================================================
@admin.register(ExamType)
class ExamTypeAdmin(admin.ModelAdmin):

    list_display = (
        "name",
    )