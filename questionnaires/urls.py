from django.urls import path
from . import views

app_name = 'questionnaires'

urlpatterns = [
    path('', views.questionnaire_list, name='questionnaire_list'),
    path('<int:questionnaire_id>/start/', views.start_questionnaire, name='start_questionnaire'),
    path('attempt/<int:attempt_id>/', views.attempt_questionnaire, name='attempt_questionnaire'),
    path('results/<int:attempt_id>/', views.view_results, name='view_results'),
    path('my-attempts/', views.my_attempts, name='my_attempts'),
]
