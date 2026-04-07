from django.urls import path
from . import views

app_name = 'ratings'

urlpatterns = [
    path('attempt/<int:attempt_id>/', views.rate_questionnaire_attempt, name='rate_attempt'),
    path('media/<int:submission_id>/', views.rate_media_submission, name='rate_media'),
    path('pending/', views.pending_ratings, name='pending_ratings'),
]
