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

from .models import InstructorProfile, StudentProfile

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



# ---------------------------------------------------------------------------
# HW6  — getUploads
# ---------------------------------------------------------------------------



