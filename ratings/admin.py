# ratings/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import Rating


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display   = ['rated_by', 'rated_item', 'batch_label',
                      'score_stars', 'comment_preview', 'created_at']
    list_filter    = ['score',
                      ('created_at', admin.DateFieldListFilter),
                      'rated_by']
    search_fields  = ['rated_by__username', 'rated_by__first_name', 'comment']
    readonly_fields = ['created_at', 'updated_at']
    ordering       = ['-created_at']
    list_per_page  = 30
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Rating', {
            'fields': ('rated_by', 'score', 'comment')
        }),
        ('Linked Item', {
            'fields': ('questionnaire_attempt', 'media_submission'),
            'description': 'One of these should be set — not both.'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def rated_item(self, obj):
        if obj.questionnaire_attempt:
            return format_html(
                '<span style="font-size:12px;">📋 {}</span>',
                obj.questionnaire_attempt.questionnaire.title[:50]
            )
        if obj.media_submission:
            return format_html(
                '<span style="font-size:12px;">🎥 {}</span>',
                obj.media_submission.title[:50]
            )
        return format_html('<span style="color:#94a3b8;">—</span>')
    rated_item.short_description = 'Rated Item'

    def batch_label(self, obj):
        batch = None
        if obj.questionnaire_attempt:
            q = obj.questionnaire_attempt.questionnaire
            if q.session:        batch = q.session.camp.batch.name
            elif q.batch:        batch = q.batch.name
            elif q.intercamp_activity: batch = q.intercamp_activity.batch.name
        elif obj.media_submission:
            batch = obj.media_submission.intercamp_activity.batch.name
        return format_html(
            '<span style="font-size:11px;color:#6366f1;">{}</span>',
            batch or '—'
        )
    batch_label.short_description = 'Batch'

    def score_stars(self, obj):
        if obj.score is None:
            return format_html('<span style="color:#94a3b8;">—</span>')
        filled  = '★' * int(obj.score)
        empty   = '☆' * (5 - int(obj.score))
        colour  = '#166534' if obj.score >= 4 else ('#92400e' if obj.score >= 2 else '#991b1b')
        return format_html(
            '<span style="color:{};font-size:16px;letter-spacing:1px;">{}</span>'
            '<span style="color:#cbd5e1;font-size:16px;">{}</span>'
            '<span style="color:#94a3b8;font-size:11px;margin-left:4px;">({})</span>',
            colour, filled, empty, obj.score
        )
    score_stars.short_description = 'Score'

    def comment_preview(self, obj):
        if obj.comment:
            return obj.comment[:80] + ('…' if len(obj.comment) > 80 else '')
        return format_html('<span style="color:#cbd5e1;font-size:11px;">No comment</span>')
    comment_preview.short_description = 'Comment'