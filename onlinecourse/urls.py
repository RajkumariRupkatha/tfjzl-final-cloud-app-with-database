from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views


app_name = 'onlinecourse'

urlpatterns = [
    # Course list
    path(
        route='',
        view=views.CourseListView.as_view(),
        name='index'
    ),

    # User registration
    path(
        'registration/',
        views.registration_request,
        name='registration'
    ),

    # User login
    path(
        'login/',
        views.login_request,
        name='login'
    ),

    # User logout
    path(
        'logout/',
        views.logout_request,
        name='logout'
    ),

    # Example: /onlinecourse/5/
    path(
        '<int:pk>/',
        views.CourseDetailView.as_view(),
        name='course_details'
    ),

    # Example: /onlinecourse/5/enroll/
    path(
        '<int:course_id>/enroll/',
        views.enroll,
        name='enroll'
    ),

    # Submit an exam
    path(
        '<int:course_id>/submit/',
        views.submit,
        name='submit'
    ),

    # Display and evaluate an exam result
    path(
        'course/<int:course_id>/submission/<int:submission_id>/result/',
        views.show_exam_result,
        name='exam_result'
    ),

] + static(
    settings.MEDIA_URL,
    document_root=settings.MEDIA_ROOT
)