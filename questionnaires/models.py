from django.db import models
from django.conf import settings
from core.models import Session, IntercampActivity, Batch

class Questionnaire(models.Model):
    TEST_TYPE_CHOICES = [
        ('PRE', 'Pre-Test'),
        ('POST', 'Post-Test'),
        ('PRE_CAMP', 'Pre-Camp'),
        ('POST_CAMP', 'Post-Camp'),
        ('INTERCAMP', 'Intercamp'),
    ]
    
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    test_type = models.CharField(max_length=20, choices=TEST_TYPE_CHOICES)
    
    # Relations
    session = models.ForeignKey(Session, on_delete=models.CASCADE, null=True, blank=True, related_name='questionnaires')
    intercamp_activity = models.ForeignKey(IntercampActivity, on_delete=models.CASCADE, null=True, blank=True, related_name='questionnaires')
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, null=True, blank=True, related_name='questionnaires')
    
    # Settings
    time_limit_minutes = models.IntegerField(null=True, blank=True, help_text='Leave blank for no time limit')
    is_active = models.BooleanField(default=False)
    is_published = models.BooleanField(default=False)
    allow_multiple_attempts = models.BooleanField(default=False)
    
    # Dates
    open_date = models.DateTimeField(null=True, blank=True)
    close_date = models.DateTimeField(null=True, blank=True)
    
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.get_test_type_display()})"

class Question(models.Model):
    QUESTION_TYPE_CHOICES = [
        ('MCQ', 'Multiple Choice'),
        ('SUBJECTIVE', 'Subjective'),
        ('IMAGE_MCQ', 'Image-based MCQ'),
    ]
    
    questionnaire = models.ForeignKey(Questionnaire, on_delete=models.CASCADE, related_name='questions')
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPE_CHOICES, default='MCQ')
    question_text = models.TextField()
    question_image = models.ImageField(upload_to='questionnaires/questions/', null=True, blank=True)
    order = models.IntegerField(default=0)
    marks = models.IntegerField(default=1)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order', 'id']
    
    def __str__(self):
        return f"Q{self.order}: {self.question_text[:50]}"

class Option(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    option_text = models.TextField(blank=True)
    option_image = models.ImageField(upload_to='questionnaires/options/', null=True, blank=True)
    is_correct = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order', 'id']
    
    def __str__(self):
        return f"Option: {self.option_text[:30]}"

class UserQuestionnaireAttempt(models.Model):
    STATUS_CHOICES = [
        ('IN_PROGRESS', 'In Progress'),
        ('SUBMITTED', 'Submitted'),
        ('RATED', 'Rated'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='questionnaire_attempts')
    questionnaire = models.ForeignKey(Questionnaire, on_delete=models.CASCADE, related_name='attempts')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='IN_PROGRESS')
    
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    time_taken_minutes = models.IntegerField(null=True, blank=True)
    
    score = models.FloatField(null=True, blank=True)
    total_marks = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.questionnaire.title}"

class UserResponse(models.Model):
    attempt = models.ForeignKey(UserQuestionnaireAttempt, on_delete=models.CASCADE, related_name='responses')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    
    # For MCQ
    selected_option = models.ForeignKey(Option, on_delete=models.CASCADE, null=True, blank=True)
    
    # For subjective
    text_response = models.TextField(blank=True)
    response_image = models.ImageField(upload_to='questionnaires/responses/', null=True, blank=True)
    
    is_correct = models.BooleanField(null=True, blank=True)
    marks_obtained = models.FloatField(null=True, blank=True)
    
    answered_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.attempt.user.username} - Q{self.question.id}"
