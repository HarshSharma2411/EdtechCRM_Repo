from django.contrib import admin
from .models import Instructor, Course, Batch, Student, Enrollment


@admin.register(Instructor)
class InstructorAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'phone', 'joined_on', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('first_name', 'last_name', 'email')
    ordering = ('last_name', 'first_name')
    list_editable = ('is_active',)
    date_hierarchy = 'joined_on'


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'instructor', 'duration_weeks', 'fee', 'status')
    list_filter = ('status', 'instructor')
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ('status',)
    ordering = ('title',)


class EnrollmentInline(admin.TabularInline):
    model = Enrollment
    extra = 0
    fields = ('student', 'enrolled_on', 'status')
    readonly_fields = ('enrolled_on',)


@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ('name', 'course', 'instructor', 'start_date', 'end_date',
                    'enrolled_count', 'seats_available', 'status')
    list_filter = ('status', 'course', 'instructor')
    search_fields = ('name', 'course__title')
    ordering = ('-start_date',)
    inlines = [EnrollmentInline]

    @admin.display(description='Enrolled')
    def enrolled_count(self, obj):
        return obj.enrolled_count

    @admin.display(description='Available Seats')
    def seats_available(self, obj):
        return obj.seats_available


class EnrollmentStudentInline(admin.TabularInline):
    model = Enrollment
    extra = 0
    fields = ('batch', 'enrolled_on', 'status', 'notes')
    readonly_fields = ('enrolled_on',)


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'phone', 'status', 'enrolled_on', 'active_courses')
    list_filter = ('status', 'gender')
    search_fields = ('first_name', 'last_name', 'email', 'phone')
    ordering = ('last_name', 'first_name')
    list_editable = ('status',)
    date_hierarchy = 'enrolled_on'
    inlines = [EnrollmentStudentInline]
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Personal Info', {
            'fields': ('first_name', 'last_name', 'email', 'phone',
                       'date_of_birth', 'gender', 'photo')
        }),
        ('Address', {'fields': ('address',), 'classes': ('collapse',)}),
        ('Status', {'fields': ('status', 'enrolled_on')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    @admin.display(description='Active Courses')
    def active_courses(self, obj):
        return obj.active_enrollments.count()


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'batch', 'enrolled_on', 'status')
    list_filter = ('status', 'batch__course')
    search_fields = ('student__first_name', 'student__last_name', 'student__email',
                     'batch__name', 'batch__course__title')
    ordering = ('-enrolled_on',)
    list_editable = ('status',)


# Customize admin site header
admin.site.site_header = 'EdTech CRM'
admin.site.site_title = 'EdTech CRM Admin'
admin.site.index_title = 'CRM Administration'
