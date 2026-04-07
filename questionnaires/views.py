from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Avg, Count
from .models import Questionnaire, Question, Option, UserQuestionnaireAttempt, UserResponse
from ratings.models import Rating
from core.decorators import batch_required  # ADD THIS IMPORT

@login_required
@batch_required
def questionnaire_list(request):
    if request.user.is_admin_role():
        questionnaires = Questionnaire.objects.all()
    else:
        questionnaires = Questionnaire.objects.filter(is_published=True, is_active=True)
    
    context = {'questionnaires': questionnaires}
    return render(request, 'questionnaires/questionnaire_list.html', context)

@login_required
@batch_required
def start_questionnaire(request, questionnaire_id):
    questionnaire = get_object_or_404(Questionnaire, id=questionnaire_id)
    
    # Check if already attempted
    existing_attempt = UserQuestionnaireAttempt.objects.filter(
        user=request.user, 
        questionnaire=questionnaire, 
        status='IN_PROGRESS'
    ).first()
    
    if existing_attempt:
        return redirect('questionnaires:attempt_questionnaire', attempt_id=existing_attempt.id)
    
    # Check if multiple attempts allowed
    if not questionnaire.allow_multiple_attempts:
        previous_attempts = UserQuestionnaireAttempt.objects.filter(
            user=request.user, 
            questionnaire=questionnaire
        ).count()
        if previous_attempts > 0:
            messages.error(request, 'You have already attempted this questionnaire.')
            return redirect('questionnaires:questionnaire_list')
    
    # Create new attempt
    attempt = UserQuestionnaireAttempt.objects.create(
        user=request.user,
        questionnaire=questionnaire
    )
    
    return redirect('questionnaires:attempt_questionnaire', attempt_id=attempt.id)

@login_required
@batch_required
def attempt_questionnaire(request, attempt_id):
    attempt = get_object_or_404(UserQuestionnaireAttempt, id=attempt_id, user=request.user)
    
    if attempt.status != 'IN_PROGRESS':
        messages.info(request, 'This attempt has already been submitted.')
        return redirect('questionnaires:view_results', attempt_id=attempt.id)
    
    questions = attempt.questionnaire.questions.all().prefetch_related('options')
    
    if request.method == 'POST':
        # Process submission
        for question in questions:
            if question.question_type == 'MCQ' or question.question_type == 'IMAGE_MCQ':
                selected_option_id = request.POST.get(f'question_{question.id}')
                if selected_option_id:
                    option = Option.objects.get(id=selected_option_id)
                    UserResponse.objects.update_or_create(
                        attempt=attempt,
                        question=question,
                        defaults={
                            'selected_option': option,
                            'is_correct': option.is_correct,
                            'marks_obtained': question.marks if option.is_correct else 0
                        }
                    )
            elif question.question_type == 'SUBJECTIVE':
                text_response = request.POST.get(f'question_{question.id}')
                if text_response:
                    UserResponse.objects.update_or_create(
                        attempt=attempt,
                        question=question,
                        defaults={'text_response': text_response}
                    )
        
        # Mark as submitted
        attempt.status = 'SUBMITTED'
        attempt.submitted_at = timezone.now()
        
        # Calculate time taken
        time_taken = (timezone.now() - attempt.started_at).total_seconds() / 60
        attempt.time_taken_minutes = int(time_taken)
        
        # Calculate score for MCQs
        total_score = attempt.responses.filter(is_correct=True).aggregate(
            total=Sum('marks_obtained')
        )['total'] or 0
        attempt.score = total_score
        attempt.total_marks = questions.aggregate(total=Sum('marks'))['total'] or 0
        attempt.save()
        
        messages.success(request, 'Questionnaire submitted successfully!')
        return redirect('questionnaires:view_results', attempt_id=attempt.id)
    
    context = {
        'attempt': attempt,
        'questionnaire': attempt.questionnaire,
        'questions': questions,
    }
    
    return render(request, 'questionnaires/attempt_questionnaire.html', context)

@login_required
@batch_required
def view_results(request, attempt_id):
    attempt = get_object_or_404(UserQuestionnaireAttempt, id=attempt_id)
    
    # Check permissions
    if attempt.user != request.user and not request.user.is_volunteer_role():
        messages.error(request, 'You do not have permission to view these results.')
        return redirect('core:homepage')
    
    responses = attempt.responses.all().select_related('question', 'selected_option')
    
    # Get rating if exists
    rating = Rating.objects.filter(
        questionnaire_attempt=attempt
    ).first()
    
    context = {
        'attempt': attempt,
        'responses': responses,
        'rating': rating,
    }
    
    return render(request, 'questionnaires/view_results.html', context)

@login_required
def my_attempts(request):
    attempts = UserQuestionnaireAttempt.objects.filter(
        user=request.user
    ).select_related('questionnaire').order_by('-started_at')
    
    context = {'attempts': attempts}
    return render(request, 'questionnaires/my_attempts.html', context)
