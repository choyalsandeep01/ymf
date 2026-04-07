from django import forms
from .models import Questionnaire, Question, Option

class QuestionnaireForm(forms.ModelForm):
    class Meta:
        model = Questionnaire
        fields = ['title', 'description', 'test_type', 'time_limit_minutes', 
                  'is_active', 'is_published', 'allow_multiple_attempts', 
                  'open_date', 'close_date']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'open_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'close_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['question_type', 'question_text', 'question_image', 'marks', 'order']
        widgets = {
            'question_text': forms.Textarea(attrs={'rows': 3}),
        }

class OptionForm(forms.ModelForm):
    class Meta:
        model = Option
        fields = ['option_text', 'option_image', 'is_correct', 'order']
