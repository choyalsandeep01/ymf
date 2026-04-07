from django.db import models
from django.conf import settings
from questionnaires.models import UserQuestionnaireAttempt
from core.models import MediaSubmission

class Rating(models.Model):
    # What is being rated
    questionnaire_attempt = models.ForeignKey(UserQuestionnaireAttempt, on_delete=models.CASCADE, 
                                             null=True, blank=True, related_name='ratings')
    media_submission = models.ForeignKey(MediaSubmission, on_delete=models.CASCADE, 
                                        null=True, blank=True, related_name='ratings')
    
    # Rating details
    rated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='given_ratings')
    score = models.IntegerField(help_text='Score out of 100')
    comment = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        if self.questionnaire_attempt:
            return f"Rating by {self.rated_by.username} for {self.questionnaire_attempt.user.username}'s attempt"
        elif self.media_submission:
            return f"Rating by {self.rated_by.username} for {self.media_submission.user.username}'s media"
        return f"Rating by {self.rated_by.username}"
