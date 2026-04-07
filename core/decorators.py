from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from core.models import UserBatch, ApplicationForm, InterviewStatus

def batch_required(view_func):
    """
    Decorator to ensure user is assigned to a batch before accessing views
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Allow admin and volunteers to bypass
        if request.user.is_admin_role() or request.user.is_volunteer_role():
            return view_func(request, *args, **kwargs)
        
        # Check if user has an active batch assignment
        has_batch = UserBatch.objects.filter(
            user=request.user,
            is_active=True
        ).exists()
        
        if not has_batch:
            messages.warning(request, 'You need to be assigned to a batch first. Please complete your application and interview process.')
            return redirect('core:homepage')
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def application_approved_required(view_func):
    """
    Decorator to ensure user's application is approved
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Allow admin and volunteers to bypass
        if request.user.is_admin_role() or request.user.is_volunteer_role():
            return view_func(request, *args, **kwargs)
        
        try:
            application = ApplicationForm.objects.get(user=request.user)
            if application.status != 'APPROVED':
                messages.warning(request, 'Your application must be approved first.')
                return redirect('core:homepage')
        except ApplicationForm.DoesNotExist:
            messages.warning(request, 'Please submit your application first.')
            return redirect('core:submit_application')
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def interview_passed_required(view_func):
    """
    Decorator to ensure user has passed the interview
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Allow admin and volunteers to bypass
        if request.user.is_admin_role() or request.user.is_volunteer_role():
            return view_func(request, *args, **kwargs)
        
        try:
            interview = InterviewStatus.objects.get(user=request.user)
            if interview.status != 'PASSED':
                messages.warning(request, 'You must pass the interview first.')
                return redirect('core:homepage')
        except InterviewStatus.DoesNotExist:
            messages.warning(request, 'Interview status not found.')
            return redirect('core:homepage')
        
        return view_func(request, *args, **kwargs)
    
    return wrapper
