from django.contrib import admin
from django.utils.html import format_html
from .models import (ApplicationForm, InterviewStatus, Batch, Camp, Session, 
                     IntercampActivity, MediaSubmission, UserBatch, ProgressTracking)

@admin.register(ApplicationForm)
class ApplicationFormAdmin(admin.ModelAdmin):
    list_display = ['user', 'full_name', 'email', 'status', 'submitted_at', 'reviewed_by']
    list_filter = ['status', 'submitted_at']
    search_fields = ['user__username', 'full_name', 'email']
    readonly_fields = ['submitted_at']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'full_name', 'email', 'phone', 'address')
        }),
        ('Application Details', {
            'fields': ('qualification', 'why_join', 'experience')
        }),
        ('Review Status', {
            'fields': ('status', 'reviewed_by', 'reviewed_at', 'admin_notes')
        }),
    )

@admin.register(InterviewStatus)
class InterviewStatusAdmin(admin.ModelAdmin):
    list_display = ['user', 'status', 'interview_date', 'score', 'interviewer']
    list_filter = ['status', 'interview_date']
    search_fields = ['user__username']

@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ['name', 'start_date', 'end_date', 'is_active', 'created_at']
    list_filter = ['is_active', 'start_date']
    search_fields = ['name']

@admin.register(Camp)
class CampAdmin(admin.ModelAdmin):
    list_display = ['batch', 'camp_number', 'start_date', 'end_date', 'is_active']
    list_filter = ['camp_number', 'is_active', 'batch']
    search_fields = ['batch__name']

@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ['camp', 'session_number', 'title', 'session_date', 'is_active']
    list_filter = ['is_active', 'camp']
    search_fields = ['title']

@admin.register(IntercampActivity)
class IntercampActivityAdmin(admin.ModelAdmin):
    list_display = ['batch', 'after_camp', 'title', 'start_date', 'end_date', 'is_active']
    list_filter = ['after_camp', 'is_active']
    search_fields = ['title', 'batch__name']

@admin.register(MediaSubmission)
class MediaSubmissionAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'intercamp_activity', 'status', 'submitted_at', 'file_link']
    list_filter = ['status', 'submitted_at']
    search_fields = ['user__username', 'title']
    
    def file_link(self, obj):
        if obj.file:
            return format_html('<a href="{}" target="_blank">View File</a>', obj.file.url)
        return '-'
    file_link.short_description = 'File'

@admin.register(UserBatch)
class UserBatchAdmin(admin.ModelAdmin):
    list_display = ['user', 'batch', 'current_camp', 'enrolled_at', 'is_active']
    list_filter = ['batch', 'current_camp', 'is_active']
    search_fields = ['user__username', 'batch__name']

@admin.register(ProgressTracking)
class ProgressTrackingAdmin(admin.ModelAdmin):
    list_display = ['user', 'batch', 'stage', 'status', 'started_at', 'completed_at']
    list_filter = ['status', 'stage', 'batch']
    search_fields = ['user__username']
