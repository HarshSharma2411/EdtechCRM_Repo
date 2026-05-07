from django import forms
from django.contrib.auth.password_validation import validate_password
from django.utils.text import slugify

from .models import Batch, Course, Enrollment, Instructor, Student


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = [
            'first_name', 'last_name', 'email', 'phone',
            'date_of_birth', 'gender', 'address', 'photo', 'status',
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 3}),
        }


class InstructorForm(forms.ModelForm):
    class Meta:
        model = Instructor
        fields = [
            'first_name', 'last_name', 'email', 'phone',
            'bio', 'photo', 'joined_on', 'is_active',
        ]
        widgets = {
            'joined_on': forms.DateInput(attrs={'type': 'date'}),
            'bio': forms.Textarea(attrs={'rows': 3}),
        }


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = [
            'title', 'description', 'duration_weeks', 'fee',
            'instructor', 'status', 'thumbnail',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def save(self, commit=True):
        """Persist the course while generating a unique slug for new records."""
        instance = super().save(commit=False)
        if not instance.slug:
            base_slug = slugify(instance.title)
            candidate_slug = base_slug
            suffix = 2
            while Course.objects.filter(slug=candidate_slug).exclude(pk=instance.pk).exists():
                candidate_slug = f'{base_slug}-{suffix}'
                suffix += 1
            instance.slug = candidate_slug
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class BatchForm(forms.ModelForm):
    class Meta:
        model = Batch
        fields = [
            'name', 'course', 'instructor', 'start_date',
            'end_date', 'max_seats', 'status',
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean(self):
        """Reject batches whose end date is earlier than the start date."""
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        if start_date and end_date and end_date < start_date:
            raise forms.ValidationError('End date cannot be earlier than the start date.')
        return cleaned_data


class EnrollmentForm(forms.ModelForm):
    class Meta:
        model = Enrollment
        fields = ['student', 'batch', 'enrolled_on', 'status', 'notes']
        widgets = {
            'enrolled_on': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }

    def clean(self):
        """Validate seat availability and batch state before saving an enrollment."""
        cleaned_data = super().clean()
        batch = cleaned_data.get('batch')
        student = cleaned_data.get('student')
        enrollment_status = cleaned_data.get('status')

        if not batch or not student:
            return cleaned_data

        existing_enrollment = Enrollment.objects.filter(student=student, batch=batch)
        if self.instance.pk:
            existing_enrollment = existing_enrollment.exclude(pk=self.instance.pk)
        if existing_enrollment.exists():
            raise forms.ValidationError('This student is already enrolled in the selected batch.')

        if enrollment_status in {'pending', 'active'} and batch.status in {'completed', 'cancelled'}:
            raise forms.ValidationError(
                'Pending or active enrollments cannot be created for completed or cancelled batches.'
            )

        active_enrollments = batch.enrollments.filter(status='active')
        if self.instance.pk:
            active_enrollments = active_enrollments.exclude(pk=self.instance.pk)
        if enrollment_status == 'active' and active_enrollments.count() >= batch.max_seats:
            raise forms.ValidationError('No seats are available in the selected batch.')

        return cleaned_data


class LearnerRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, min_length=8)
    confirm_password = forms.CharField(widget=forms.PasswordInput, min_length=8)

    class Meta:
        model = Student
        fields = [
            'first_name', 'last_name', 'email', 'phone', 'date_of_birth', 'gender', 'address',
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_email(self):
        email = self.cleaned_data['email']
        if Student.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError('Passwords do not match.')
        if password:
            validate_password(password)
        return cleaned_data

    def save(self, commit=True):
        student = super().save(commit=False)
        student.status = 'pending'
        student.set_password(self.cleaned_data['password'])
        if commit:
            student.save()
        return student


class LearnerLoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

    def clean_email(self):
        return self.cleaned_data['email'].strip().lower()


class LearnerEnrollmentRequestForm(forms.ModelForm):
    class Meta:
        model = Enrollment
        fields = ['batch', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        self.student = kwargs.pop('student')
        super().__init__(*args, **kwargs)
        self.fields['batch'].queryset = Batch.objects.select_related('course').filter(
            course__status='active',
            status__in=['upcoming', 'ongoing'],
        )

    def clean_batch(self):
        batch = self.cleaned_data['batch']
        if Enrollment.objects.filter(student=self.student, batch=batch).exists():
            raise forms.ValidationError('You have already requested enrollment for this batch.')
        return batch

    def save(self, commit=True):
        enrollment = super().save(commit=False)
        enrollment.student = self.student
        enrollment.status = 'pending'
        if commit:
            enrollment.save()
        return enrollment
