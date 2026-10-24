'''
LLM used: ChatGPT
Intentional "mistake": I did not tell it the split users into instructors and students hint to see what it would do.

Prompt:
I'm trying to make a relational database with the following functions. Figure out the ER diagram and write the program for the models.py file on Django.

Here's some background information:
AttendanceChimp tracks class attendance via QR codes:
• Users: students and instructors (two roles).
• Courses: each has one instructor. Students can enroll in multiple courses.
• Lectures: individual class meetings, each associated with a course.
• QR Code Uploads: photos uploaded by students, each associated with a student and a lecture.
Design requirements: simple to use, supports attendance analytics, robust to cheating.

Attributes:
• A way to save the profiles of the users
• Course table with at least name, instructor, meeting schedule
• Enrollment table: links students to courses (many-to-many)
• Lecture table: linked to a course, has a date and a QR identifier
• QRCodeUpload table: linked to a student and (optionally) a lecture
'''

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.conf import settings


# 1. USER
class User(AbstractUser):
    class Role(models.TextChoices):
        STUDENT = "student", "Student"
        INSTRUCTOR = "instructor", "Instructor"

    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.STUDENT
    )

    def __str__(self):
        return f"{self.username} ({self.role})"


# 2. COURSE
class Course(models.Model):
    name = models.CharField(max_length=200)

    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="courses_taught"
    )

    meeting_schedule = models.CharField(max_length=200)

    students = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="Enrollment",
        related_name="enrolled_courses",
        blank=True
    )

    def clean(self):
        super().clean()
        if self.instructor_id and self.instructor.role != User.Role.INSTRUCTOR:
            raise ValidationError({
                "instructor": "The instructor must have the instructor role."
            })

    def __str__(self):
        return self.name


# 3. ENROLLMENT
class Enrollment(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="enrollments"
    )

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="enrollments"
    )

    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["student", "course"],
                name="unique_student_course"
            )
        ]

    def clean(self):
        super().clean()
        if self.student_id and self.student.role != User.Role.STUDENT:
            raise ValidationError({
                "student": "Only students can enroll."
            })

    def __str__(self):
        return f"{self.student.username} - {self.course.name}"


# 4. LECTURE
class Lecture(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="lectures"
    )

    date = models.DateField()

    qr_identifier = models.CharField(
        max_length=100,
        unique=True
    )

    qr_expires_at = models.DateTimeField(
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.course.name} - {self.date}"


# 5. QR CODE UPLOAD
class QRCodeUpload(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        VERIFIED = "verified", "Verified"
        REJECTED = "rejected", "Rejected"

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="qr_uploads"
    )

    lecture = models.ForeignKey(
        Lecture,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="qr_uploads"
    )

    image = models.ImageField(
        upload_to="qr_uploads/"
    )

    submitted_at = models.DateTimeField(auto_now_add=True)

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["student", "lecture"],
                name="unique_student_lecture_upload"
            )
        ]

    def clean(self):
        super().clean()

        if self.student_id and self.student.role != User.Role.STUDENT:
            raise ValidationError({
                "student": "Only students can submit QR uploads."
            })

        if self.student_id and self.lecture_id:
            if not Enrollment.objects.filter(
                student_id=self.student_id,
                course_id=self.lecture.course_id
            ).exists():
                raise ValidationError(
                    "Student must be enrolled in the lecture's course."
                )

    def __str__(self):
        lecture_name = str(self.lecture) if self.lecture else "Unassigned"
        return f"{self.student.username} - {lecture_name}"
