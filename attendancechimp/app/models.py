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
from zoneinfo import ZoneInfo
from django.utils import timezone

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

    courseID = models.AutoField(primary_key =True)
    coursename = models.CharField(max_length=255, unique=True)
    instructorID = models.ForeignKey(InstructorProfile, on_delete=models.PROTECT)
    mon = models.BooleanField(default=False)
    tues = models.BooleanField(default=False)
    wed = models.BooleanField(default=False)
    thurs = models.BooleanField(default=False)
    fri = models.BooleanField(default=False)
    startTime = models.TimeField()
    endTime = models.TimeField()
    startDate = models.DateField(null=True, blank=True)
    endDate =  models.DateField(null=True, blank=True)

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
class QRCodeUpload(models.Model):
    """
    Stores the QR codes uploaded by the student. QRidentifier is an optional input
    and can remain null.
    """

    QRidentifier = models.ForeignKey(Lecture, on_delete=models.SET_NULL, null=True, blank=True)
    studentID = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    QRcodeImage = models.FileField(upload_to = 'qr_uploads/')
    submissionID = models.AutoField(primary_key=True)
    time = models.DateTimeField(auto_now_add=True)

# ---------------------------------------------------------------------------
# Helper / API functions
# ---------------------------------------------------------------------------
def is_instructor(user):
    """ Returns true is user is an instructor"""
    return (user.is_authenticated and InstructorProfile.objects.filter(userID=user).exists())

def is_student(user):
    """ Returns true is user is a student"""
    return (user.is_authenticated and StudentProfile.objects.filter(userID=user).exists())

def getUploadsForCourse(course):
    """
    Returns a list with valid QRCodeUploads or empty list if course doesn't exist
    input course is the unique Course.coursename
    """
    course_obj = Course.objects.filter(coursename=course).first()
    if course_obj is None:
        return []

    meets = [course_obj.mon, course_obj.tues, course_obj.wed,
             course_obj.thurs, course_obj.fri]

    valid = []
    uploads = QRCodeUpload.objects.filter(QRidentifier__courseID=course_obj)
    for upload in uploads:
        stamp = upload.time
        if timezone.is_aware(stamp):
            stamp = stamp.astimezone(CDT)
        day = stamp.weekday()  # 0 = Monday ... 6 = Sunday
        if (day < 5 and meets[day]
                and course_obj.startTime <= stamp.time() <= course_obj.endTime):
            valid.append(upload)
    return valid    

