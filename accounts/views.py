from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .forms import SignUpForm, LoginForm
from .models import User

def signup_view(request):
    if request.user.is_authenticated:
        return redirect('core:homepage')
    
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'USER'
            user.save()
            messages.success(request, 'Account created successfully! Please login.')
            return redirect('accounts:login')
    else:
        form = SignUpForm()
    
    return render(request, 'accounts/signup.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('core:homepage')
    
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        username_or_email = request.POST.get('username')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember_me')
        
        # Check if email is provided instead of username
        user_obj = User.objects.filter(Q(username=username_or_email) | Q(email=username_or_email)).first()
        
        if user_obj:
            user = authenticate(request, username=user_obj.username, password=password)
            if user is not None:
                login(request, user)
                
                # Handle remember me
                if not remember_me:
                    request.session.set_expiry(0)
                
                messages.success(request, f'Welcome back, {user.first_name}!')
                return redirect('core:homepage')
        
        messages.error(request, 'Invalid username/email or password.')
    else:
        form = LoginForm()
    
    return render(request, 'accounts/login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('accounts:login')

@login_required
def profile_view(request):
    return render(request, 'accounts/profile.html')
