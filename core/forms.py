from django import forms
from .models import Student, Instructor, Course, Batch, Enrollment
from django.utils.text import slugify


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
        instance = super().save(commit=False)
        if not instance.slug:
            instance.slug = slugify(instance.title)
        if commit:
            instance.save()
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


class EnrollmentForm(forms.ModelForm):
    class Meta:
        model = Enrollment
        fields = ['student', 'batch', 'enrolled_on', 'status', 'notes']
        widgets = {
            'enrolled_on': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }
