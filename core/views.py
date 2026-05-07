from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from .models import Student, Instructor, Course, Batch, Enrollment
from .forms import StudentForm, InstructorForm, CourseForm, BatchForm, EnrollmentForm


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

def crm_login(request):
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user and user.is_staff:
            login(request, user)
            return redirect(request.GET.get('next', 'core:dashboard'))
        messages.error(request, 'Invalid credentials or insufficient permissions.')
    return render(request, 'crm/login.html')


def crm_logout(request):
    logout(request)
    return redirect('core:login')


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@login_required
def dashboard(request):
    context = {
        'total_students': Student.objects.filter(status='active').count(),
        'total_instructors': Instructor.objects.filter(is_active=True).count(),
        'total_courses': Course.objects.filter(status='active').count(),
        'total_batches': Batch.objects.filter(status='ongoing').count(),
        'pending_enrollments': Enrollment.objects.filter(status='pending').count(),
        'recent_students': Student.objects.order_by('-created_at')[:5],
        'recent_enrollments': Enrollment.objects.select_related(
            'student', 'batch__course'
        ).order_by('-created_at')[:5],
        'ongoing_batches': Batch.objects.filter(status='ongoing').select_related(
            'course', 'instructor'
        )[:5],
    }
    return render(request, 'crm/dashboard.html', context)


# ---------------------------------------------------------------------------
# Students
# ---------------------------------------------------------------------------

@login_required
def student_list(request):
    qs = Student.objects.all()
    q = request.GET.get('q', '').strip()
    status = request.GET.get('status', '')
    if q:
        qs = qs.filter(
            Q(first_name__icontains=q) | Q(last_name__icontains=q) |
            Q(email__icontains=q) | Q(phone__icontains=q)
        )
    if status:
        qs = qs.filter(status=status)
    return render(request, 'crm/students/list.html', {
        'students': qs,
        'q': q,
        'status': status,
        'status_choices': Student.STATUS_CHOICES,
    })


@login_required
def student_detail(request, pk):
    student = get_object_or_404(Student, pk=pk)
    enrollments = student.enrollments.select_related('batch__course', 'batch__instructor')
    return render(request, 'crm/students/detail.html', {
        'student': student,
        'enrollments': enrollments,
    })


@login_required
def student_add(request):
    form = StudentForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        student = form.save()
        messages.success(request, f'Student "{student.full_name}" added successfully.')
        return redirect('core:student_detail', pk=student.pk)
    return render(request, 'crm/students/form.html', {'form': form, 'action': 'Add'})


@login_required
def student_edit(request, pk):
    student = get_object_or_404(Student, pk=pk)
    form = StudentForm(request.POST or None, request.FILES or None, instance=student)
    if form.is_valid():
        form.save()
        messages.success(request, 'Student updated successfully.')
        return redirect('core:student_detail', pk=pk)
    return render(request, 'crm/students/form.html', {
        'form': form, 'action': 'Edit', 'student': student,
    })


@login_required
def student_delete(request, pk):
    student = get_object_or_404(Student, pk=pk)
    if request.method == 'POST':
        name = student.full_name
        student.delete()
        messages.success(request, f'Student "{name}" deleted.')
        return redirect('core:student_list')
    return render(request, 'crm/confirm_delete.html', {
        'object': student, 'object_type': 'Student',
        'cancel_url': 'core:student_detail', 'pk': pk,
    })


# ---------------------------------------------------------------------------
# Instructors
# ---------------------------------------------------------------------------

@login_required
def instructor_list(request):
    qs = Instructor.objects.all()
    q = request.GET.get('q', '').strip()
    active = request.GET.get('active', '')
    if q:
        qs = qs.filter(
            Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(email__icontains=q)
        )
    if active == '1':
        qs = qs.filter(is_active=True)
    elif active == '0':
        qs = qs.filter(is_active=False)
    return render(request, 'crm/instructors/list.html', {
        'instructors': qs, 'q': q, 'active': active,
    })


@login_required
def instructor_detail(request, pk):
    instructor = get_object_or_404(Instructor, pk=pk)
    courses = instructor.courses.all()
    batches = instructor.batches.select_related('course').order_by('-start_date')
    return render(request, 'crm/instructors/detail.html', {
        'instructor': instructor, 'courses': courses, 'batches': batches,
    })


@login_required
def instructor_add(request):
    form = InstructorForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        instructor = form.save()
        messages.success(request, f'Instructor "{instructor.full_name}" added.')
        return redirect('core:instructor_detail', pk=instructor.pk)
    return render(request, 'crm/instructors/form.html', {'form': form, 'action': 'Add'})


@login_required
def instructor_edit(request, pk):
    instructor = get_object_or_404(Instructor, pk=pk)
    form = InstructorForm(request.POST or None, request.FILES or None, instance=instructor)
    if form.is_valid():
        form.save()
        messages.success(request, 'Instructor updated.')
        return redirect('core:instructor_detail', pk=pk)
    return render(request, 'crm/instructors/form.html', {
        'form': form, 'action': 'Edit', 'instructor': instructor,
    })


@login_required
def instructor_delete(request, pk):
    instructor = get_object_or_404(Instructor, pk=pk)
    if request.method == 'POST':
        name = instructor.full_name
        instructor.delete()
        messages.success(request, f'Instructor "{name}" deleted.')
        return redirect('core:instructor_list')
    return render(request, 'crm/confirm_delete.html', {
        'object': instructor, 'object_type': 'Instructor',
        'cancel_url': 'core:instructor_detail', 'pk': pk,
    })


# ---------------------------------------------------------------------------
# Courses
# ---------------------------------------------------------------------------

@login_required
def course_list(request):
    qs = Course.objects.select_related('instructor').all()
    q = request.GET.get('q', '').strip()
    status = request.GET.get('status', '')
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q))
    if status:
        qs = qs.filter(status=status)
    return render(request, 'crm/courses/list.html', {
        'courses': qs, 'q': q, 'status': status,
        'status_choices': Course.STATUS_CHOICES,
    })


@login_required
def course_detail(request, pk):
    course = get_object_or_404(Course, pk=pk)
    batches = course.batches.select_related('instructor').annotate(
        enrolled=Count('enrollments')
    )
    return render(request, 'crm/courses/detail.html', {
        'course': course, 'batches': batches,
    })


@login_required
def course_add(request):
    form = CourseForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        course = form.save()
        messages.success(request, f'Course "{course.title}" added.')
        return redirect('core:course_detail', pk=course.pk)
    return render(request, 'crm/courses/form.html', {'form': form, 'action': 'Add'})


@login_required
def course_edit(request, pk):
    course = get_object_or_404(Course, pk=pk)
    form = CourseForm(request.POST or None, request.FILES or None, instance=course)
    if form.is_valid():
        form.save()
        messages.success(request, 'Course updated.')
        return redirect('core:course_detail', pk=pk)
    return render(request, 'crm/courses/form.html', {
        'form': form, 'action': 'Edit', 'course': course,
    })


@login_required
def course_delete(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if request.method == 'POST':
        title = course.title
        course.delete()
        messages.success(request, f'Course "{title}" deleted.')
        return redirect('core:course_list')
    return render(request, 'crm/confirm_delete.html', {
        'object': course, 'object_type': 'Course',
        'cancel_url': 'core:course_detail', 'pk': pk,
    })


# ---------------------------------------------------------------------------
# Batches
# ---------------------------------------------------------------------------

@login_required
def batch_list(request):
    qs = Batch.objects.select_related('course', 'instructor').all()
    q = request.GET.get('q', '').strip()
    status = request.GET.get('status', '')
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(course__title__icontains=q))
    if status:
        qs = qs.filter(status=status)
    return render(request, 'crm/batches/list.html', {
        'batches': qs, 'q': q, 'status': status,
        'status_choices': Batch.STATUS_CHOICES,
    })


@login_required
def batch_detail(request, pk):
    batch = get_object_or_404(Batch, pk=pk)
    enrollments = batch.enrollments.select_related('student').order_by(
        'student__last_name', 'student__first_name'
    )
    return render(request, 'crm/batches/detail.html', {
        'batch': batch, 'enrollments': enrollments,
    })


@login_required
def batch_add(request):
    form = BatchForm(request.POST or None)
    if form.is_valid():
        batch = form.save()
        messages.success(request, f'Batch "{batch.name}" added.')
        return redirect('core:batch_detail', pk=batch.pk)
    return render(request, 'crm/batches/form.html', {'form': form, 'action': 'Add'})


@login_required
def batch_edit(request, pk):
    batch = get_object_or_404(Batch, pk=pk)
    form = BatchForm(request.POST or None, instance=batch)
    if form.is_valid():
        form.save()
        messages.success(request, 'Batch updated.')
        return redirect('core:batch_detail', pk=pk)
    return render(request, 'crm/batches/form.html', {
        'form': form, 'action': 'Edit', 'batch': batch,
    })


@login_required
def batch_delete(request, pk):
    batch = get_object_or_404(Batch, pk=pk)
    if request.method == 'POST':
        name = batch.name
        batch.delete()
        messages.success(request, f'Batch "{name}" deleted.')
        return redirect('core:batch_list')
    return render(request, 'crm/confirm_delete.html', {
        'object': batch, 'object_type': 'Batch',
        'cancel_url': 'core:batch_detail', 'pk': pk,
    })


# ---------------------------------------------------------------------------
# Enrollments
# ---------------------------------------------------------------------------

@login_required
def enrollment_list(request):
    qs = Enrollment.objects.select_related(
        'student', 'batch__course'
    ).order_by('-created_at')
    q = request.GET.get('q', '').strip()
    status = request.GET.get('status', '')
    if q:
        qs = qs.filter(
            Q(student__first_name__icontains=q) |
            Q(student__last_name__icontains=q) |
            Q(batch__course__title__icontains=q)
        )
    if status:
        qs = qs.filter(status=status)
    return render(request, 'crm/enrollments/list.html', {
        'enrollments': qs, 'q': q, 'status': status,
        'status_choices': Enrollment.STATUS_CHOICES,
    })


@login_required
def enrollment_add(request):
    form = EnrollmentForm(request.POST or None)
    if form.is_valid():
        enrollment = form.save()
        messages.success(request, 'Enrollment created.')
        return redirect('core:enrollment_list')
    return render(request, 'crm/enrollments/form.html', {'form': form, 'action': 'Add'})


@login_required
def enrollment_edit(request, pk):
    enrollment = get_object_or_404(Enrollment, pk=pk)
    form = EnrollmentForm(request.POST or None, instance=enrollment)
    if form.is_valid():
        form.save()
        messages.success(request, 'Enrollment updated.')
        return redirect('core:enrollment_list')
    return render(request, 'crm/enrollments/form.html', {
        'form': form, 'action': 'Edit', 'enrollment': enrollment,
    })


@login_required
def enrollment_delete(request, pk):
    enrollment = get_object_or_404(Enrollment, pk=pk)
    if request.method == 'POST':
        enrollment.delete()
        messages.success(request, 'Enrollment removed.')
        return redirect('core:enrollment_list')
    return render(request, 'crm/confirm_delete.html', {
        'object': enrollment, 'object_type': 'Enrollment',
        'cancel_url': 'core:enrollment_list', 'pk': pk,
    })
