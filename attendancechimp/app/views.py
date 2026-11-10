"""
views.py — HTTP request handlers for AttendanceChimp.

Each view corresponds to one URL endpoint.  Views receive an HTTP request,
interact with the database via models.py, and return an HTTP response.
"""

from django.shortcuts import render, redirect
from django.http import (HttpResponse, HttpResponseForbidden,
                         HttpResponseBadRequest, JsonResponse)
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from datetime import datetime
from zoneinfo import ZoneInfo
import json
import io

from .models import (InstructorProfile, StudentProfile, Course, Lecture, QRCodeUpload)
import secrets
from django.utils.dateparse import parse_time

# from .models import (InstructorProfile, StudentProfile, Course, Enrollment,
#                      Lecture, QRCodeUpload, is_instructor, is_student,
#                      getUploadsForCourse)

CDT = ZoneInfo("America/Chicago")


# ---------------------------------------------------------------------------
# HW2  — index, time, sum
# ---------------------------------------------------------------------------

def index(request):
    """
    Render the home page (index.html).
    Pass current time to HW4 (app/templates/app/index.html)
    """

    now = datetime.now(ZoneInfo('America/Chicago'))
    if request.user.is_authenticated:
        user_name = request.user.get_full_name() or request.user.username
    else:
        user_name = None

    context = {
        'current_time': now.strftime('%H:%M'),
        'user_name': user_name,
    }

    return render(request, 'app/index.html', context)

# ---------------------------------------------------------------------------
# HW4  — user creation
# ---------------------------------------------------------------------------
@require_GET
def new(request):
    """
    Display the sign-up form (new.html).

    Accepts GET requests. POST returns an error
    Submits to /app/createUser.
    """
    return render(request, 'app/new.html')

@csrf_exempt
@require_POST
def createUser(request):
    """
    Create a new user account (API endpoint for /app/createUser).

    Accepts only POST requests. Reads email, user_name, password and is_student from the POST data.
    Otherwise creates a Django User plus a StudentProfile (if student exists) or an InstructorProfile,
    Signs the user in, and returns HTTP 200 with a JSON success message.

    csrf_exempt, only accepts POST requests
    """

    email = request.POST.get('email', '').strip()
    user_name = request.POST.get('user_name', '').strip()
    password = request.POST.get('password', '')
    is_student = request.POST.get('is_student', '').lower() in ('1', 'true')

    if not (email and user_name and password):
        return HttpResponseBadRequest('Missing email, user_name or password')
    if User.objects.filter(email=email).exists():
        return HttpResponseBadRequest('Email already registered')
    if User.objects.filter(username=user_name).exists():
        return HttpResponseBadRequest('User name already taken')

    user = User.objects.create_user(
        username=user_name, email=email, password=password)
    if is_student:
        StudentProfile.objects.create(userID=user)
    else:
        InstructorProfile.objects.create(userID=user)

    login(request, user)
    return JsonResponse({'status': 'ok', 'user_name': user_name,
                         'is_student': is_student})

# ---------------------------------------------------------------------------
# HW5  — courses, lectures, QR uploads, dump
# ---------------------------------------------------------------------------

DAY_FIELDS = [('day-mon', 'Mon'), ('day-tue', 'Tue'), ('day-wed', 'Wed'),
              ('day-thu', 'Thu'), ('day-fri', 'Fri')]


def is_instructor(user):
    """Return True if `user` is logged in and has an InstructorProfile."""
    return (user.is_authenticated
            and InstructorProfile.objects.filter(userID=user).exists())


def is_student(user):
    """Return True if `user` is logged in and has a StudentProfile."""
    return (user.is_authenticated
            and StudentProfile.objects.filter(userID=user).exists())


def unauthorized():
    """Return the standard HTTP 401 response."""
    return HttpResponse('Unauthorized', status=401)


def parse_time_or_none(value):
    """Parse 'HH:MM' (or 'HH:MM:SS') into a time; return None if invalid."""
    try:
        return parse_time(value)
    except ValueError:
        return None


@require_GET
def new_course(request):
    """Display the course-creation form (new_course.html)."""
    return render(request, 'app/new_course.html')


@require_GET
def new_lecture(request):
    """Display the lecture form with a dropdown of existing courses."""
    return render(request, 'app/new_lecture.html',
                  {'courses': Course.objects.all()})


@require_GET
def new_qr_upload(request):
    """Display the QR-code upload form (new_qr_upload.html)."""
    return render(request, 'app/new_qr_upload.html')


@csrf_exempt
@require_POST
def createCourse(request):
    """
    Creates a Course (POST, instructors only).

    Reads course-name, start-time, end-time and any of day-mon..day-fri from
    the POST. Returns 401 if user is not an instructor, 400 if data is missing or 
    invalid, and 200 if a duplicate course name is used.
    """
    if not is_instructor(request.user):
        return unauthorized()

    name = request.POST.get('course-name', '').strip()
    start = parse_time_or_none(request.POST.get('start-time', ''))
    end = parse_time_or_none(request.POST.get('end-time', ''))
    if not name or start is None or end is None:
        return HttpResponseBadRequest('Need course-name, start-time, end-time')

    days = [label for key, label in DAY_FIELDS if key in request.POST]
    instructor = InstructorProfile.objects.get(userID=request.user)
    course, created = Course.objects.get_or_create(
        coursename=name,
        defaults={'instructorID': instructor, 'meetingDays': ','.join(days),
                  'startTime': start, 'endTime': end})
    return JsonResponse({'course': course.coursename, 'created': created})


@csrf_exempt
@require_POST
def createLecture(request):
    """
    Creates a Lecture for a course (POST, instructors only).

    Reads the course name. Returns 401 unless user is an instructor, and 
    400 if the course does not exist. The lecture is assigned a date and 
    gets a random QR identifier.
    """
    if not is_instructor(request.user):
        return unauthorized()

    course = Course.objects.filter(
        coursename=request.POST.get('choice', '').strip()).first()
    if course is None:
        return HttpResponseBadRequest('No such course')

    lecture = Lecture.objects.create(
        courseID=course,
        lectureDate=datetime.now(CDT).date(),
        QRidentifier=secrets.token_hex(6))
    return JsonResponse({'course': course.coursename,
                         'qr_identifier': lecture.QRidentifier})


@csrf_exempt
@require_POST
def createQRCodeUpload(request):
    """
    Saves an uploaded QR-code (POST, students only).

    Reads the uploaded image. Returns 401 if user is not a student, and 400 
    if no file was sent.
    """
    if not is_student(request.user):
        return unauthorized()

    image = request.FILES.get('imageUpload')
    if image is None:
        return HttpResponseBadRequest('Missing imageUpload file')

    student = StudentProfile.objects.get(userID=request.user)
    QRCodeUpload.objects.create(studentID=student, QRcodeImage=image)
    return JsonResponse({'status': 'ok'})


@require_GET
def dumpUploads(request):
    """
    Return every upload as JSON (GET, instructors only).

    Outputs a list of  dictionaries.
    Returns 401 user is not an instructor.
    """
    if not is_instructor(request.user):
        return unauthorized()

    data = [{'username': u.studentID.userID.username,
             'upload_time': u.time.strftime('%Y-%m-%d %H:%M:%S')}
            for u in QRCodeUpload.objects.select_related('studentID__userID')]
    return JsonResponse(data, safe=False)

# ---------------------------------------------------------------------------
# HW6  — getUploads
# ---------------------------------------------------------------------------



