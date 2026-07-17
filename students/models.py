from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


# =====================================================
# SUBJECT MASTER
# =====================================================
class Subject(models.Model):

    DEPARTMENT_CHOICES = [
        ("CS", "Computer Science"),
        ("IT", "Information Technology"),
    ]

    SEMESTER_CHOICES = [
        (1, "Sem 1"),
        (2, "Sem 2"),
        (3, "Sem 3"),
        (4, "Sem 4"),
        (5, "Sem 5"),
        (6, "Sem 6"),
        (7, "Sem 7"),
        (8, "Sem 8"),
    ]

    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)

    department = models.CharField(
        max_length=10,
        choices=DEPARTMENT_CHOICES
    )

    semester = models.IntegerField(
        choices=SEMESTER_CHOICES
    )

    total_marks = models.PositiveIntegerField(default=100)

    def pass_marks(self):
        return int(self.total_marks * 0.30)

    def __str__(self):
        return f"{self.code} - {self.name} ({self.department} Sem {self.semester})"


# =====================================================
# EXAM TYPE
# =====================================================
class ExamType(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


# =====================================================
# STUDENT MODEL
# =====================================================
class Student(models.Model):

    YEAR_CHOICES = [
        (1, "1st Year"),
        (2, "2nd Year"),
        (3, "3rd Year"),
        (4, "4th Year"),
    ]

    SEMESTER_CHOICES = [
        (1, "Sem 1"),
        (2, "Sem 2"),
        (3, "Sem 3"),
        (4, "Sem 4"),
        (5, "Sem 5"),
        (6, "Sem 6"),
        (7, "Sem 7"),
        (8, "Sem 8"),
    ]

    DEPARTMENT_CHOICES = [
        ("CS", "Computer Science"),
        ("IT", "Information Technology"),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="student_profile",
        null=True,
        blank=True
    )

    student_id = models.CharField(max_length=20, unique=True)
    full_name = models.CharField(max_length=100)

    department = models.CharField(
        max_length=10,
        choices=DEPARTMENT_CHOICES,
        default="CS"
    )

    year = models.IntegerField(choices=YEAR_CHOICES)
    semester = models.IntegerField(choices=SEMESTER_CHOICES)

    section = models.CharField(max_length=1)

    attendance_percentage = models.FloatField(default=0.0)
    average_marks = models.FloatField(default=0.0)
    predicted_cgpa = models.FloatField(default=0.0)
    risk_level = models.CharField(max_length=10, default="LOW")

    # =====================================================
    # VALIDATION
    # =====================================================
    def clean(self):

        # Year ↔ Semester validation
        valid_semesters = {
            1: [1, 2],
            2: [3, 4],
            3: [5, 6],
            4: [7, 8]
        }

        if self.year in valid_semesters:
            if self.semester not in valid_semesters[self.year]:
                raise ValidationError(
                    f"Year {self.year} students must select semester {valid_semesters[self.year]}"
                )

        # 🔴 CS Department only 6 semesters
        if self.department == "CS" and self.semester > 6:
            raise ValidationError(
                "Computer Science department has only 6 semesters."
            )

    # ------------------------------------------------
    # CALCULATIONS
    # ------------------------------------------------
    def calculate_average_marks(self):
        marks = self.marks.all()
        percentages = []

        for mark in marks:
            if mark.total_marks > 0:
                percentages.append((mark.marks_obtained / mark.total_marks) * 100)

        return round(sum(percentages) / len(percentages), 2) if percentages else 0.0

    def calculate_attendance_percentage(self):
        records = self.attendance_records.all()
        total_conducted = sum(r.lectures_conducted for r in records)
        total_attended = sum(r.lectures_attended for r in records)

        if total_conducted == 0:
            return 0.0

        return round((total_attended / total_conducted) * 100, 2)

    def calculate_risk_level(self):
        if self.attendance_percentage < 60 or self.average_marks < 40:
            return "HIGH"
        elif self.attendance_percentage < 75 or self.average_marks < 55:
            return "MEDIUM"
        return "LOW"

    # ------------------------------------------------
    # DETECT WEAK SUBJECTS
    # ------------------------------------------------
    def get_weak_subjects(self):
        weak_subjects = []

        for mark in self.marks.all():
            if mark.percentage < 60:
                weak_subjects.append({
                    "subject": mark.subject.name,
                    "exam": mark.exam.name,
                    "percentage": mark.percentage
                })

        return weak_subjects

    def save(self, *args, **kwargs):

        self.full_clean()

        super().save(*args, **kwargs)

        self.average_marks = self.calculate_average_marks()
        self.predicted_cgpa = round((self.average_marks / 100) * 10, 2)
        self.attendance_percentage = self.calculate_attendance_percentage()
        self.risk_level = self.calculate_risk_level()

        super().save(update_fields=[
            "average_marks",
            "predicted_cgpa",
            "attendance_percentage",
            "risk_level"
        ])

    def __str__(self):
        return f"{self.student_id} - {self.full_name}"


# =====================================================
# STUDENT MARKS
# =====================================================
class StudentMark(models.Model):

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="marks"
    )

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE
    )

    exam = models.ForeignKey(
        ExamType,
        on_delete=models.CASCADE
    )

    marks_obtained = models.FloatField()
    total_marks = models.FloatField()

    percentage = models.FloatField(default=0.0)

    class Meta:
        unique_together = ("student", "subject", "exam")

    def save(self, *args, **kwargs):
        if self.total_marks > 0:
            self.percentage = round(
                (self.marks_obtained / self.total_marks) * 100, 2
            )
        else:
            self.percentage = 0.0

        super().save(*args, **kwargs)

        if self.student and self.student.pk:
            self.student.save()

    def __str__(self):
        return f"{self.student} | {self.subject} | {self.exam}"


# =====================================================
# SUBJECT ATTENDANCE
# =====================================================
class SubjectAttendance(models.Model):

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="attendance_records"
    )

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE
    )

    lectures_conducted = models.PositiveIntegerField(default=0)
    lectures_attended = models.PositiveIntegerField(default=0)
    attendance_percentage = models.FloatField(default=0.0)

    class Meta:
        unique_together = ("student", "subject")

    def clean(self):
        if self.lectures_attended > self.lectures_conducted:
            raise ValidationError(
                "Lectures attended cannot be greater than lectures conducted."
            )

    def save(self, *args, **kwargs):

        self.full_clean()

        if self.lectures_conducted == 0:
            self.attendance_percentage = 0.0
        else:
            self.attendance_percentage = round(
                (self.lectures_attended / self.lectures_conducted) * 100, 2
            )

        super().save(*args, **kwargs)

        if self.student and self.student.pk:
            self.student.save()

    def __str__(self):
        return f"{self.student} | {self.subject}"