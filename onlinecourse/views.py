from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponseRedirect
from django.contrib.auth.models import User
from django.urls import reverse
from django.views import generic
from django.contrib.auth import login, logout, authenticate
import logging

# Import all models required for the assessment feature
from .models import Course, Enrollment, Question, Choice, Submission


# Get an instance of a logger
logger = logging.getLogger(__name__)


def registration_request(request):
    context = {}

    if request.method == 'GET':
        return render(
            request,
            'onlinecourse/user_registration_bootstrap.html',
            context
        )

    elif request.method == 'POST':
        # Check if user exists
        username = request.POST['username']
        password = request.POST['psw']
        first_name = request.POST['firstname']
        last_name = request.POST['lastname']
        user_exist = False

        try:
            User.objects.get(username=username)
            user_exist = True
        except User.DoesNotExist:
            logger.error("New user")

        if not user_exist:
            user = User.objects.create_user(
                username=username,
                first_name=first_name,
                last_name=last_name,
                password=password
            )

            login(request, user)
            return redirect("onlinecourse:index")

        context['message'] = "User already exists."

        return render(
            request,
            'onlinecourse/user_registration_bootstrap.html',
            context
        )


def login_request(request):
    context = {}

    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['psw']

        user = authenticate(
            username=username,
            password=password
        )

        if user is not None:
            login(request, user)
            return redirect('onlinecourse:index')

        context['message'] = "Invalid username or password."

        return render(
            request,
            'onlinecourse/user_login_bootstrap.html',
            context
        )

    return render(
        request,
        'onlinecourse/user_login_bootstrap.html',
        context
    )


def logout_request(request):
    logout(request)
    return redirect('onlinecourse:index')


def check_if_enrolled(user, course):
    is_enrolled = False

    if user.id is not None:
        # Check whether the user is enrolled
        num_results = Enrollment.objects.filter(
            user=user,
            course=course
        ).count()

        if num_results > 0:
            is_enrolled = True

    return is_enrolled


# Course list view
class CourseListView(generic.ListView):
    template_name = 'onlinecourse/course_list_bootstrap.html'
    context_object_name = 'course_list'

    def get_queryset(self):
        user = self.request.user
        courses = Course.objects.order_by('-total_enrollment')[:10]

        for course in courses:
            if user.is_authenticated:
                course.is_enrolled = check_if_enrolled(
                    user,
                    course
                )

        return courses


# Course detail view
class CourseDetailView(generic.DetailView):
    model = Course
    template_name = 'onlinecourse/course_detail_bootstrap.html'


def enroll(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    user = request.user

    is_enrolled = check_if_enrolled(user, course)

    if not is_enrolled and user.is_authenticated:
        # Create an enrollment
        Enrollment.objects.create(
            user=user,
            course=course,
            mode='honor'
        )

        course.total_enrollment += 1
        course.save()

    return HttpResponseRedirect(
        reverse(
            viewname='onlinecourse:course_details',
            args=(course.id,)
        )
    )


# Create an exam submission record
def submit(request, course_id):
    course = get_object_or_404(
        Course,
        pk=course_id
    )

    user = request.user

    # Get the user's enrollment for this course
    enrollment = Enrollment.objects.get(
        user=user,
        course=course
    )

    # Create a new submission
    submission = Submission.objects.create(
        enrollment=enrollment
    )

    # Get the selected choice IDs from the form
    choices = extract_answers(request)

    # Associate the selected choices with the submission
    submission.choices.set(choices)

    submission_id = submission.id

    # Redirect to the exam result page
    return HttpResponseRedirect(
        reverse(
            viewname='onlinecourse:exam_result',
            args=(course_id, submission_id,)
        )
    )


# Collect the selected choice IDs from the submitted form
def extract_answers(request):
    submitted_answers = []

    for key in request.POST:
        if key.startswith('choice'):
            value = request.POST[key]
            choice_id = int(value)
            submitted_answers.append(choice_id)

    return submitted_answers


# Evaluate and display the exam result
def show_exam_result(request, course_id, submission_id):
    context = {}

    # Get the course and submission
    course = get_object_or_404(
        Course,
        pk=course_id
    )

    submission = Submission.objects.get(
        id=submission_id
    )

    # Get all choices selected in this submission
    choices = submission.choices.all()

    total_score = 0
    questions = course.question_set.all()

    # Evaluate each question
    for question in questions:
        correct_choices = question.choice_set.filter(
            is_correct=True
        )

        selected_choices = choices.filter(
            question=question
        )

        # Award points only when selected choices exactly match
        # all of the correct choices
        if set(correct_choices) == set(selected_choices):
            total_score += question.grade

    context['course'] = course
    context['grade'] = total_score
    context['choices'] = choices

    return render(
        request,
        'onlinecourse/exam_result_bootstrap.html',
        context
    )