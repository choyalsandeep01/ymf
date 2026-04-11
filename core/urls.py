from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('submit-application/', views.submit_application, name='submit_application'),
    path('autosave-draft/', views.autosave_draft, name='autosave_draft'),   # ← NEW
    path('batch/<int:batch_id>/', views.batch_detail, name='batch_detail'),
    path('camp/<int:camp_id>/', views.camp_detail, name='camp_detail'),
    path('session/<int:session_id>/', views.session_detail, name='session_detail'),
    path('intercamp/<int:activity_id>/', views.intercamp_activity_detail, name='intercamp_activity_detail'),
    path('intercamp/<int:activity_id>/submit/', views.submit_media, name='submit_media'),
    path('my-progress/', views.my_progress, name='my_progress'),
]
