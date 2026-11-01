"""
models.py — Data model for AttendanceChimp.

AttendanceChimp is an electronic class attendance tool.  Instructors create
courses and lectures; each lecture is assigned a random QR code.  Students
photograph the QR code and upload the image.  The system decodes the QR code,
matches it to a lecture, and records the attendance.

Entities
--------
- CourseProfile   : extends Django User → instructor-specific data
- StudentProfile  : extends Django User → student-specific data
- Course          : a course taught by one instructor
- Enrollment      : junction table linking students to courses
- Lecture         : a single class meeting (has a QR-code identifier)
- QRCodeUpload    : a student's uploaded QR-code photograph
"""

from django.db import models
from django.contrib.auth.models import User

import logging
import string
import random

logger = logging.getLogger(__name__) # set up tracking, auditing, and debugging
                                                               # allows using logger.warning(), logger.error(), 
                                                               # logger.info(), etc. Better than print() for debuggin... 


# ---------------------------------------------------------------------------
# User profiles
# ---------------------------------------------------------------------------
class InstructorProfile(models.Model):
    """
    This saves the information of instructors from Django's user (1 to 1).
    Connects to Courses (1 to many) through instructorID.
    Automatically assigns each instructor with an instructor ID.
    """ 

    userID = models.OneToOneField(User, on_delete=models.CASCADE)
    instructorID = models.AutoField(primary_key=True)
    department = models.CharField(max_length=255)


class StudentProfile(models.Model):
    """
    This saves the information of students from Django's user (1 to 1).
    Connects to Enrollments and QRcodeUpload through studentID.
    Automatically assigns each student with a student ID.
    """

    userID = models.OneToOneField(User, on_delete=models.CASCADE)
    studentID = models.AutoField(primary_key=True)
    year = models.PositiveSmallIntegerField(null=True, blank=True)
    major = models.CharField(max_length=255, blank=True)

# ---------------------------------------------------------------------------
# Course
# ---------------------------------------------------------------------------
class Course(models.Model):
    """
    Saves info on a course, including the instructor, course name, start and
    end times (meetings times).
    Autogenerates an ID for courseID.
    """

    courseID = models.AutoField(primary_key = True)
    coursename = models.CharField(max_length=255)
    instructorID = models.ForeignKey(InstructorProfile, on_delete=models.PROTECT)
    meetingDays = models.CharField(max_length=50)
    startDate = models.DateField()
    endDate =  models.DateField()

# ---------------------------------------------------------------------------
# Enrollment
# ---------------------------------------------------------------------------
class Enrollment(models.Model):
    """
    Saves each studentID-courseID pair per enrollment.
    """

    courseID = models.ForeignKey(Course, on_delete=models.CASCADE)
    studentID = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)

# ---------------------------------------------------------------------------
# Lecture
# ---------------------------------------------------------------------------
class Lecture(models.Model):
    """
    Saves an individual lecture, saved with the course ID, date, and QRidentifier.
    """

    courseID = models.ForeignKey(Course, on_delete=models.CASCADE)
    lectureDate = models.DateField()
    QRidentifier = models.CharField(max_length=64, primary_key=True)

# ---------------------------------------------------------------------------
# QR Code Upload
# ---------------------------------------------------------------------------
class QRcodeUpload(models.Model):
    """
    Stores the QR codes uploaded by the student. lectureID is an optional input
    and can remain null.
    """

    QRidentifier = models.ForeignKey(Lecture, on_delete=models.CASCADE)
    studentID = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    QRcodeImage = models.ImageField(upload_to = 'qr_uploads/')
    submissionID = models.AutoField(primary_key=True)
    time = models.DateTimeField(auto_now_add=True)

# ---------------------------------------------------------------------------
# Helper / API functions
# ---------------------------------------------------------------------------



