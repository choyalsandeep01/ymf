# core/views.py — COMPLETE FILE
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone

from .models import (
    ApplicationForm, InterviewStatus, Batch, Camp, Session,
    IntercampActivity, MediaSubmission, UserBatch, ProgressTracking,
    CampLocation, FormSection, FormQuestion, FormQuestionOption,
    ApplicationDraft, ApplicationAnswer,
)
from .forms import ApplicationFormForm, MediaSubmissionForm
from questionnaires.models import Questionnaire, UserQuestionnaireAttempt
from .decorators import batch_required


# ─────────────────────────────────────────────────────────────────────────────
# HOMEPAGE
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def homepage(request):
    user = request.user
    context = {'user': user}

    try:
        application = ApplicationForm.objects.get(user=user)
        context['application'] = application

        if application.status == 'PENDING':
            context['message'] = "Your application is under review."
        elif application.status == 'REJECTED':
            context['message'] = "Your application was not approved."
            return render(request, 'core/homepage.html', context)
        elif application.status == 'APPROVED':
            try:
                interview = InterviewStatus.objects.get(user=user)
                context['interview'] = interview
                if interview.status == 'FAILED':
                    context['message'] = "You are not selected. Thank you for your interest."
                elif interview.status == 'PASSED':
                    user_batch = UserBatch.objects.filter(user=user, is_active=True).first()
                    if user_batch:
                        context['user_batch'] = user_batch
                        context['batch'] = user_batch.batch
                        context['current_stage'] = (
                            f"Camp {user_batch.current_camp}"
                            if user_batch.current_camp > 0 else "Pre-Camp"
                        )
                    else:
                        context['message'] = "Congratulations! You passed the interview. Awaiting batch assignment."
                else:
                    context['message'] = "Your interview has been scheduled."
            except InterviewStatus.DoesNotExist:
                context['message'] = "You have been moved to the next step: Call Interview."
    except ApplicationForm.DoesNotExist:
        context['message'] = "Please complete your application form."

    return render(request, 'core/homepage.html', context)


# ─────────────────────────────────────────────────────────────────────────────
# SUBMIT APPLICATION  (multi-step dynamic form)
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def submit_application(request):
    if ApplicationForm.objects.filter(user=request.user).exists():
        messages.info(request, 'You have already submitted your application.')
        return redirect('core:homepage')

    # Load draft for resume
    draft          = ApplicationDraft.objects.filter(user=request.user).first()
    draft_answers  = draft.answers if draft else {}
    draft_location = draft.preferred_location_id if draft else None
    draft_language = draft.language if draft else 'en'
    draft_step     = draft.last_step if draft else 0

    errors = {}

    if request.method == 'POST':
        lang   = request.POST.get('language', 'en')
        loc_id = request.POST.get('preferred_location', '')
        answers = {}

        location = None
        if loc_id:
            try:
                location = CampLocation.objects.get(pk=loc_id, is_active=True)
            except CampLocation.DoesNotExist:
                errors['preferred_location'] = 'Invalid location selected.'

        questions = FormQuestion.objects.filter(
            section__is_active=True, is_active=True
        ).select_related('section').prefetch_related('options')

        for q in questions:
            key = f'q_{q.id}'
            if q.question_type in ('SINGLE', 'SELECT'):
                val       = request.POST.get(key, '')
                other_val = request.POST.get(f'{key}_other', '').strip()
                answers[str(q.id)] = {'value': val, 'other': other_val}
                if q.is_required and not val:
                    errors[key] = 'This field is required.'
            elif q.question_type == 'MULTI':
                vals      = request.POST.getlist(key)
                other_val = request.POST.get(f'{key}_other', '').strip()
                answers[str(q.id)] = {'value': vals, 'other': other_val}
                if q.is_required and not vals:
                    errors[key] = 'Please select at least one option.'
            else:
                val = request.POST.get(key, '').strip()
                answers[str(q.id)] = {'value': val, 'other': ''}
                if q.is_required and not val:
                    errors[key] = 'This field is required.'

        if not errors:
            app = ApplicationForm.objects.create(
                user               = request.user,
                full_name          = request.POST.get('full_name', '').strip(),
                email              = request.POST.get('email', request.user.email).strip(),
                phone              = request.POST.get('phone', '').strip(),
                address            = request.POST.get('address', '').strip(),
                qualification      = request.POST.get('qualification', '').strip(),
                why_join           = request.POST.get('why_join', '').strip(),
                experience         = request.POST.get('experience', '').strip(),
                preferred_location = location,
            )

            for q in questions:
                data      = answers.get(str(q.id), {})
                val       = data.get('value', '')
                other_val = data.get('other', '')

                if q.question_type in ('SINGLE', 'SELECT'):
                    sel_opts = []
                    if val:
                        try:
                            opt = FormQuestionOption.objects.get(pk=int(val))
                            sel_opts = [opt.id]
                        except (FormQuestionOption.DoesNotExist, ValueError):
                            pass
                    ans = ApplicationAnswer(
                        application=app, question=q, other_text=other_val
                    )
                    ans.set_selected_options(sel_opts)
                    ans.save()

                elif q.question_type == 'MULTI':
                    sel_opts = []
                    for v in (val if isinstance(val, list) else []):
                        try:
                            sel_opts.append(int(v))
                        except ValueError:
                            pass
                    ans = ApplicationAnswer(
                        application=app, question=q, other_text=other_val
                    )
                    ans.set_selected_options(sel_opts)
                    ans.save()

                else:
                    ApplicationAnswer.objects.create(
                        application=app, question=q,
                        answer_text=val if isinstance(val, str) else '',
                    )

            ApplicationDraft.objects.filter(user=request.user).delete()
            messages.success(request, 'Application submitted successfully! 🎉')
            return redirect('core:homepage')

    # ── Build context ─────────────────────────────────────────────────────────
    sections  = (
        FormSection.objects
        .filter(is_active=True)
        .prefetch_related('questions__options')
        .order_by('order')
    )
    locations = CampLocation.objects.filter(is_active=True).order_by('state', 'city')

    locations_json = json.dumps([
        {
            'id':       loc.id,
            'name':     loc.name,
            'state':    loc.get_state_display(),
            'city':     loc.city,
            'capacity': loc.capacity,
        }
        for loc in locations
    ])

    return render(request, 'core/submit_application.html', {
        'sections':       sections,
        'locations':      locations,
        'locations_json': locations_json,
        'draft_answers':  json.dumps(draft_answers),
        'draft_location': draft_location or '',
        'draft_language': draft_language,
        'draft_step':     draft_step,
        'errors':         errors,
    })


# ─────────────────────────────────────────────────────────────────────────────
# AUTOSAVE DRAFT  (AJAX)
# ─────────────────────────────────────────────────────────────────────────────

@login_required
@require_POST
def autosave_draft(request):
    if ApplicationForm.objects.filter(user=request.user).exists():
        return JsonResponse({'status': 'already_submitted'})

    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'detail': 'Invalid JSON'}, status=400)

    loc_id   = payload.get('preferred_location')
    location = None
    if loc_id:
        try:
            location = CampLocation.objects.get(pk=loc_id, is_active=True)
        except CampLocation.DoesNotExist:
            pass

    draft, _ = ApplicationDraft.objects.get_or_create(user=request.user)
    draft.preferred_location = location
    draft.language  = payload.get('language', 'en')
    draft.set_answers(payload.get('answers', {}))   # use helper, not property setter
    draft.last_step = payload.get('last_step', 0)
    draft.save()

    return JsonResponse({
        'status':    'saved',
        'timestamp': draft.last_saved.strftime('%H:%M:%S'),
    })


# ─────────────────────────────────────────────────────────────────────────────
# BATCH / CAMP / SESSION / INTERCAMP / MEDIA / PROGRESS
# ─────────────────────────────────────────────────────────────────────────────

@login_required
@batch_required
def batch_detail(request, batch_id):
    batch      = get_object_or_404(Batch, id=batch_id)
    user_batch = UserBatch.objects.filter(user=request.user, batch=batch).first()

    if not user_batch and not request.user.is_admin_role():
        messages.error(request, 'You are not enrolled in this batch.')
        return redirect('core:homepage')

    camps                = Camp.objects.filter(batch=batch).prefetch_related('sessions')
    intercamp_activities = IntercampActivity.objects.filter(batch=batch)

    return render(request, 'core/batch_detail.html', {
        'batch':                batch,
        'user_batch':           user_batch,
        'camps':                camps,
        'intercamp_activities': intercamp_activities,
    })


@login_required
def camp_detail(request, camp_id):
    camp     = get_object_or_404(Camp, id=camp_id)
    sessions = Session.objects.filter(camp=camp)
    return render(request, 'core/camp_detail.html', {'camp': camp, 'sessions': sessions})


@login_required
@batch_required
def session_detail(request, session_id):
    session    = get_object_or_404(Session, id=session_id)
    pre_tests  = Questionnaire.objects.filter(session=session, test_type='PRE')
    post_tests = Questionnaire.objects.filter(session=session, test_type='POST')
    return render(request, 'core/session_detail.html', {
        'session':    session,
        'pre_tests':  pre_tests,
        'post_tests': post_tests,
    })


@login_required
@batch_required
def intercamp_activity_detail(request, activity_id):
    activity         = get_object_or_404(IntercampActivity, id=activity_id)
    user_submissions = MediaSubmission.objects.filter(user=request.user, intercamp_activity=activity)
    return render(request, 'core/intercamp_activity.html', {
        'activity':         activity,
        'user_submissions': user_submissions,
    })


@login_required
@batch_required
def submit_media(request, activity_id):
    activity = get_object_or_404(IntercampActivity, id=activity_id)

    if request.method == 'POST':
        form = MediaSubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            submission                    = form.save(commit=False)
            submission.user               = request.user
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
    progress     = ProgressTracking.objects.filter(user=request.user)

    for user_batch in user_batches:
        user_batch.progress_percentage = (
            (user_batch.current_camp / 3) * 100 if user_batch.current_camp > 0 else 0
        )

    return render(request, 'core/my_progress.html', {
        'user_batches': user_batches,
        'progress':     progress,
    })
