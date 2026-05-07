from datetime import date, timedelta

from django.test import TestCase

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
