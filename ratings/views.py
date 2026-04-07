from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from questionnaires.models import UserQuestionnaireAttempt
from core.models import MediaSubmission
from .models import Rating

@login_required
def rate_questionnaire_attempt(request, attempt_id):
    if not request.user.is_volunteer_role():
        messages.error(request, 'You do not have permission to rate.')
        return redirect('core:homepage')
    
    attempt = get_object_or_404(UserQuestionnaireAttempt, id=attempt_id)
    
    if request.method == 'POST':
        score = request.POST.get('score')
        comment = request.POST.get('comment', '')
        
        Rating.objects.update_or_create(
            questionnaire_attempt=attempt,
            rated_by=request.user,
            defaults={'score': score, 'comment': comment}
        )
        
        # Update attempt status
        attempt.status = 'RATED'
        attempt.save()
        
        messages.success(request, 'Rating submitted successfully!')
        return redirect('questionnaires:view_results', attempt_id=attempt.id)
    
    existing_rating = Rating.objects.filter(
        questionnaire_attempt=attempt,
        rated_by=request.user
    ).first()
    
    context = {
        'attempt': attempt,
        'existing_rating': existing_rating,
    }
    
    return render(request, 'ratings/rate_attempt.html', context)

@login_required
def rate_media_submission(request, submission_id):
    if not request.user.is_volunteer_role():
        messages.error(request, 'You do not have permission to rate.')
        return redirect('core:homepage')
    
    submission = get_object_or_404(MediaSubmission, id=submission_id)
    
    if request.method == 'POST':
        score = request.POST.get('score')
        comment = request.POST.get('comment', '')
        
        Rating.objects.update_or_create(
            media_submission=submission,
            rated_by=request.user,
            defaults={'score': score, 'comment': comment}
        )
        
        messages.success(request, 'Rating submitted successfully!')
        return redirect('core:intercamp_activity_detail', activity_id=submission.intercamp_activity.id)
    
    existing_rating = Rating.objects.filter(
        media_submission=submission,
        rated_by=request.user
    ).first()
    
    context = {
        'submission': submission,
        'existing_rating': existing_rating,
    }
    
    return render(request, 'ratings/rate_media.html', context)

@login_required
def pending_ratings(request):
    if not request.user.is_volunteer_role():
        messages.error(request, 'You do not have permission to view this page.')
        return redirect('core:homepage')
    
    # Questionnaire attempts pending rating
    pending_attempts = UserQuestionnaireAttempt.objects.filter(
        status='SUBMITTED'
    ).select_related('user', 'questionnaire')
    
    # Media submissions pending rating
    pending_media = MediaSubmission.objects.filter(
        status='PENDING'
    ).select_related('user', 'intercamp_activity')
    
    context = {
        'pending_attempts': pending_attempts,
        'pending_media': pending_media,
    }
    
    return render(request, 'ratings/pending_ratings.html', context)
