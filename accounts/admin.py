# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.db.models import Count
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    # ── List View ──────────────────────────────────
    list_display   = ['username', 'full_name_display', 'email', 'phone',
                      'role_badge', 'application_status', 'interview_status',
                      'batch_info', 'is_active', 'created_at']
    list_filter    = ['role', 'is_active', 'is_staff',
                      'application__status',
                      'interview__status',
                      'user_batches__batch']
    search_fields  = ['username', 'email', 'first_name', 'last_name', 'phone']
    ordering       = ['-created_at']
    list_per_page  = 30
    date_hierarchy = 'created_at'

    # ── Detail View ────────────────────────────────
    fieldsets = (
        ('Login Credentials', {
            'fields': ('username', 'password')
        }),
        ('Personal Details', {
            'fields': ('first_name', 'last_name', 'email', 'phone', 'profile_pic')
        }),
        ('Role & Permissions', {
            'fields': ('role', 'is_active', 'is_staff', 'is_superuser'),
            'description': 'USER = applicant/volunteer. VOLUNTEER = assigned to batch. ADMIN = full access.'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields  = ['created_at', 'updated_at']
    add_fieldsets = (
        ('Create New User', {
            'fields': ('username', 'email', 'first_name', 'last_name',
                       'password1', 'password2', 'role')
        }),
    )

    # ── Computed Columns ───────────────────────────
    def full_name_display(self, obj):
        name = f"{obj.first_name} {obj.last_name}".strip()
        return name or format_html('<span style="color:#94a3b8;">—</span>')
    full_name_display.short_description = 'Full Name'

    def role_badge(self, obj):
        colours = {
            'ADMIN':     ('#fdf4ff', '#7e22ce'),
            'VOLUNTEER': ('#eff6ff', '#1e40af'),
            'USER':      ('#f1f5f9', '#475569'),
        }
        bg, fg = colours.get(obj.role, ('#f1f5f9', '#475569'))
        return format_html(
            '<span style="background:{};color:{};padding:2px 10px;'
            'border-radius:12px;font-size:12px;font-weight:600;">{}</span>',
            bg, fg, obj.get_role_display()
        )
    role_badge.short_description = 'Role'

    def application_status(self, obj):
        try:
            app = obj.application
            colours = {
                'PENDING':  ('#fefce8', '#92400e'),
                'APPROVED': ('#f0fdf4', '#166534'),
                'REJECTED': ('#fef2f2', '#991b1b'),
            }
            bg, fg = colours.get(app.status, ('#f1f5f9', '#475569'))
            return format_html(
                '<span style="background:{};color:{};padding:2px 8px;'
                'border-radius:10px;font-size:11px;font-weight:600;">{}</span>',
                bg, fg, app.get_status_display()
            )
        except Exception:
            return format_html('<span style="color:#cbd5e1;font-size:11px;">No app</span>')
    application_status.short_description = 'Application'

    def interview_status(self, obj):
        try:
            iv = obj.interview
            colours = {
                'SCHEDULED': ('#eff6ff', '#1d4ed8'),
                'PASSED':    ('#f0fdf4', '#166534'),
                'FAILED':    ('#fef2f2', '#991b1b'),
            }
            bg, fg = colours.get(iv.status, ('#f1f5f9', '#475569'))
            return format_html(
                '<span style="background:{};color:{};padding:2px 8px;'
                'border-radius:10px;font-size:11px;font-weight:600;">{}</span>',
                bg, fg, iv.get_status_display()
            )
        except Exception:
            return format_html('<span style="color:#cbd5e1;font-size:11px;">—</span>')
    interview_status.short_description = 'Interview'

    def batch_info(self, obj):
        ub = obj.user_batches.filter(is_active=True).select_related('batch').first()
        if ub:
            stages = {0:'Pre-Camp',1:'Camp 1',2:'Camp 2',3:'Camp 3',4:'Post-Camp',5:'Done'}
            stage  = stages.get(ub.current_camp, '—')
            return format_html(
                '<span style="font-size:11px;color:#1e40af;font-weight:600;">{}</span>'
                '<br><span style="font-size:10px;color:#94a3b8;">{}</span>',
                ub.batch.name, stage
            )
        return format_html('<span style="color:#cbd5e1;font-size:11px;">—</span>')
    batch_info.short_description = 'Batch / Stage'

    # ── Quick Actions ──────────────────────────────
    actions = ['mark_active', 'mark_inactive', 'set_role_volunteer']

    def mark_active(self, request, qs):
        qs.update(is_active=True)
        self.message_user(request, f"{qs.count()} user(s) activated.")
    mark_active.short_description = "✓ Activate selected users"

    def mark_inactive(self, request, qs):
        qs.update(is_active=False)
        self.message_user(request, f"{qs.count()} user(s) deactivated.")
    mark_inactive.short_description = "✗ Deactivate selected users"

    def set_role_volunteer(self, request, qs):
        qs.update(role='VOLUNTEER')
        self.message_user(request, f"{qs.count()} user(s) set to Volunteer.")
    set_role_volunteer.short_description = "→ Set role: Volunteer"