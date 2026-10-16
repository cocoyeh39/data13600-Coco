"""
views.py — HTTP request handlers for AttendanceChimp.

Each view corresponds to one URL endpoint.  Views receive an HTTP request,
interact with the database via models.py, and return an HTTP response.
"""

from django.shortcuts import render, redirect
from django.http import (HttpResponse, HttpResponseForbidden,
                         HttpResponseBadRequest, JsonResponse)
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from datetime import datetime
import zoneinfo
import json
import io

# from .models import (InstructorProfile, StudentProfile, Course, Enrollment,
#                      Lecture, QRCodeUpload, is_instructor, is_student,
#                      getUploadsForCourse)

CDT = zoneinfo.ZoneInfo("America/Chicago")


# ---------------------------------------------------------------------------
# HW2  — index, time, sum
# ---------------------------------------------------------------------------

from datetime import datetime
from zoneinfo import ZoneInfo
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render

def time_view(request):
    now = datetime.now(ZoneInfo("America/Chicago"))
    return HttpResponse(now.strftime("%H:%M"), content_type = "text/plain")

def sum_view(request):
    n1 = float(request.GET.get("n1",10))
    n2 = float(request.GET.get("n2",10))
    total = n1+n2
    if total.is_integer():
        total = int(total)
    return HttpResponse(f"<p>sum: {total}</p>")

def index(request):
    """Render the home page (index.html)."""

    context = {}
    return render(request, 'app/index.html', context)


# ---------------------------------------------------------------------------
# HW4  — user creation
# ---------------------------------------------------------------------------



# ---------------------------------------------------------------------------
# HW5  — courses, lectures, QR uploads, dump
# ---------------------------------------------------------------------------



# ---------------------------------------------------------------------------
# HW6  — getUploads
# ---------------------------------------------------------------------------



