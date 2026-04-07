from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import (ApplicationForm, InterviewStatus, Batch, Camp, Session, 
                     IntercampActivity, MediaSubmission, UserBatch, ProgressTracking)
from .forms import ApplicationFormForm, MediaSubmissionForm
from questionnaires.models import Questionnaire, UserQuestionnaireAttempt
from .decorators import batch_required  # ADD THIS IMPORT

@login_required
def homepage(request):
    user = request.user
    context = {'user': user}
    
    # Check application status
    try:
        application = ApplicationForm.objects.get(user=user)
        context['application'] = application
        
        if application.status == 'PENDING':
            context['message'] = "Your application is under review."
        elif application.status == 'REJECTED':
            context['message'] = "Your application was not approved."
            return render(request, 'core/homepage.html', context)
        elif application.status == 'APPROVED':
            # Check interview status
            try:
                interview = InterviewStatus.objects.get(user=user)
                context['interview'] = interview
                
                if interview.status == 'FAILED':
                    context['message'] = "You are not selected. Thank you for your interest."
                elif interview.status == 'PASSED':
                    # Check batch assignment
                    user_batch = UserBatch.objects.filter(user=user, is_active=True).first()
                    if user_batch:
                        context['user_batch'] = user_batch
                        context['batch'] = user_batch.batch
                        context['current_stage'] = f"Camp {user_batch.current_camp}" if user_batch.current_camp > 0 else "Pre-Camp"
                    else:
                        context['message'] = "Congratulations! You passed the interview. Awaiting batch assignment."
                else:
                    context['message'] = "Your interview has been scheduled."
            except InterviewStatus.DoesNotExist:
                context['message'] = "You have been moved to the next step: Call Interview."
    except ApplicationForm.DoesNotExist:
        context['message'] = "Please complete your application form."
    
    return render(request, 'core/homepage.html', context)

@login_required
def submit_application(request):
    # Check if already submitted
    if ApplicationForm.objects.filter(user=request.user).exists():
        messages.info(request, 'You have already submitted your application.')
        return redirect('core:homepage')
    
    if request.method == 'POST':
        form = ApplicationFormForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.user = request.user
            application.save()
            messages.success(request, 'Application submitted successfully!')
            return redirect('core:homepage')
    else:
        form = ApplicationFormForm()
    
    return render(request, 'core/submit_application.html', {'form': form})

@login_required
@batch_required
def batch_detail(request, batch_id):
    batch = get_object_or_404(Batch, id=batch_id)
    user_batch = UserBatch.objects.filter(user=request.user, batch=batch).first()
    
    if not user_batch and not request.user.is_admin_role():
        messages.error(request, 'You are not enrolled in this batch.')
        return redirect('core:homepage')
    
    camps = Camp.objects.filter(batch=batch).prefetch_related('sessions')
    intercamp_activities = IntercampActivity.objects.filter(batch=batch)
    
    context = {
        'batch': batch,
        'user_batch': user_batch,
        'camps': camps,
        'intercamp_activities': intercamp_activities,
    }
    
    return render(request, 'core/batch_detail.html', context)

@login_required
def camp_detail(request, camp_id):
    camp = get_object_or_404(Camp, id=camp_id)
    sessions = Session.objects.filter(camp=camp)
    
    context = {
        'camp': camp,
        'sessions': sessions,
    }
    
    return render(request, 'core/camp_detail.html', context)

@login_required
@batch_required
def session_detail(request, session_id):
    session = get_object_or_404(Session, id=session_id)
    
    # Get pre-test and post-test questionnaires
    pre_tests = Questionnaire.objects.filter(session=session, test_type='PRE')
    post_tests = Questionnaire.objects.filter(session=session, test_type='POST')
    
    context = {
        'session': session,
        'pre_tests': pre_tests,
        'post_tests': post_tests,
    }
    
    return render(request, 'core/session_detail.html', context)

@login_required
@batch_required
def intercamp_activity_detail(request, activity_id):
    activity = get_object_or_404(IntercampActivity, id=activity_id)
    
    # Get user submissions
    user_submissions = MediaSubmission.objects.filter(
        user=request.user, 
        intercamp_activity=activity
    )
    
    context = {
        'activity': activity,
        'user_submissions': user_submissions,
    }
    
    return render(request, 'core/intercamp_activity.html', context)

@login_required
@batch_required
def submit_media(request, activity_id):
    activity = get_object_or_404(IntercampActivity, id=activity_id)
    
    if request.method == 'POST':
        form = MediaSubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.user = request.user
            submission.intercamp_activity = activity
            submission.save()
            messages.success(request, 'Media submitted successfully!')
            return redirect('core:intercamp_activity_detail', activity_id=activity.id)
    else:
        form = MediaSubmissionForm()
    
    return render(request, 'core/submit_media.html', {'form': form, 'activity': activity})

@login_required
@batch_required
def my_progress(request):
    user_batches = UserBatch.objects.filter(user=request.user)
    progress = ProgressTracking.objects.filter(user=request.user)
    
    # Calculate progress percentage for each batch
    for user_batch in user_batches:
        user_batch.progress_percentage = (user_batch.current_camp / 3) * 100 if user_batch.current_camp > 0 else 0
    
    context = {
        'user_batches': user_batches,
        'progress': progress,
    }
    
    return render(request, 'core/my_progress.html', context)

