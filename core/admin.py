# core/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import (
    CampLocation, ApplicationForm, ApplicationAnswer,
    InterviewStatus, Batch, Camp, Session, IntercampActivity,
    MediaSubmission, UserBatch, ProgressTracking,
    FormSection, FormQuestion, FormQuestionOption,
    ApplicationDraft,
)


# ──────────────────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────────────────

def pill(text, bg, fg):
    return format_html(
        '<span style="background:{};color:{};padding:2px 10px;'
        'border-radius:12px;font-size:12px;font-weight:600;">{}</span>',
        bg, fg, text
    )


STATUS_COLOURS = {
    'PENDING':   ('#fefce8', '#92400e'),
    'APPROVED':  ('#f0fdf4', '#166534'),
    'REJECTED':  ('#fef2f2', '#991b1b'),
    'SCHEDULED': ('#eff6ff', '#1d4ed8'),
    'PASSED':    ('#f0fdf4', '#166534'),
    'FAILED':    ('#fef2f2', '#991b1b'),
}


# ──────────────────────────────────────────────────────────
# DYNAMIC FORM BUILDER
# ──────────────────────────────────────────────────────────

class FormQuestionOptionInline(admin.TabularInline):
    model = FormQuestionOption
    extra = 3
    fields = ['order', 'option_en', 'option_hi', 'is_other']
    ordering = ['order']


class FormQuestionInline(admin.StackedInline):
    model = FormQuestion
    extra = 1
    fields = [
        'order', 'question_type', 'is_required', 'is_active',
        'question_en', 'question_hi',
        'hint_en', 'hint_hi',
    ]
    ordering = ['order']
    show_change_link = True
    classes = ['collapse']


@admin.register(FormSection)
class FormSectionAdmin(admin.ModelAdmin):
    list_display = ['order', 'title_en', 'title_hi', 'question_count', 'is_active']
    list_display_links = ['title_en']          # ← add this line
    list_editable = ['order', 'is_active']
    list_per_page = 30
    ordering = ['order']
    inlines = [FormQuestionInline]

    fieldsets = (
        ('Section Title', {
            'description': 'Create section first. Then add questions inside it below.',
            'fields': (('order', 'is_active'), 'title_en', 'title_hi'),
        }),
        ('Optional Description', {
            'classes': ('collapse',),
            'fields': ('description_en', 'description_hi'),
        }),
    )

    def question_count(self, obj):
        n = obj.questions.filter(is_active=True).count()
        t = obj.questions.count()
        return format_html(
            '<b style="color:#1d4ed8;">{}</b> <span style="color:#94a3b8;">/ {} total</span>',
            n, t
        )
    question_count.short_description = 'Active Questions'


@admin.register(FormQuestion)
class FormQuestionAdmin(admin.ModelAdmin):
    list_display = [
        'section_name', 'order', 'short_question',
        'type_badge', 'option_count', 'is_required', 'is_active'
    ]
    list_filter = ['section', 'question_type', 'is_required', 'is_active']
    list_editable = ['order', 'is_required', 'is_active']
    search_fields = ['question_en', 'question_hi']
    ordering = ['section__order', 'order']
    list_per_page = 40
    inlines = [FormQuestionOptionInline]

    fieldsets = (
        ('Question Setup', {
            'fields': (
                ('section', 'order'),
                ('question_type', 'is_required', 'is_active'),
            ),
        }),
        ('English', {
            'fields': ('question_en', 'hint_en'),
        }),
        ('Hindi', {
            'fields': ('question_hi', 'hint_hi'),
        }),
    )

    def section_name(self, obj):
        return format_html(
            '<span style="font-weight:600;color:#1e40af;">[{}] {}</span>',
            obj.section.order, obj.section.title_en[:30]
        )
    section_name.short_description = 'Section'
    section_name.admin_order_field = 'section__order'

    def short_question(self, obj):
        return obj.question_en[:70] + ('…' if len(obj.question_en) > 70 else '')
    short_question.short_description = 'Question'

    def type_badge(self, obj):
        colours = {
            'TEXT':     ('#f8fafc', '#475569'),
            'TEXTAREA': ('#fefce8', '#92400e'),
            'SINGLE':   ('#eff6ff', '#1d4ed8'),
            'MULTI':    ('#f5f3ff', '#6d28d9'),
            'SELECT':   ('#ecfdf5', '#065f46'),
            'DATE':     ('#fff7ed', '#c2410c'),
            'NUMBER':   ('#fdf4ff', '#7e22ce'),
            'EMAIL':    ('#f0f9ff', '#0369a1'),
            'PHONE':    ('#f0fdf4', '#166534'),
        }
        bg, fg = colours.get(obj.question_type, ('#f1f5f9', '#475569'))
        return pill(obj.get_question_type_display(), bg, fg)
    type_badge.short_description = 'Type'

    def option_count(self, obj):
        n = obj.options.count()
        if n == 0 and obj.question_type in ('SINGLE', 'MULTI', 'SELECT'):
            return format_html('<span style="color:#dc2626;font-weight:700;">⚠ 0 options</span>')
        return format_html('<b style="color:#6d28d9;">{}</b>', n) if n else '—'
    option_count.short_description = 'Options'


@admin.register(FormQuestionOption)
class FormQuestionOptionAdmin(admin.ModelAdmin):
    list_display = ['question_short', 'order', 'option_en', 'option_hi', 'is_other']
    list_filter = ['is_other', 'question__question_type', 'question__section']
    list_editable = ['order', 'is_other']
    search_fields = ['option_en', 'option_hi', 'question__question_en']
    ordering = ['question__section__order', 'question__order', 'order']
    list_per_page = 50

    def question_short(self, obj):
        return obj.question.question_en[:60]
    question_short.short_description = 'Question'


# ──────────────────────────────────────────────────────────
# APPLICATION ANSWERS INLINE
# ──────────────────────────────────────────────────────────

class ApplicationAnswerInline(admin.TabularInline):
    model = ApplicationAnswer
    extra = 0
    can_delete = False
    fields = ['question_label', 'answer_preview']
    readonly_fields = ['question_label', 'answer_preview']

    def has_add_permission(self, request, obj=None):
        return False

    def question_label(self, obj):
        return format_html(
            '<span style="font-weight:600;font-size:12px;color:#1e40af;">[S{} Q{}]</span> {}',
            obj.question.section.order,
            obj.question.order,
            obj.question.question_en[:80],
        )
    question_label.short_description = 'Question'

    def answer_preview(self, obj):
        if obj.answer_text:
            text = obj.answer_text[:200] + ('…' if len(obj.answer_text) > 200 else '')
            return format_html('<span style="white-space:pre-wrap;">{}</span>', text)

        opts = obj.get_selected_options()
        if opts:
            labels = []
            for pk in opts:
                try:
                    o = FormQuestionOption.objects.get(pk=pk)
                    labels.append(o.option_en)
                except FormQuestionOption.DoesNotExist:
                    labels.append(f'#{pk}')
            text = ' | '.join(labels)
            if obj.other_text:
                text += f'  →  Other: {obj.other_text}'
            return text

        return format_html('<span style="color:#94a3b8;">—</span>')
    answer_preview.short_description = 'Answer'


# ──────────────────────────────────────────────────────────
# CAMP LOCATION
# ──────────────────────────────────────────────────────────

@admin.register(CampLocation)
class CampLocationAdmin(admin.ModelAdmin):
    list_display = ['name', 'state_badge', 'city', 'capacity',
                    'applicant_count', 'camp_count', 'is_active']
    list_filter = ['state', 'is_active']
    list_editable = ['is_active']
    search_fields = ['name', 'city']
    ordering = ['state', 'city']
    list_per_page = 25

    fieldsets = (
        ('Location Details', {'fields': ('name', 'state', 'city', 'address')}),
        ('Settings', {'fields': ('capacity', 'is_active')}),
    )

    def state_badge(self, obj):
        return pill(obj.get_state_display(), '#eff6ff', '#1d4ed8')
    state_badge.short_description = 'State'

    def applicant_count(self, obj):
        n = obj.applicants.count()
        return format_html('<b style="color:#1d4ed8;">{}</b>', n)
    applicant_count.short_description = '# Applicants'

    def camp_count(self, obj):
        n = obj.camps.count()
        return format_html('<b style="color:#0369a1;">{}</b>', n)
    camp_count.short_description = '# Camps'


# ──────────────────────────────────────────────────────────
# APPLICATION FORM
# ──────────────────────────────────────────────────────────

@admin.register(ApplicationForm)
class ApplicationFormAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'phone',
                    'location_badge', 'status_badge',
                    'submitted_at', 'reviewed_by', 'quick_review_link']
    list_filter = ['status',
                   'preferred_location__state',
                   'preferred_location',
                   ('submitted_at', admin.DateFieldListFilter)]
    search_fields = ['full_name', 'email', 'user__username', 'phone']
    readonly_fields = ['submitted_at', 'user']
    ordering = ['-submitted_at']
    list_per_page = 25
    date_hierarchy = 'submitted_at'
    inlines = [ApplicationAnswerInline]

    fieldsets = (
        ('Applicant', {
            'fields': ('user', 'full_name', 'email', 'phone', 'address')
        }),
        ('Application', {
            'fields': ('qualification', 'preferred_location', 'why_join', 'experience')
        }),
        ('Review', {
            'fields': ('status', 'admin_notes', 'reviewed_by', 'reviewed_at'),
            'description': 'Change status here to Approve or Reject.'
        }),
        ('Meta', {
            'fields': ('submitted_at',),
            'classes': ('collapse',)
        }),
    )

    actions = ['bulk_approve', 'bulk_reject']

    def bulk_approve(self, request, qs):
        updated = qs.filter(status='PENDING').update(
            status='APPROVED', reviewed_by=request.user, reviewed_at=timezone.now()
        )
        self.message_user(request, f"{updated} application(s) approved.")
    bulk_approve.short_description = "✓ Approve selected applications"

    def bulk_reject(self, request, qs):
        updated = qs.filter(status='PENDING').update(
            status='REJECTED', reviewed_by=request.user, reviewed_at=timezone.now()
        )
        self.message_user(request, f"{updated} application(s) rejected.")
    bulk_reject.short_description = "✗ Reject selected applications"

    def location_badge(self, obj):
        if obj.preferred_location:
            return pill(
                f"{obj.preferred_location.city}, {obj.preferred_location.get_state_display()}",
                '#f0fdf4', '#166534'
            )
        return format_html('<span style="color:#94a3b8;">—</span>')
    location_badge.short_description = 'Location'

    def status_badge(self, obj):
        bg, fg = STATUS_COLOURS.get(obj.status, ('#f1f5f9', '#475569'))
        return pill(obj.get_status_display(), bg, fg)
    status_badge.short_description = 'Status'

    def quick_review_link(self, obj):
        from django.urls import reverse
        url = reverse('admin:core_applicationform_change', args=[obj.pk])
        return format_html(
            '<a href="{}" style="color:#1d4ed8;font-size:12px;font-weight:600;">Review →</a>',
            url
        )
    quick_review_link.short_description = ''


# ──────────────────────────────────────────────────────────
# INTERVIEW STATUS
# ──────────────────────────────────────────────────────────

@admin.register(InterviewStatus)
class InterviewStatusAdmin(admin.ModelAdmin):
    list_display = ['user', 'status_badge', 'interview_date',
                    'score', 'interviewer', 'notes_preview']
    list_filter = ['status',
                   ('interview_date', admin.DateFieldListFilter),
                   'interviewer']
    search_fields = ['user__username', 'user__email', 'user__first_name']
    ordering = ['-interview_date']
    list_per_page = 25
    date_hierarchy = 'interview_date'

    fieldsets = (
        ('Candidate', {'fields': ('user',)}),
        ('Interview', {'fields': ('interview_date', 'interviewer', 'status', 'score')}),
        ('Notes', {'fields': ('notes',)}),
    )

    actions = ['mark_passed', 'mark_failed']

    def mark_passed(self, request, qs):
        qs.update(status='PASSED')
        self.message_user(request, f"{qs.count()} candidate(s) marked as Passed.")
    mark_passed.short_description = "✓ Mark selected as Passed"

    def mark_failed(self, request, qs):
        qs.update(status='FAILED')
        self.message_user(request, f"{qs.count()} candidate(s) marked as Failed.")
    mark_failed.short_description = "✗ Mark selected as Failed"

    def status_badge(self, obj):
        bg, fg = STATUS_COLOURS.get(obj.status, ('#f1f5f9', '#475569'))
        return pill(obj.get_status_display(), bg, fg)
    status_badge.short_description = 'Result'

    def notes_preview(self, obj):
        if obj.notes:
            return obj.notes[:60] + ('…' if len(obj.notes) > 60 else '')
        return format_html('<span style="color:#cbd5e1;">—</span>')
    notes_preview.short_description = 'Notes'


# ──────────────────────────────────────────────────────────
# BATCH
# ──────────────────────────────────────────────────────────

class SessionInline(admin.TabularInline):
    model = Session
    extra = 0
    fields = ['session_number', 'title', 'session_date', 'is_active']
    ordering = ['session_number']
    show_change_link = True


class CampInline(admin.TabularInline):
    model = Camp
    extra = 0
    fields = ['camp_number', 'location', 'start_date', 'end_date', 'is_active']
    show_change_link = True


@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ['name', 'start_date', 'end_date',
                    'volunteer_count', 'camp_count', 'is_active']
    list_filter = ['is_active', ('start_date', admin.DateFieldListFilter)]
    list_editable = ['is_active']
    search_fields = ['name', 'description']
    ordering = ['-start_date']
    list_per_page = 20
    inlines = [CampInline]

    fieldsets = (
        ('Batch Details', {'fields': ('name', 'description', 'created_by')}),
        ('Schedule', {'fields': ('start_date', 'end_date', 'is_active')}),
    )

    def volunteer_count(self, obj):
        n = obj.batch_users.filter(is_active=True).count()
        return format_html('<b style="color:#1d4ed8;">{}</b> volunteers', n)
    volunteer_count.short_description = 'Volunteers'

    def camp_count(self, obj):
        n = obj.camps.count()
        return format_html('<b>{}</b> camps', n)
    camp_count.short_description = 'Camps'


# ──────────────────────────────────────────────────────────
# CAMP
# ──────────────────────────────────────────────────────────

@admin.register(Camp)
class CampAdmin(admin.ModelAdmin):
    list_display = ['batch', 'camp_number', 'location_badge',
                    'start_date', 'end_date', 'session_count', 'is_active']
    list_filter = ['batch', 'camp_number', 'location__state', 'location', 'is_active']
    list_editable = ['is_active']
    search_fields = ['batch__name', 'location__name', 'location__city']
    ordering = ['batch', 'camp_number']
    list_per_page = 25
    list_select_related = ['batch', 'location']
    inlines = [SessionInline]

    fieldsets = (
        ('Camp', {'fields': ('batch', 'camp_number', 'location')}),
        ('Schedule', {'fields': ('start_date', 'end_date', 'is_active')}),
    )

    def location_badge(self, obj):
        if obj.location:
            return pill(
                f"{obj.location.city} — {obj.location.get_state_display()}",
                '#eff6ff', '#1e40af'
            )
        return format_html('<span style="color:#fca5a5;font-weight:600;">⚠ No Location</span>')
    location_badge.short_description = 'Location'

    def session_count(self, obj):
        n = obj.sessions.count()
        return format_html('<b>{}</b> sessions', n)
    session_count.short_description = 'Sessions'


# ──────────────────────────────────────────────────────────
# SESSION
# ──────────────────────────────────────────────────────────

@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ['camp_batch', 'camp', 'session_number',
                    'title', 'session_date', 'questionnaire_count', 'is_active']
    list_filter = ['camp__batch', 'camp', 'is_active',
                   ('session_date', admin.DateFieldListFilter)]
    list_editable = ['is_active']
    search_fields = ['title', 'camp__batch__name']
    ordering = ['camp__batch', 'camp__camp_number', 'session_number']
    list_per_page = 30

    fieldsets = (
        ('Session', {'fields': ('camp', 'session_number', 'title', 'description')}),
        ('Schedule', {'fields': ('session_date', 'is_active')}),
    )

    def camp_batch(self, obj):
        return obj.camp.batch.name
    camp_batch.short_description = 'Batch'
    camp_batch.admin_order_field = 'camp__batch__name'

    def questionnaire_count(self, obj):
        n = obj.questionnaires.count()
        return format_html('<span style="color:#6366f1;font-weight:600;">{} Q</span>', n)
    questionnaire_count.short_description = 'Tests'


# ──────────────────────────────────────────────────────────
# INTERCAMP ACTIVITY
# ──────────────────────────────────────────────────────────

@admin.register(IntercampActivity)
class IntercampActivityAdmin(admin.ModelAdmin):
    list_display = ['batch', 'after_camp', 'title',
                    'start_date', 'end_date', 'submission_count', 'is_active']
    list_filter = ['batch', 'after_camp', 'is_active']
    list_editable = ['is_active']
    search_fields = ['title', 'batch__name']
    ordering = ['batch', 'after_camp']
    list_per_page = 20

    def submission_count(self, obj):
        n = obj.submissions.count()
        pending = obj.submissions.filter(status='PENDING').count()
        if pending:
            return format_html(
                '<b style="color:#1d4ed8;">{}</b> total '
                '<span style="color:#92400e;font-weight:600;">({} pending)</span>',
                n, pending
            )
        return format_html('<b style="color:#166534;">{}</b> total', n)
    submission_count.short_description = 'Submissions'


# ──────────────────────────────────────────────────────────
# MEDIA SUBMISSION
# ──────────────────────────────────────────────────────────

@admin.register(MediaSubmission)
class MediaSubmissionAdmin(admin.ModelAdmin):
    list_display = ['user', 'activity_batch', 'intercamp_activity',
                    'title', 'status_badge', 'submitted_at',
                    'reviewed_by', 'file_link', 'quick_review_link']
    list_filter = ['status',
                   'intercamp_activity__batch',
                   'intercamp_activity',
                   ('submitted_at', admin.DateFieldListFilter)]
    search_fields = ['user__username', 'user__first_name', 'title']
    ordering = ['-submitted_at']
    list_per_page = 30
    date_hierarchy = 'submitted_at'
    readonly_fields = ['submitted_at']

    fieldsets = (
        ('Submission', {
            'fields': ('user', 'intercamp_activity', 'title', 'description', 'file')
        }),
        ('Review', {
            'fields': ('status', 'reviewed_by', 'reviewed_at'),
            'description': 'Set status to Approved or Rejected after reviewing the file.'
        }),
    )

    actions = ['bulk_approve', 'bulk_reject']

    def bulk_approve(self, request, qs):
        updated = qs.filter(status='PENDING').update(
            status='APPROVED', reviewed_by=request.user, reviewed_at=timezone.now()
        )
        self.message_user(request, f"{updated} submission(s) approved.")
    bulk_approve.short_description = "✓ Approve selected submissions"

    def bulk_reject(self, request, qs):
        updated = qs.filter(status='PENDING').update(
            status='REJECTED', reviewed_by=request.user, reviewed_at=timezone.now()
        )
        self.message_user(request, f"{updated} submission(s) rejected.")
    bulk_reject.short_description = "✗ Reject selected submissions"

    def activity_batch(self, obj):
        return obj.intercamp_activity.batch.name
    activity_batch.short_description = 'Batch'
    activity_batch.admin_order_field = 'intercamp_activity__batch__name'

    def status_badge(self, obj):
        bg, fg = STATUS_COLOURS.get(obj.status, ('#f1f5f9', '#475569'))
        return pill(obj.get_status_display(), bg, fg)
    status_badge.short_description = 'Status'

    def file_link(self, obj):
        if obj.file:
            return format_html(
                '<a href="{}" target="_blank" '
                'style="color:#1d4ed8;font-weight:600;font-size:12px;">View ↗</a>',
                obj.file.url
            )
        return format_html('<span style="color:#94a3b8;">—</span>')
    file_link.short_description = 'File'

    def quick_review_link(self, obj):
        from django.urls import reverse
        url = reverse('admin:core_mediasubmission_change', args=[obj.pk])
        return format_html(
            '<a href="{}" style="color:#7c3aed;font-size:12px;font-weight:600;">Review →</a>',
            url
        )
    quick_review_link.short_description = ''


# ──────────────────────────────────────────────────────────
# USER BATCH
# ──────────────────────────────────────────────────────────

@admin.register(UserBatch)
class UserBatchAdmin(admin.ModelAdmin):
    list_display = ['user', 'batch', 'location_info',
                    'stage_badge', 'enrolled_at', 'is_active']
    list_filter = ['batch', 'current_camp', 'is_active',
                   'batch__camps__location__state']
    list_editable = ['is_active']
    search_fields = ['user__username', 'user__first_name',
                     'user__email', 'batch__name']
    ordering = ['-enrolled_at']
    list_per_page = 30
    date_hierarchy = 'enrolled_at'

    fieldsets = (
        ('Assignment', {'fields': ('user', 'batch', 'current_camp', 'is_active')}),
    )

    actions = ['advance_stage']

    def advance_stage(self, request, qs):
        for ub in qs.filter(current_camp__lt=5):
            ub.current_camp += 1
            ub.save()
        self.message_user(request, f"{qs.count()} volunteer(s) advanced one stage.")
    advance_stage.short_description = "→ Advance selected volunteers one stage"

    def location_info(self, obj):
        camp = obj.batch.camps.filter(
            camp_number=obj.current_camp
        ).select_related('location').first()
        if camp and camp.location:
            return format_html(
                '<span style="font-size:11px;color:#1e40af;">{}</span>',
                camp.location.city
            )
        return format_html('<span style="color:#cbd5e1;font-size:11px;">—</span>')
    location_info.short_description = 'Current City'

    def stage_badge(self, obj):
        stages = {
            0: ('Pre-Camp', '#eff6ff', '#1e40af'),
            1: ('Camp 1', '#f0fdf4', '#166534'),
            2: ('Camp 2', '#fefce8', '#92400e'),
            3: ('Camp 3', '#fdf4ff', '#7e22ce'),
            4: ('Post-Camp', '#fff7ed', '#c2410c'),
            5: ('Completed', '#f0fdf4', '#14532d'),
        }
        label, bg, fg = stages.get(obj.current_camp, ('Unknown', '#f1f5f9', '#475569'))
        return pill(label, bg, fg)
    stage_badge.short_description = 'Stage'


# ──────────────────────────────────────────────────────────
# PROGRESS TRACKING
# ──────────────────────────────────────────────────────────

@admin.register(ProgressTracking)
class ProgressTrackingAdmin(admin.ModelAdmin):
    list_display = ['user', 'batch', 'stage', 'status_badge',
                    'started_at', 'completed_at']
    list_filter = ['batch', 'status', 'stage']
    search_fields = ['user__username', 'user__first_name', 'batch__name']
    ordering = ['user', 'batch', 'started_at']
    list_per_page = 40

    def status_badge(self, obj):
        colours = {
            'not-started': ('#f1f5f9', '#475569'),
            'in-progress': ('#eff6ff', '#1d4ed8'),
            'completed': ('#f0fdf4', '#166534'),
        }
        bg, fg = colours.get(obj.status, ('#f1f5f9', '#475569'))
        return pill(obj.status.replace('-', ' ').title(), bg, fg)
    status_badge.short_description = 'Status'


# ──────────────────────────────────────────────────────────
# APPLICATION DRAFT
# ──────────────────────────────────────────────────────────

@admin.register(ApplicationDraft)
class ApplicationDraftAdmin(admin.ModelAdmin):
    list_display = ['user', 'preferred_location', 'language', 'last_step', 'last_saved']
    list_filter = ['language', 'preferred_location__state']
    search_fields = ['user__username', 'user__email']
    ordering = ['-last_saved']
    readonly_fields = ['user', 'last_saved', 'created_at', 'answers_preview']
    list_per_page = 30

    fieldsets = (
        ('Draft Info', {
            'fields': ('user', 'preferred_location', 'language', 'last_step', 'last_saved', 'created_at')
        }),
        ('Saved Answers (Preview)', {
            'fields': ('answers_preview',),
            'classes': ('collapse',)
        }),
    )

    def has_add_permission(self, request):
        return False

    def answers_preview(self, obj):
        import json
        try:
            data = obj.get_answers()
            pretty = json.dumps(data, indent=2, ensure_ascii=False)
            return format_html('<pre style="font-size:11px;max-height:300px;overflow:auto;">{}</pre>', pretty)
        except Exception:
            return obj._answers
    answers_preview.short_description = 'Answers'