from datetime import date, timedelta

from django.test import TestCase
from django.urls import reverse

from .forms import BatchForm, CourseForm, EnrollmentForm
from .models import Batch, Course, Enrollment, Instructor, Student


class CoreFormTests(TestCase):
    def setUp(self):
        self.instructor = Instructor.objects.create(
            first_name='Asha',
            last_name='Mehta',
            email='asha@example.com',
        )
        self.course = Course.objects.create(
            title='Data Science Immersive',
            slug='data-science-immersive',
            duration_weeks=12,
            fee='25000.00',
            instructor=self.instructor,
            status='active',
        )
        self.batch = Batch.objects.create(
            name='Weekend Cohort',
            course=self.course,
            instructor=self.instructor,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            max_seats=1,
            status='ongoing',
        )
        self.student_one = Student.objects.create(
            first_name='Riya',
            last_name='Shah',
            email='riya@example.com',
        )
        self.student_two = Student.objects.create(
            first_name='Kabir',
            last_name='Shah',
            email='kabir@example.com',
        )

    def test_course_form_generates_unique_slug(self):
        form = CourseForm(data={
            'title': 'Data Science Immersive',
            'description': 'Duplicate title should get a unique slug.',
            'duration_weeks': 8,
            'fee': '10000.00',
            'instructor': self.instructor.pk,
            'status': 'active',
        })

        assert form.is_valid(), form.errors

        duplicate_course = form.save()

        assert duplicate_course.slug == 'data-science-immersive-2', duplicate_course.slug

    def test_batch_form_rejects_reversed_dates(self):
        form = BatchForm(data={
            'name': 'Invalid Batch',
            'course': self.course.pk,
            'instructor': self.instructor.pk,
            'start_date': date.today().isoformat(),
            'end_date': (date.today() - timedelta(days=1)).isoformat(),
            'max_seats': 20,
            'status': 'upcoming',
        })

        assert not form.is_valid()
        assert 'End date cannot be earlier than the start date.' in form.non_field_errors()

    def test_enrollment_form_rejects_full_batch(self):
        Enrollment.objects.create(
            student=self.student_one,
            batch=self.batch,
            status='active',
        )

        form = EnrollmentForm(data={
            'student': self.student_two.pk,
            'batch': self.batch.pk,
            'enrolled_on': date.today().isoformat(),
            'status': 'active',
            'notes': '',
        })

        assert not form.is_valid()
        assert 'No seats are available in the selected batch.' in form.non_field_errors()


class PublicLearnerFlowTests(TestCase):
    def setUp(self):
        self.instructor = Instructor.objects.create(
            first_name='Meera',
            last_name='Nair',
            email='meera@example.com',
            bio='Industry practitioner with 10 years of experience.',
        )
        self.active_course = Course.objects.create(
            title='Python Foundations',
            slug='python-foundations',
            description='Learn Python from scratch.',
            duration_weeks=6,
            fee='12000.00',
            instructor=self.instructor,
            status='active',
        )
        self.draft_course = Course.objects.create(
            title='Hidden Draft Course',
            slug='hidden-draft-course',
            duration_weeks=4,
            fee='9000.00',
            instructor=self.instructor,
            status='draft',
        )
        self.batch = Batch.objects.create(
            name='Weekday Morning',
            course=self.active_course,
            instructor=self.instructor,
            start_date=date.today() + timedelta(days=1),
            end_date=date.today() + timedelta(days=60),
            max_seats=25,
            status='upcoming',
        )

    def _register_learner(self):
        response = self.client.post(reverse('public:learner_register'), {
            'first_name': 'Aarav',
            'last_name': 'Sharma',
            'email': 'aarav@example.com',
            'phone': '9999999999',
            'date_of_birth': '2000-01-01',
            'gender': 'M',
            'address': 'Pune',
            'password': 'StrongPass123!',
            'confirm_password': 'StrongPass123!',
        })
        assert response.status_code == 302
        return Student.objects.get(email='aarav@example.com')

    def _login_learner(self):
        return self.client.post(reverse('public:learner_login'), {
            'email': 'aarav@example.com',
            'password': 'StrongPass123!',
        })

    def test_course_catalog_lists_only_active_courses(self):
        response = self.client.get(reverse('public:course_catalog'))

        assert response.status_code == 200
        content = response.content.decode()
        assert 'Python Foundations' in content
        assert 'Hidden Draft Course' not in content

    def test_registration_creates_pending_learner_and_separate_session_auth(self):
        learner = self._register_learner()

        assert learner.status == 'pending'
        assert learner.password_hash

        login_response = self._login_learner()
        assert login_response.status_code == 302
        assert login_response.url == reverse('public:learner_dashboard')

        crm_response = self.client.get(reverse('core:dashboard'))
        assert crm_response.status_code == 302
        assert reverse('core:login') in crm_response.url

    def test_enrollment_request_creates_pending_enrollment_visible_in_crm_records(self):
        learner = self._register_learner()
        login_response = self._login_learner()
        assert login_response.status_code == 302

        response = self.client.post(reverse('public:enrollment_request'), {
            'batch': self.batch.pk,
            'notes': 'I would like to join this cohort.',
        })

        assert response.status_code == 302
        enrollment = Enrollment.objects.get(student=learner, batch=self.batch)
        assert enrollment.status == 'pending'
