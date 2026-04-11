# questionnaires/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import Questionnaire, Question, Option, UserQuestionnaireAttempt, UserResponse


def pill(text, bg, fg):
    return format_html(
        '<span style="background:{};color:{};padding:2px 10px;'
        'border-radius:12px;font-size:12px;font-weight:600;">{}</span>',
        bg, fg, text
    )


# ──────────────────────────────────────────────────────────
#  INLINES
# ──────────────────────────────────────────────────────────

class OptionInline(admin.TabularInline):
    model  = Option
    extra  = 4
    fields = ['option_text', 'option_image', 'is_correct', 'order']


class QuestionInline(admin.StackedInline):
    model            = Question
    extra            = 1
    fields           = ['question_type', 'question_text', 'question_image', 'marks', 'order']
    show_change_link = True  # click through to see options


class UserResponseInline(admin.TabularInline):
    model         = UserResponse
    extra         = 0
    readonly_fields = ['question', 'selected_option', 'text_response',
                       'is_correct', 'marks_obtained', 'answered_at']
    can_delete    = False
    fields        = ['question', 'selected_option', 'text_response',
                     'is_correct', 'marks_obtained']

    def has_add_permission(self, request, obj=None):
        return False


# ──────────────────────────────────────────────────────────
#  QUESTIONNAIRE
# ──────────────────────────────────────────────────────────

@admin.register(Questionnaire)
class QuestionnaireAdmin(admin.ModelAdmin):
    list_display   = ['title', 'type_badge', 'context_label',
                      'question_count', 'attempt_count',
                      'is_active', 'is_published', 'created_at']
    list_filter    = ['test_type', 'is_active', 'is_published',
                      'session__camp__batch', 'batch']
    list_editable  = ['is_active', 'is_published']
    search_fields  = ['title', 'description']
    ordering       = ['-created_at']
    list_per_page  = 25
    inlines        = [QuestionInline]

    fieldsets = (
        ('Questionnaire', {
            'fields': ('title', 'description', 'test_type', 'created_by')
        }),
        ('Linked To', {
            'fields': ('batch', 'session', 'intercamp_activity'),
            'description': 'Link this test to a Batch, Session, OR Intercamp Activity — not all three.'
        }),
        ('Settings', {
            'fields': ('time_limit_minutes', 'allow_multiple_attempts',
                       'is_active', 'is_published')
        }),
        ('Open / Close Window', {
            'fields': ('open_date', 'close_date'),
            'classes': ('collapse',)
        }),
    )

    actions = ['publish_all', 'unpublish_all']

    def publish_all(self, request, qs):
        qs.update(is_published=True, is_active=True)
        self.message_user(request, f"{qs.count()} questionnaire(s) published.")
    publish_all.short_description = "✓ Publish & activate selected"

    def unpublish_all(self, request, qs):
        qs.update(is_published=False, is_active=False)
        self.message_user(request, f"{qs.count()} questionnaire(s) unpublished.")
    unpublish_all.short_description = "✗ Unpublish & deactivate selected"

    def type_badge(self, obj):
        colours = {
            'PRE':       ('#eff6ff', '#1e40af'),
            'POST':      ('#f0fdf4', '#166534'),
            'PRE_CAMP':  ('#fdf4ff', '#7e22ce'),
            'POST_CAMP': ('#fff7ed', '#c2410c'),
            'INTERCAMP': ('#fefce8', '#92400e'),
        }
        bg, fg = colours.get(obj.test_type, ('#f1f5f9', '#475569'))
        return pill(obj.get_test_type_display(), bg, fg)
    type_badge.short_description = 'Type'

    def context_label(self, obj):
        if obj.session:
            return format_html(
                '<span style="font-size:11px;">📋 {}</span>',
                str(obj.session)
            )
        if obj.intercamp_activity:
            return format_html(
                '<span style="font-size:11px;">🏕 {}</span>',
                str(obj.intercamp_activity)
            )
        if obj.batch:
            return format_html(
                '<span style="font-size:11px;">📦 {}</span>',
                obj.batch.name
            )
        return format_html('<span style="color:#94a3b8;font-size:11px;">—</span>')
    context_label.short_description = 'Linked To'

    def question_count(self, obj):
        n = obj.questions.count()
        return format_html('<b style="color:#6366f1;">{}</b> Qs', n)
    question_count.short_description = 'Questions'

    def attempt_count(self, obj):
        n       = obj.attempts.count()
        pending = obj.attempts.filter(status='IN_PROGRESS').count()
        submitted = obj.attempts.filter(status='SUBMITTED').count()
        if pending or submitted:
            return format_html(
                '<b style="color:#1d4ed8;">{}</b> total '
                '<span style="color:#92400e;font-size:11px;">({} pending rating)</span>',
                n, submitted
            )
        return format_html('<b>{}</b>', n)
    attempt_count.short_description = 'Attempts'


# ──────────────────────────────────────────────────────────
#  QUESTION
# ──────────────────────────────────────────────────────────

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display   = ['questionnaire', 'order', 'type_badge',
                      'question_preview', 'marks', 'option_count']
    list_filter    = ['question_type',
                      'questionnaire__test_type',
                      'questionnaire__session__camp__batch',
                      'questionnaire']
    search_fields  = ['question_text', 'questionnaire__title']
    ordering       = ['questionnaire', 'order']
    list_per_page  = 40
    inlines        = [OptionInline]

    def type_badge(self, obj):
        colours = {
            'MCQ':       ('#eff6ff', '#1e40af'),
            'SUBJECTIVE':('#fdf4ff', '#7e22ce'),
            'IMAGE_MCQ': ('#fff7ed', '#c2410c'),
        }
        bg, fg = colours.get(obj.question_type, ('#f1f5f9', '#475569'))
        return pill(obj.get_question_type_display(), bg, fg)
    type_badge.short_description = 'Type'

    def question_preview(self, obj):
        text = obj.question_text[:70]
        return text + ('…' if len(obj.question_text) > 70 else '')
    question_preview.short_description = 'Question'

    def option_count(self, obj):
        n       = obj.options.count()
        correct = obj.options.filter(is_correct=True).count()
        return format_html(
            '<span style="font-size:11px;">{} options, '
            '<span style="color:#166534;font-weight:600;">{} correct</span></span>',
            n, correct
        )
    option_count.short_description = 'Options'


# ──────────────────────────────────────────────────────────
#  ATTEMPT  (what the admin spends most time on)
# ──────────────────────────────────────────────────────────

@admin.register(UserQuestionnaireAttempt)
class UserQuestionnaireAttemptAdmin(admin.ModelAdmin):
    list_display   = ['user', 'batch_label', 'questionnaire',
                      'status_badge', 'score_display',
                      'time_taken_minutes', 'started_at', 'submitted_at',
                      'rate_link']
    list_filter    = ['status',
                      'questionnaire__test_type',
                      'questionnaire__session__camp__batch',
                      'questionnaire',
                      ('submitted_at', admin.DateFieldListFilter)]
    search_fields  = ['user__username', 'user__first_name',
                      'questionnaire__title']
    readonly_fields = ['started_at', 'submitted_at', 'user',
                       'questionnaire', 'time_taken_minutes']
    ordering       = ['-submitted_at']
    list_per_page  = 30
    date_hierarchy = 'submitted_at'
    inlines        = [UserResponseInline]

    fieldsets = (
        ('Attempt Info', {
            'fields': ('user', 'questionnaire', 'status',
                       'started_at', 'submitted_at', 'time_taken_minutes')
        }),
        ('Scoring', {
            'fields': ('score', 'total_marks'),
            'description': '✏️ Enter score here for subjective questions.'
        }),
    )

    actions = ['mark_rated']

    def mark_rated(self, request, qs):
        qs.filter(status='SUBMITTED').update(status='RATED')
        self.message_user(request, f"{qs.count()} attempt(s) marked as Rated.")
    mark_rated.short_description = "✓ Mark selected as Rated"

    def batch_label(self, obj):
        b = None
        if obj.questionnaire.session:
            b = obj.questionnaire.session.camp.batch.name
        elif obj.questionnaire.batch:
            b = obj.questionnaire.batch.name
        elif obj.questionnaire.intercamp_activity:
            b = obj.questionnaire.intercamp_activity.batch.name
        return format_html(
            '<span style="font-size:11px;color:#6366f1;">{}</span>',
            b or '—'
        )
    batch_label.short_description = 'Batch'

    def status_badge(self, obj):
        colours = {
            'IN_PROGRESS': ('#fefce8', '#92400e'),
            'SUBMITTED':   ('#eff6ff', '#1d4ed8'),
            'RATED':       ('#f0fdf4', '#166534'),
        }
        bg, fg = colours.get(obj.status, ('#f1f5f9', '#475569'))
        return pill(obj.get_status_display(), bg, fg)
    status_badge.short_description = 'Status'

    def score_display(self, obj):
        if obj.score is not None and obj.total_marks:
            pct = round((obj.score / obj.total_marks) * 100)
            colour = '#166534' if pct >= 60 else ('#92400e' if pct >= 40 else '#991b1b')
            return format_html(
                '<b style="color:{};">{}/{}</b> '
                '<span style="font-size:11px;color:#94a3b8;">({}%)</span>',
                colour, obj.score, obj.total_marks, pct
            )
        return format_html('<span style="color:#94a3b8;">—</span>')
    score_display.short_description = 'Score'

    def rate_link(self, obj):
        if obj.status == 'SUBMITTED':
            from django.urls import reverse
            url = reverse('admin:questionnaires_userquestionnaireatempt_change', args=[obj.pk])
            return format_html(
                '<a href="{}" style="color:#7c3aed;font-weight:600;font-size:12px;">Rate →</a>',
                url
            )
        return format_html('<span style="color:#cbd5e1;font-size:11px;">—</span>')
    rate_link.short_description = ''