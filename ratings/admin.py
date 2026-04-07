from django.contrib import admin
from .models import Rating

@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ['rated_by', 'get_rated_item', 'score', 'created_at']
    list_filter = ['score', 'created_at', 'rated_by']
    search_fields = ['rated_by__username', 'comment']
    readonly_fields = ['created_at', 'updated_at']
    
    def get_rated_item(self, obj):
        if obj.questionnaire_attempt:
            return f"Attempt: {obj.questionnaire_attempt.questionnaire.title}"
        elif obj.media_submission:
            return f"Media: {obj.media_submission.title}"
        return '-'
    get_rated_item.short_description = 'Rated Item'
