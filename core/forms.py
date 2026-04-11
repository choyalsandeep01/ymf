# core/forms.py
from django import forms
from .models import ApplicationForm, MediaSubmission, Batch, Camp, Session, IntercampActivity, CampLocation


INPUT_CLASS = 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
TEXTAREA_CLASS = INPUT_CLASS


class ApplicationFormForm(forms.ModelForm):

    preferred_location = forms.ModelChoiceField(
        queryset=CampLocation.objects.filter(is_active=True).order_by('state', 'city'),
        empty_label="— Select your preferred camp location —",
        widget=forms.Select(attrs={
            'class': INPUT_CLASS,
        }),
        help_text='Choose the state/city where you would like to attend the camp.',
        error_messages={'required': 'Please select a preferred camp location.'}
    )

    class Meta:
        model = ApplicationForm
        fields = [
            'full_name', 'email', 'phone', 'address',
            'qualification', 'why_join', 'experience',
            'preferred_location',            # ← new field
        ]
        widgets = {
            'full_name':     forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'e.g. Rajesh Kumar'}),
            'email':         forms.EmailInput(attrs={'class': INPUT_CLASS, 'placeholder': 'e.g. rajesh@example.com'}),
            'phone':         forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'e.g. +91 98765 43210'}),
            'address':       forms.Textarea(attrs={'class': TEXTAREA_CLASS, 'rows': 3, 'placeholder': 'Your full postal address'}),
            'qualification': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'e.g. B.Sc, B.Ed, Volunteer...'}),
            'why_join':      forms.Textarea(attrs={'class': TEXTAREA_CLASS, 'rows': 4, 'placeholder': 'Tell us why you want to join…'}),
            'experience':    forms.Textarea(attrs={'class': TEXTAREA_CLASS, 'rows': 3, 'placeholder': 'Any prior relevant experience…'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['experience'].required = False

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        digits = ''.join(filter(str.isdigit, phone))
        if len(digits) < 10:
            raise forms.ValidationError("Enter a valid phone number with at least 10 digits.")
        return phone


class MediaSubmissionForm(forms.ModelForm):
    class Meta:
        model = MediaSubmission
        fields = ['title', 'description', 'file']
        widgets = {
            'title':       forms.TextInput(attrs={'class': INPUT_CLASS}),
            'description': forms.Textarea(attrs={'class': TEXTAREA_CLASS, 'rows': 4}),
            'file':        forms.FileInput(attrs={'class': 'mt-1 block w-full'}),
        }


class BatchForm(forms.ModelForm):
    class Meta:
        model = Batch
        fields = ['name', 'description', 'start_date', 'end_date', 'is_active']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm'}),
            'end_date':   forms.DateInput(attrs={'type': 'date', 'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm'}),
        }
