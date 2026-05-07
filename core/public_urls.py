from django.urls import path

from . import public_views

app_name = 'public'

urlpatterns = [
    path('', public_views.home, name='home'),
    path('about/', public_views.about, name='about'),
    path('contact/', public_views.contact, name='contact'),
    path('courses/', public_views.course_catalog, name='course_catalog'),
    path('courses/<slug:slug>/', public_views.course_detail, name='course_detail'),
    path('register/', public_views.learner_register, name='learner_register'),
    path('login/', public_views.learner_login, name='learner_login'),
    path('logout/', public_views.learner_logout, name='learner_logout'),
    path('dashboard/', public_views.learner_dashboard, name='learner_dashboard'),
    path('enrollment-request/', public_views.enrollment_request, name='enrollment_request'),
]
