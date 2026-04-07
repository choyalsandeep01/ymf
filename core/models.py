from django.db import models
from django.conf import settings
from django.utils import timezone

class ApplicationForm(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending Review'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='application')
    full_name = models.CharField(max_length=300)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    address = models.TextField()
    qualification = models.CharField(max_length=200)
    why_join = models.TextField()
    experience = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, 
                                    null=True, blank=True, related_name='reviewed_applications')
    admin_notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.status}"

class InterviewStatus(models.Model):
    STATUS_CHOICES = [
        ('SCHEDULED', 'Scheduled'),
        ('PASSED', 'Passed'),
        ('FAILED', 'Failed'),
    ]
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='interview')
    interview_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SCHEDULED')
    interviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, 
                                   null=True, blank=True, related_name='conducted_interviews')
    notes = models.TextField(blank=True)
    score = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.status}"

class Batch(models.Model):
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        verbose_name_plural = 'Batches'
        ordering = ['-start_date']
    
    def __str__(self):
        return self.name

class Camp(models.Model):
    CAMP_CHOICES = [
        (1, 'Camp 1'),
        (2, 'Camp 2'),
        (3, 'Camp 3'),
    ]
    
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='camps')
    camp_number = models.IntegerField(choices=CAMP_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['batch', 'camp_number']
        ordering = ['batch', 'camp_number']
    
    def __str__(self):
        return f"{self.batch.name} - Camp {self.camp_number}"

class Session(models.Model):
    camp = models.ForeignKey(Camp, on_delete=models.CASCADE, related_name='sessions')
    session_number = models.IntegerField()  # 1 to 7
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    session_date = models.DateField()
    is_active = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['camp', 'session_number']
        ordering = ['camp', 'session_number']
    
    def __str__(self):
        return f"{self.camp} - Session {self.session_number}"

class IntercampActivity(models.Model):
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='intercamp_activities')
    after_camp = models.IntegerField(choices=[(1, 'After Camp 1'), (2, 'After Camp 2')])
    title = models.CharField(max_length=300)
    description = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False)
    
    class Meta:
        verbose_name_plural = 'Intercamp Activities'
        unique_together = ['batch', 'after_camp']
        ordering = ['batch', 'after_camp']
    
    def __str__(self):
        return f"{self.batch.name} - After Camp {self.after_camp}"

class MediaSubmission(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending Review'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='media_submissions')
    intercamp_activity = models.ForeignKey(IntercampActivity, on_delete=models.CASCADE, related_name='submissions')
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='media_submissions/%Y/%m/')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, 
                                   null=True, blank=True, related_name='reviewed_media')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-submitted_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"

class UserBatch(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user_batches')
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='batch_users')
    enrolled_at = models.DateTimeField(auto_now_add=True)
    current_camp = models.IntegerField(default=0)  # 0=pre-camp, 1-3=camps, 4=post-camp, 5=completed
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['user', 'batch']
        ordering = ['-enrolled_at']
    
    def __str__(self):
        return f"{self.user.username} in {self.batch.name}"

class ProgressTracking(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='progress')
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE)
    camp = models.ForeignKey(Camp, on_delete=models.CASCADE, null=True, blank=True)
    session = models.ForeignKey(Session, on_delete=models.CASCADE, null=True, blank=True)
    stage = models.CharField(max_length=50)  # 'pre-camp', 'camp1-session1', 'intercamp1', etc.
    status = models.CharField(max_length=50)  # 'not-started', 'in-progress', 'completed'
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['user', 'batch', 'started_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.stage} - {self.status}"
