# core/models.py — COMPLETE FILE
import json as _json
from django.db import models
from django.conf import settings
from django.utils import timezone


# ─────────────────────────────────────────────────────────────────────────────
# CAMP LOCATION
# ─────────────────────────────────────────────────────────────────────────────

class CampLocation(models.Model):
    STATE_CHOICES = [
        ('AN', 'Andaman & Nicobar Islands'), ('AP', 'Andhra Pradesh'),
        ('AR', 'Arunachal Pradesh'), ('AS', 'Assam'), ('BR', 'Bihar'),
        ('CG', 'Chhattisgarh'), ('GA', 'Goa'), ('GJ', 'Gujarat'),
        ('HR', 'Haryana'), ('HP', 'Himachal Pradesh'), ('JK', 'Jammu & Kashmir'),
        ('JH', 'Jharkhand'), ('KA', 'Karnataka'), ('KL', 'Kerala'),
        ('MP', 'Madhya Pradesh'), ('MH', 'Maharashtra'), ('MN', 'Manipur'),
        ('ML', 'Meghalaya'), ('MZ', 'Mizoram'), ('NL', 'Nagaland'),
        ('OD', 'Odisha'), ('PB', 'Punjab'), ('RJ', 'Rajasthan'),
        ('SK', 'Sikkim'), ('TN', 'Tamil Nadu'), ('TS', 'Telangana'),
        ('TR', 'Tripura'), ('UP', 'Uttar Pradesh'), ('UK', 'Uttarakhand'),
        ('WB', 'West Bengal'), ('DL', 'Delhi'), ('CH', 'Chandigarh'),
    ]

    name       = models.CharField(max_length=200)
    state      = models.CharField(max_length=2, choices=STATE_CHOICES)
    city       = models.CharField(max_length=100)
    address    = models.TextField(blank=True)
    is_active  = models.BooleanField(default=True)
    capacity   = models.IntegerField(default=50)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['state', 'city']
        verbose_name = 'Camp Location'
        verbose_name_plural = 'Camp Locations'

    def __str__(self):
        return f"{self.name} — {self.get_state_display()}"


# ─────────────────────────────────────────────────────────────────────────────
# APPLICATION FORM
# ─────────────────────────────────────────────────────────────────────────────

class ApplicationForm(models.Model):
    STATUS_CHOICES = [
        ('PENDING',  'Pending Review'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]

    user               = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='application')
    full_name          = models.CharField(max_length=300)
    email              = models.EmailField()
    phone              = models.CharField(max_length=15)
    address            = models.TextField()
    qualification      = models.CharField(max_length=200)
    why_join           = models.TextField()
    experience         = models.TextField(blank=True)
    preferred_location = models.ForeignKey(
        CampLocation, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='applicants', help_text='Select the camp location nearest to you'
    )
    status      = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at  = models.DateTimeField(null=True, blank=True)
    reviewed_by  = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='reviewed_applications'
    )
    admin_notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.status}"


# ─────────────────────────────────────────────────────────────────────────────
# INTERVIEW STATUS
# ─────────────────────────────────────────────────────────────────────────────

class InterviewStatus(models.Model):
    STATUS_CHOICES = [
        ('SCHEDULED', 'Scheduled'),
        ('PASSED',    'Passed'),
        ('FAILED',    'Failed'),
    ]

    user           = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='interview')
    interview_date = models.DateTimeField(null=True, blank=True)
    status         = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SCHEDULED')
    interviewer    = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='conducted_interviews'
    )
    notes      = models.TextField(blank=True)
    score      = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.status}"


# ─────────────────────────────────────────────────────────────────────────────
# BATCH / CAMP / SESSION / INTERCAMP
# ─────────────────────────────────────────────────────────────────────────────

class Batch(models.Model):
    name        = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    start_date  = models.DateField()
    end_date    = models.DateField(null=True, blank=True)
    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    created_by  = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    class Meta:
        verbose_name_plural = 'Batches'
        ordering = ['-start_date']

    def __str__(self):
        return self.name


class Camp(models.Model):
    CAMP_CHOICES = [(1, 'Camp 1'), (2, 'Camp 2'), (3, 'Camp 3')]

    batch       = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='camps')
    camp_number = models.IntegerField(choices=CAMP_CHOICES)
    location    = models.ForeignKey(
        CampLocation, on_delete=models.SET_NULL, null=True, blank=True, related_name='camps'
    )
    start_date = models.DateField()
    end_date   = models.DateField()
    is_active  = models.BooleanField(default=False)

    class Meta:
        unique_together = ['batch', 'camp_number']
        ordering = ['batch', 'camp_number']

    def __str__(self):
        loc = f" @ {self.location.city}" if self.location else ""
        return f"{self.batch.name} - Camp {self.camp_number}{loc}"


class Session(models.Model):
    camp           = models.ForeignKey(Camp, on_delete=models.CASCADE, related_name='sessions')
    session_number = models.IntegerField()
    title          = models.CharField(max_length=300)
    description    = models.TextField(blank=True)
    session_date   = models.DateField()
    is_active      = models.BooleanField(default=False)

    class Meta:
        unique_together = ['camp', 'session_number']
        ordering = ['camp', 'session_number']

    def __str__(self):
        return f"{self.camp} - Session {self.session_number}"


class IntercampActivity(models.Model):
    batch       = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='intercamp_activities')
    after_camp  = models.IntegerField(choices=[(1, 'After Camp 1'), (2, 'After Camp 2')])
    title       = models.CharField(max_length=300)
    description = models.TextField()
    start_date  = models.DateField()
    end_date    = models.DateField()
    is_active   = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = 'Intercamp Activities'
        unique_together = ['batch', 'after_camp']
        ordering = ['batch', 'after_camp']

    def __str__(self):
        return f"{self.batch.name} - After Camp {self.after_camp}"


# ─────────────────────────────────────────────────────────────────────────────
# MEDIA SUBMISSION
# ─────────────────────────────────────────────────────────────────────────────

class MediaSubmission(models.Model):
    STATUS_CHOICES = [
        ('PENDING',  'Pending Review'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]

    user               = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='media_submissions')
    intercamp_activity = models.ForeignKey(IntercampActivity, on_delete=models.CASCADE, related_name='submissions')
    title              = models.CharField(max_length=300)
    description        = models.TextField(blank=True)
    file               = models.FileField(upload_to='media_submissions/%Y/%m/')
    status             = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    submitted_at       = models.DateTimeField(auto_now_add=True)
    reviewed_by        = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='reviewed_media'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.user.username} - {self.title}"


# ─────────────────────────────────────────────────────────────────────────────
# USER BATCH & PROGRESS
# ─────────────────────────────────────────────────────────────────────────────

class UserBatch(models.Model):
    user         = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user_batches')
    batch        = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='batch_users')
    enrolled_at  = models.DateTimeField(auto_now_add=True)
    current_camp = models.IntegerField(default=0)  # 0=pre-camp, 1-3=camps, 4=post-camp, 5=completed
    is_active    = models.BooleanField(default=True)

    class Meta:
        unique_together = ['user', 'batch']
        ordering = ['-enrolled_at']

    def __str__(self):
        return f"{self.user.username} in {self.batch.name}"


class ProgressTracking(models.Model):
    user         = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='progress')
    batch        = models.ForeignKey(Batch, on_delete=models.CASCADE)
    camp         = models.ForeignKey(Camp, on_delete=models.CASCADE, null=True, blank=True)
    session      = models.ForeignKey(Session, on_delete=models.CASCADE, null=True, blank=True)
    stage        = models.CharField(max_length=50)
    status       = models.CharField(max_length=50)
    started_at   = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['user', 'batch', 'started_at']

    def __str__(self):
        return f"{self.user.username} - {self.stage} - {self.status}"


# ─────────────────────────────────────────────────────────────────────────────
# DYNAMIC FORM BUILDER  (SQLite-safe — no JSONField)
# ─────────────────────────────────────────────────────────────────────────────

class FormSection(models.Model):
    """Admin-created section that groups questions."""
    title_en       = models.CharField(max_length=300, verbose_name="Title (English)")
    title_hi       = models.CharField(max_length=300, verbose_name="Title (Hindi)")
    description_en = models.TextField(blank=True, verbose_name="Description (English)")
    description_hi = models.TextField(blank=True, verbose_name="Description (Hindi)")
    order          = models.PositiveIntegerField(default=0, help_text="Lower = shown first")
    is_active      = models.BooleanField(default=True)
    created_at     = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'id']
        verbose_name = 'Form Section'
        verbose_name_plural = 'Form Sections'

    def __str__(self):
        return f"[{self.order}] {self.title_en}"


class FormQuestion(models.Model):
    QUESTION_TYPES = [
        ('TEXT',     'Short Text'),
        ('TEXTAREA', 'Long Text / Subjective'),
        ('SINGLE',   'Single Choice (Radio)'),
        ('MULTI',    'Multiple Choice (Checkboxes)'),
        ('SELECT',   'Dropdown Select'),
        ('DATE',     'Date Picker'),
        ('NUMBER',   'Number Input'),
        ('EMAIL',    'Email Input'),
        ('PHONE',    'Phone Number'),
    ]

    section       = models.ForeignKey(FormSection, on_delete=models.CASCADE, related_name='questions')
    question_en   = models.TextField(verbose_name="Question (English)")
    question_hi   = models.TextField(verbose_name="Question (Hindi)")
    hint_en       = models.CharField(max_length=500, blank=True, verbose_name="Hint (English)")
    hint_hi       = models.CharField(max_length=500, blank=True, verbose_name="Hint (Hindi)")
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES, default='TEXTAREA')
    is_required   = models.BooleanField(default=True)
    order         = models.PositiveIntegerField(default=0)
    is_active     = models.BooleanField(default=True)
    created_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['section__order', 'order', 'id']
        verbose_name = 'Form Question'
        verbose_name_plural = 'Form Questions'

    def __str__(self):
        return f"[S{self.section.order} Q{self.order}] {self.question_en[:60]}"


class FormQuestionOption(models.Model):
    """An answer option for SINGLE / MULTI / SELECT questions."""
    question  = models.ForeignKey(FormQuestion, on_delete=models.CASCADE, related_name='options')
    option_en = models.CharField(max_length=500, verbose_name="Option Text (English)")
    option_hi = models.CharField(max_length=500, verbose_name="Option Text (Hindi)")
    order     = models.PositiveIntegerField(default=0)
    is_other  = models.BooleanField(
        default=False,
        help_text="Tick to make this the 'Other — please specify' option"
    )

    class Meta:
        ordering = ['order', 'id']
        verbose_name = 'Question Option'
        verbose_name_plural = 'Question Options'

    def __str__(self):
        return f"Q#{self.question_id} | {self.option_en[:40]}"


# ── SQLite-safe helpers ───────────────────────────────────────────────────────
# Both ApplicationDraft and ApplicationAnswer use TextField to store JSON.
# Access via the .answers / .selected_options properties — identical API to
# JSONField so no view code needs changing.
# ─────────────────────────────────────────────────────────────────────────────

class ApplicationDraft(models.Model):
    """
    Autosave store — one row per user.
    Answers serialised to a plain TextField (JSON string) for SQLite compatibility.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='application_draft'
    )
    preferred_location = models.ForeignKey(
        CampLocation, on_delete=models.SET_NULL, null=True, blank=True
    )
    language  = models.CharField(
        max_length=2, choices=[('en', 'English'), ('hi', 'Hindi')], default='en'
    )
    # Use get_answers() / set_answers() or the .answers property — never _answers directly
    _answers  = models.TextField(default='{}', db_column='answers', blank=True)
    last_step = models.PositiveIntegerField(default=0)
    last_saved = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # ── JSON helpers ─────────────────────────────────────────────────────────
    def get_answers(self) -> dict:
        try:
            return _json.loads(self._answers or '{}')
        except (_json.JSONDecodeError, TypeError):
            return {}

    def set_answers(self, data: dict):
        self._answers = _json.dumps(data, ensure_ascii=False)

    @property
    def answers(self):
        return self.get_answers()

    @answers.setter
    def answers(self, value):
        self.set_answers(value)

    def __str__(self):
        return f"Draft — {self.user.username} (saved {self.last_saved:%d %b %Y %H:%M})"


class ApplicationAnswer(models.Model):
    """Final submitted answers — one row per question per application."""
    application = models.ForeignKey(
        ApplicationForm, on_delete=models.CASCADE, related_name='answers'
    )
    question    = models.ForeignKey(FormQuestion, on_delete=models.PROTECT)
    # TEXT / TEXTAREA / EMAIL / PHONE / NUMBER / DATE
    answer_text = models.TextField(blank=True)
    # SINGLE / MULTI / SELECT — list of option PKs stored as JSON string
    _selected_options = models.TextField(
        default='[]', db_column='selected_options', blank=True
    )
    other_text = models.TextField(blank=True)

    # ── JSON helpers ─────────────────────────────────────────────────────────
    def get_selected_options(self) -> list:
        try:
            return _json.loads(self._selected_options or '[]')
        except (_json.JSONDecodeError, TypeError):
            return []

    def set_selected_options(self, data: list):
        self._selected_options = _json.dumps(data)

    @property
    def selected_options(self):
        return self.get_selected_options()

    @selected_options.setter
    def selected_options(self, value):
        self.set_selected_options(value)

    class Meta:
        unique_together = ['application', 'question']
        ordering = ['question__section__order', 'question__order']

    def __str__(self):
        return f"App#{self.application_id} Q#{self.question_id}"
