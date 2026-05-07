from django.contrib import messages
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from .forms import LearnerEnrollmentRequestForm, LearnerLoginForm, LearnerRegistrationForm
from .models import Course, Enrollment, Student


LEARNER_SESSION_KEY = 'learner_id'


def _get_current_learner(request):
    learner_id = request.session.get(LEARNER_SESSION_KEY)
    if not learner_id:
        return None
    return Student.objects.filter(pk=learner_id).first()


def learner_login_required(view_func):
    def wrapped(request, *args, **kwargs):
        learner = _get_current_learner(request)
        if not learner:
            messages.error(request, 'Please log in to access your dashboard.')
            return redirect('public:learner_login')
        request.learner = learner
        return view_func(request, *args, **kwargs)

    return wrapped


def home(request):
    featured_courses = Course.objects.filter(status='active').select_related('instructor')[:6]
    return render(request, 'public/home.html', {
        'featured_courses': featured_courses,
        'learner': _get_current_learner(request),
    })


def about(request):
    return render(request, 'public/about.html', {'learner': _get_current_learner(request)})


def contact(request):
    return render(request, 'public/contact.html', {'learner': _get_current_learner(request)})


def course_catalog(request):
    courses = Course.objects.filter(status='active').select_related('instructor')
    q = request.GET.get('q', '').strip()
    if q:
        courses = courses.filter(Q(title__icontains=q) | Q(description__icontains=q))
    return render(request, 'public/courses/list.html', {
        'courses': courses,
        'q': q,
        'learner': _get_current_learner(request),
    })


def course_detail(request, slug):
    course = get_object_or_404(
        Course.objects.select_related('instructor').filter(status='active'),
        slug=slug,
    )
    batches = course.batches.select_related('instructor').annotate(active_enrollments=Count(
        'enrollments', filter=Q(enrollments__status='active')
    ))
    return render(request, 'public/courses/detail.html', {
        'course': course,
        'batches': batches,
        'learner': _get_current_learner(request),
    })


def learner_register(request):
    if _get_current_learner(request):
        return redirect('public:learner_dashboard')

    form = LearnerRegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Registration submitted successfully. Your account is pending staff approval.')
        return redirect('public:learner_login')

    return render(request, 'public/auth/register.html', {
        'form': form,
        'learner': _get_current_learner(request),
    })


def learner_login(request):
    if _get_current_learner(request):
        return redirect('public:learner_dashboard')

    form = LearnerLoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']
        learner = Student.objects.filter(email__iexact=email).first()
        if learner and learner.check_password(password):
            request.session.cycle_key()
            request.session[LEARNER_SESSION_KEY] = learner.pk
            return redirect('public:learner_dashboard')
        messages.error(request, 'Invalid email or password.')

    return render(request, 'public/auth/login.html', {
        'form': form,
        'learner': _get_current_learner(request),
    })


def learner_logout(request):
    request.session.pop(LEARNER_SESSION_KEY, None)
    messages.success(request, 'You have been logged out.')
    return redirect('public:home')


@learner_login_required
def learner_dashboard(request):
    enrollments = Enrollment.objects.filter(student=request.learner).select_related('batch__course').order_by('-created_at')
    return render(request, 'public/learner/dashboard.html', {
        'learner': request.learner,
        'enrollments': enrollments,
    })


@learner_login_required
def enrollment_request(request):
    form = LearnerEnrollmentRequestForm(request.POST or None, student=request.learner)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Enrollment request submitted. Our team will review it shortly.')
        return redirect('public:learner_dashboard')
    return render(request, 'public/learner/enrollment_request.html', {
        'form': form,
        'learner': request.learner,
    })
