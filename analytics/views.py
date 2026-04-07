from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Avg, Count, Sum, Q, F, Case, When, FloatField
from django.contrib import messages
from accounts.models import User
from core.models import Batch, Camp, Session, UserBatch
from questionnaires.models import UserQuestionnaireAttempt, Questionnaire
from ratings.models import Rating


@login_required
def analytics_dashboard(request):
    """Main analytics dashboard"""
    if not request.user.is_admin_role():
        messages.error(request, 'You do not have permission to view analytics.')
        return redirect('core:homepage')

    batches = Batch.objects.all()

    # Calculate stats
    total_students = UserBatch.objects.filter(is_active=True).count()
    total_attempts = UserQuestionnaireAttempt.objects.filter(status__in=['SUBMITTED', 'RATED']).count()
    avg_score = UserQuestionnaireAttempt.objects.filter(
        status__in=['SUBMITTED', 'RATED']
    ).aggregate(avg=Avg('score'))['avg'] or 0

    context = {
        'batches': batches,
        'total_students': total_students,
        'total_attempts': total_attempts,
        'avg_score': round(avg_score, 1),
    }

    return render(request, 'analytics/dashboard.html', context)


@login_required
def batch_analytics(request, batch_id):
    """Enhanced batch analytics with student performance details"""
    if not request.user.is_admin_role():
        messages.error(request, 'You do not have permission to view analytics.')
        return redirect('core:homepage')

    batch = get_object_or_404(Batch, id=batch_id)

    # Get all users in batch
    batch_users = UserBatch.objects.filter(batch=batch).select_related('user')

    # Get all camps for this batch
    camps = Camp.objects.filter(batch=batch).prefetch_related('sessions').order_by('camp_number')

    # Calculate batch statistics
    total_students = batch_users.count()

    # Average scores across all questionnaires in this batch
    avg_score = UserQuestionnaireAttempt.objects.filter(
        user__user_batches__batch=batch,
        status__in=['SUBMITTED', 'RATED']
    ).aggregate(avg=Avg('score'))['avg'] or 0

    # Total sessions
    total_sessions = Session.objects.filter(camp__batch=batch).count()

    # Get detailed student performance
    student_performance = []
    for ub in batch_users:
        user = ub.user
        attempts = UserQuestionnaireAttempt.objects.filter(
            user=user,
            status__in=['SUBMITTED', 'RATED']
        )

        # Overall average
        overall_avg = attempts.aggregate(avg=Avg('score'))['avg'] or 0

        # Pre-test average
        pre_attempts = attempts.filter(questionnaire__test_type='PRE')
        pre_avg = pre_attempts.aggregate(avg=Avg('score'))['avg'] or 0

        # Post-test average
        post_attempts = attempts.filter(questionnaire__test_type='POST')
        post_avg = post_attempts.aggregate(avg=Avg('score'))['avg'] or 0

        # Calculate improvement
        improvement = post_avg - pre_avg if pre_avg > 0 and post_avg > 0 else 0

        # Total attempts
        total_attempts = attempts.count()

        student_performance.append({
            'user': user,
            'current_camp': ub.current_camp,
            'overall_avg': round(overall_avg, 1),
            'pre_avg': round(pre_avg, 1),
            'post_avg': round(post_avg, 1),
            'improvement': round(improvement, 1),
            'total_attempts': total_attempts,
        })

    # Sort by overall average (default)
    student_performance.sort(key=lambda x: x['overall_avg'], reverse=True)

    context = {
        'batch': batch,
        'total_students': total_students,
        'avg_score': round(avg_score, 2),
        'total_sessions': total_sessions,
        'camps': camps,
        'batch_users': batch_users,
        'student_performance': student_performance,
    }

    return render(request, 'analytics/batch_analytics.html', context)


@login_required
def user_analytics(request, user_id):
    """Individual user analytics"""
    if not request.user.is_admin_role() and request.user.id != user_id:
        messages.error(request, 'You do not have permission to view this page.')
        return redirect('core:homepage')

    profile_user = get_object_or_404(User, id=user_id)

    # Get all attempts with related data
    attempts = UserQuestionnaireAttempt.objects.filter(
        user=profile_user,
        status__in=['SUBMITTED', 'RATED']
    ).select_related('questionnaire').order_by('-submitted_at')[:20]

    # All attempts for statistics
    all_attempts = UserQuestionnaireAttempt.objects.filter(
        user=profile_user,
        status__in=['SUBMITTED', 'RATED']
    )

    # Get ratings received by this user
    ratings = Rating.objects.filter(
        questionnaire_attempt__user=profile_user
    ).select_related('questionnaire_attempt__questionnaire', 'rated_by').order_by('-created_at')

    # Calculate statistics
    total_attempts = all_attempts.count()
    avg_score = all_attempts.aggregate(avg=Avg('score'))['avg'] or 0
    total_time = all_attempts.aggregate(total=Sum('time_taken_minutes'))['total'] or 0

    # Pre vs Post comparison
    pre_attempts = all_attempts.filter(questionnaire__test_type='PRE')
    post_attempts = all_attempts.filter(questionnaire__test_type='POST')

    pre_avg = pre_attempts.aggregate(avg=Avg('score'))['avg'] or 0
    post_avg = post_attempts.aggregate(avg=Avg('score'))['avg'] or 0
    pre_count = pre_attempts.count()
    post_count = post_attempts.count()

    # Get batch info
    user_batches = UserBatch.objects.filter(user=profile_user).select_related('batch')

    # Prepare chart data for progression
    chart_attempts = all_attempts.order_by('submitted_at')[:15]
    chart_data = {
        'labels': [f"{att.questionnaire.title[:20]}..." if len(att.questionnaire.title) > 20 
                   else att.questionnaire.title for att in chart_attempts],
        'scores': [float(att.score or 0) for att in chart_attempts],
        'dates': [att.submitted_at.strftime('%b %d') for att in chart_attempts]
    }

    context = {
        'profile_user': profile_user,
        'attempts': attempts,
        'ratings': ratings,
        'total_attempts': total_attempts,
        'avg_score': round(avg_score, 1),
        'total_time': total_time,
        'user_batches': user_batches,
        'pre_avg': round(pre_avg, 1),
        'post_avg': round(post_avg, 1),
        'pre_count': pre_count,
        'post_count': post_count,
        'chart_data': chart_data,
        'avg_rating': round(ratings.aggregate(avg=Avg('score'))['avg'] or 0, 1),
    }

    return render(request, 'analytics/user_analytics.html', context)


@login_required
def camp_analytics(request, camp_id):
    """Camp-wise analytics"""
    if not request.user.is_admin_role():
        messages.error(request, 'You do not have permission to view analytics.')
        return redirect('core:homepage')

    camp = get_object_or_404(Camp, id=camp_id)
    sessions = Session.objects.filter(camp=camp).order_by('session_number')

    # Initialize aggregated data
    session_data = []
    total_pre_attempts = 0
    total_post_attempts = 0
    total_pre_score = 0
    total_post_score = 0
    pre_sessions_count = 0
    post_sessions_count = 0

    for session in sessions:
        # Get PRE test data
        pre_questionnaires = Questionnaire.objects.filter(session=session, test_type='PRE')
        pre_attempts = UserQuestionnaireAttempt.objects.filter(
            questionnaire__in=pre_questionnaires,
            status__in=['SUBMITTED', 'RATED']
        )
        pre_count = pre_attempts.count()
        pre_avg = pre_attempts.aggregate(avg=Avg('score'))['avg'] or 0

        # Get POST test data
        post_questionnaires = Questionnaire.objects.filter(session=session, test_type='POST')
        post_attempts = UserQuestionnaireAttempt.objects.filter(
            questionnaire__in=post_questionnaires,
            status__in=['SUBMITTED', 'RATED']
        )
        post_count = post_attempts.count()
        post_avg = post_attempts.aggregate(avg=Avg('score'))['avg'] or 0

        # Aggregate totals
        total_pre_attempts += pre_count
        total_post_attempts += post_count

        if pre_count > 0:
            total_pre_score += pre_avg
            pre_sessions_count += 1

        if post_count > 0:
            total_post_score += post_avg
            post_sessions_count += 1

        session_data.append({
            'session': session,
            'pre_attempts': pre_count,
            'post_attempts': post_count,
            'pre_avg_score': round(pre_avg, 1),
            'post_avg_score': round(post_avg, 1),
            'total_attempts': pre_count + post_count,
            'combined_avg_score': round((pre_avg + post_avg) / 2 if (pre_count + post_count) > 0 else 0, 1)
        })

    # Calculate overall averages
    overall_pre_avg = round(total_pre_score / pre_sessions_count, 1) if pre_sessions_count > 0 else 0
    overall_post_avg = round(total_post_score / post_sessions_count, 1) if post_sessions_count > 0 else 0

    context = {
        'camp': camp,
        'session_data': session_data,
        'total_sessions': sessions.count(),
        'total_pre_attempts': total_pre_attempts,
        'total_post_attempts': total_post_attempts,
        'total_attempts': total_pre_attempts + total_post_attempts,
        'overall_pre_avg': overall_pre_avg,
        'overall_post_avg': overall_post_avg,
    }

    return render(request, 'analytics/camp_analytics.html', context)


# ============== AJAX ENDPOINTS FOR CHARTS ==============

@login_required
def batch_performance_chart_data(request, batch_id):
    """
    Returns chart data for batch performance
    Supports filters: view_type, camp_id, session_id
    """
    if not request.user.is_admin_role():
        return JsonResponse({'error': 'Permission denied'}, status=403)

    batch = get_object_or_404(Batch, id=batch_id)
    view_type = request.GET.get('view_type', 'overall')
    camp_id = request.GET.get('camp_id', '')
    session_id = request.GET.get('session_id', '')

    labels = []
    data = []

    if view_type == 'overall':
        # Overall performance across all camps and sessions
        camps = Camp.objects.filter(batch=batch).order_by('camp_number')
        for camp in camps:
            sessions = Session.objects.filter(camp=camp).order_by('session_number')
            for session in sessions:
                questionnaires = Questionnaire.objects.filter(session=session)
                avg_score = UserQuestionnaireAttempt.objects.filter(
                    questionnaire__in=questionnaires,
                    status__in=['SUBMITTED', 'RATED']
                ).aggregate(avg=Avg('score'))['avg'] or 0

                labels.append(f"Camp {camp.camp_number} - S{session.session_number}")
                data.append(round(avg_score, 2))

    elif view_type == 'camp' and camp_id:
        # Camp-specific performance
        camp = get_object_or_404(Camp, id=camp_id)
        sessions = Session.objects.filter(camp=camp).order_by('session_number')
        for session in sessions:
            questionnaires = Questionnaire.objects.filter(session=session)
            avg_score = UserQuestionnaireAttempt.objects.filter(
                questionnaire__in=questionnaires,
                status__in=['SUBMITTED', 'RATED']
            ).aggregate(avg=Avg('score'))['avg'] or 0

            labels.append(f"Session {session.session_number}")
            data.append(round(avg_score, 2))

    elif view_type == 'session' and session_id:
        # Session-specific performance
        session = get_object_or_404(Session, id=session_id)
        questionnaires = Questionnaire.objects.filter(session=session)
        for q in questionnaires:
            avg_score = UserQuestionnaireAttempt.objects.filter(
                questionnaire=q,
                status__in=['SUBMITTED', 'RATED']
            ).aggregate(avg=Avg('score'))['avg'] or 0

            labels.append(q.get_test_type_display())
            data.append(round(avg_score, 2))

    elif view_type == 'prepost':
        # Pre vs Post comparison across all sessions
        if session_id:
            sessions = [get_object_or_404(Session, id=session_id)]
        elif camp_id:
            camp = get_object_or_404(Camp, id=camp_id)
            sessions = Session.objects.filter(camp=camp).order_by('session_number')
        else:
            camps = Camp.objects.filter(batch=batch).order_by('camp_number')
            sessions = Session.objects.filter(camp__in=camps).order_by('camp__camp_number', 'session_number')

        pre_data = []
        post_data = []

        for session in sessions:
            # Pre-test average
            pre_q = Questionnaire.objects.filter(session=session, test_type='PRE')
            pre_avg = UserQuestionnaireAttempt.objects.filter(
                questionnaire__in=pre_q,
                status__in=['SUBMITTED', 'RATED']
            ).aggregate(avg=Avg('score'))['avg'] or 0

            # Post-test average
            post_q = Questionnaire.objects.filter(session=session, test_type='POST')
            post_avg = UserQuestionnaireAttempt.objects.filter(
                questionnaire__in=post_q,
                status__in=['SUBMITTED', 'RATED']
            ).aggregate(avg=Avg('score'))['avg'] or 0

            labels.append(f"C{session.camp.camp_number}-S{session.session_number}")
            pre_data.append(round(pre_avg, 2))
            post_data.append(round(post_avg, 2))

        return JsonResponse({
            'labels': labels,
            'datasets': [
                {
                    'label': 'Pre-Test',
                    'data': pre_data,
                    'backgroundColor': 'rgba(255, 159, 64, 0.6)',
                    'borderColor': 'rgb(255, 159, 64)',
                    'borderWidth': 2
                },
                {
                    'label': 'Post-Test',
                    'data': post_data,
                    'backgroundColor': 'rgba(75, 192, 192, 0.6)',
                    'borderColor': 'rgb(75, 192, 192)',
                    'borderWidth': 2
                }
            ]
        })

    return JsonResponse({
        'labels': labels,
        'datasets': [{
            'label': 'Average Score',
            'data': data,
            'backgroundColor': 'rgba(59, 130, 246, 0.5)',
            'borderColor': 'rgb(59, 130, 246)',
            'borderWidth': 2,
            'fill': True
        }]
    })


@login_required
def student_comparison_data(request, batch_id):
    """
    Returns data for comparing students across different metrics
    """
    if not request.user.is_admin_role():
        return JsonResponse({'error': 'Permission denied'}, status=403)

    batch = get_object_or_404(Batch, id=batch_id)
    batch_users = UserBatch.objects.filter(batch=batch).select_related('user')[:10]  # Top 10 students

    labels = []
    datasets = []
    colors = [
        'rgba(59, 130, 246, 0.6)',   # Blue
        'rgba(16, 185, 129, 0.6)',   # Green
        'rgba(239, 68, 68, 0.6)',    # Red
        'rgba(245, 158, 11, 0.6)',   # Orange
        'rgba(139, 92, 246, 0.6)',   # Purple
        'rgba(236, 72, 153, 0.6)',   # Pink
        'rgba(14, 165, 233, 0.6)',   # Cyan
        'rgba(234, 179, 8, 0.6)',    # Yellow
        'rgba(168, 85, 247, 0.6)',   # Violet
        'rgba(34, 197, 94, 0.6)',    # Lime
    ]

    # Get all camps for this batch
    camps = Camp.objects.filter(batch=batch).order_by('camp_number')[:5]  # First 5 camps
    labels = [f"Camp {camp.camp_number}" for camp in camps]

    for idx, ub in enumerate(batch_users):
        user = ub.user
        student_data = []

        for camp in camps:
            sessions = Session.objects.filter(camp=camp)
            questionnaires = Questionnaire.objects.filter(session__in=sessions)
            avg_score = UserQuestionnaireAttempt.objects.filter(
                user=user,
                questionnaire__in=questionnaires,
                status__in=['SUBMITTED', 'RATED']
            ).aggregate(avg=Avg('score'))['avg'] or 0

            student_data.append(round(avg_score, 2))

        datasets.append({
            'label': user.get_full_name(),
            'data': student_data,
            'backgroundColor': colors[idx % len(colors)],
            'borderColor': colors[idx % len(colors)].replace('0.6', '1'),
            'borderWidth': 2
        })

    return JsonResponse({
        'labels': labels,
        'datasets': datasets
    })


@login_required
def prepost_comparison_data(request, batch_id):
    """
    Returns pre-test vs post-test comparison data with improvement metrics
    """
    if not request.user.is_admin_role():
        return JsonResponse({'error': 'Permission denied'}, status=403)

    batch = get_object_or_404(Batch, id=batch_id)
    batch_users = UserBatch.objects.filter(batch=batch).select_related('user')

    labels = []
    pre_data = []
    post_data = []
    improvements = []

    for ub in batch_users[:10]:  # Top 10 students
        user = ub.user

        # Pre-test average
        pre_attempts = UserQuestionnaireAttempt.objects.filter(
            user=user,
            questionnaire__test_type='PRE',
            status__in=['SUBMITTED', 'RATED']
        )
        pre_avg = pre_attempts.aggregate(avg=Avg('score'))['avg'] or 0

        # Post-test average
        post_attempts = UserQuestionnaireAttempt.objects.filter(
            user=user,
            questionnaire__test_type='POST',
            status__in=['SUBMITTED', 'RATED']
        )
        post_avg = post_attempts.aggregate(avg=Avg('score'))['avg'] or 0

        if pre_avg > 0 or post_avg > 0:  # Only include students with data
            labels.append(user.get_full_name()[:15])
            pre_data.append(round(pre_avg, 2))
            post_data.append(round(post_avg, 2))
            improvements.append(round(post_avg - pre_avg, 2))

    # Calculate average improvement
    avg_improvement = sum(improvements) / len(improvements) if improvements else 0

    # Find top performer
    top_performer = None
    if improvements:
        max_improvement_idx = improvements.index(max(improvements))
        top_performer = {
            'name': labels[max_improvement_idx],
            'improvement': improvements[max_improvement_idx]
        }

    return JsonResponse({
        'chartData': {
            'labels': labels,
            'datasets': [
                {
                    'label': 'Pre-Test Average',
                    'data': pre_data,
                    'backgroundColor': 'rgba(255, 159, 64, 0.7)',
                    'borderColor': 'rgb(255, 159, 64)',
                    'borderWidth': 2
                },
                {
                    'label': 'Post-Test Average',
                    'data': post_data,
                    'backgroundColor': 'rgba(75, 192, 192, 0.7)',
                    'borderColor': 'rgb(75, 192, 192)',
                    'borderWidth': 2
                }
            ]
        },
        'avgImprovement': round(avg_improvement, 2),
        'topPerformer': top_performer
    })


@login_required
def user_progress_chart_data(request, user_id):
    """User's individual progress chart data"""
    if not request.user.is_admin_role() and request.user.id != user_id:
        return JsonResponse({'error': 'Permission denied'}, status=403)

    user = get_object_or_404(User, id=user_id)
    attempts = UserQuestionnaireAttempt.objects.filter(
        user=user,
        status__in=['SUBMITTED', 'RATED']
    ).order_by('started_at')

    labels = []
    scores = []

    for idx, attempt in enumerate(attempts, 1):
        labels.append(f"Test {idx}")
        scores.append(attempt.score or 0)

    return JsonResponse({
        'labels': labels,
        'datasets': [{
            'label': 'Score',
            'data': scores,
            'backgroundColor': 'rgba(16, 185, 129, 0.5)',
            'borderColor': 'rgb(16, 185, 129)',
            'borderWidth': 2,
            'fill': True
        }]
    })


@login_required
def get_camp_sessions(request, camp_id):
    """
    AJAX endpoint to get sessions for a specific camp
    """
    if not request.user.is_admin_role():
        return JsonResponse({'error': 'Permission denied'}, status=403)

    sessions = Session.objects.filter(camp_id=camp_id).order_by('session_number').values('id', 'session_number', 'title')
    return JsonResponse(list(sessions), safe=False)