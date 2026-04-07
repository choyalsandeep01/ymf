from django.contrib import admin
from .models import Questionnaire, Question, Option, UserQuestionnaireAttempt, UserResponse

class OptionInline(admin.TabularInline):
    model = Option
    extra = 4
    fields = ['option_text', 'option_image', 'is_correct', 'order']

class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1
    fields = ['question_type', 'question_text', 'marks', 'order']

@admin.register(Questionnaire)
class QuestionnaireAdmin(admin.ModelAdmin):
    list_display = ['title', 'test_type', 'is_active', 'is_published', 'created_at']
    list_filter = ['test_type', 'is_active', 'is_published', 'created_at']
    search_fields = ['title', 'description']
    inlines = [QuestionInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'test_type')
        }),
        ('Relations', {
            'fields': ('session', 'intercamp_activity', 'batch')
        }),
        ('Settings', {
            'fields': ('time_limit_minutes', 'is_active', 'is_published', 'allow_multiple_attempts')
        }),
        ('Scheduling', {
            'fields': ('open_date', 'close_date')
        }),
    )

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['questionnaire', 'question_type', 'question_text_short', 'marks', 'order']
    list_filter = ['question_type', 'questionnaire']
    search_fields = ['question_text']
    inlines = [OptionInline]
    
    def question_text_short(self, obj):
        return obj.question_text[:50]
    question_text_short.short_description = 'Question'

@admin.register(Option)
class OptionAdmin(admin.ModelAdmin):
    list_display = ['question', 'option_text_short', 'is_correct', 'order']
    list_filter = ['is_correct', 'question__questionnaire']
    
    def option_text_short(self, obj):
        return obj.option_text[:40] if obj.option_text else 'Image Option'
    option_text_short.short_description = 'Option'

@admin.register(UserQuestionnaireAttempt)
class UserQuestionnaireAttemptAdmin(admin.ModelAdmin):
    list_display = ['user', 'questionnaire', 'status', 'score', 'total_marks', 'started_at', 'submitted_at']
    list_filter = ['status', 'questionnaire', 'started_at']
    search_fields = ['user__username', 'questionnaire__title']
    readonly_fields = ['started_at', 'submitted_at']

@admin.register(UserResponse)
class UserResponseAdmin(admin.ModelAdmin):
    list_display = ['attempt', 'question', 'is_correct', 'marks_obtained']
    list_filter = ['is_correct', 'attempt__questionnaire']
    search_fields = ['attempt__user__username']
