from django.urls import path
from . import views


app_name = 'analytics'


urlpatterns = [
    # Main views
    path('', views.analytics_dashboard, name='dashboard'),
    path('batch/<int:batch_id>/', views.batch_analytics, name='batch_analytics'),
    path('user/<int:user_id>/', views.user_analytics, name='user_analytics'),
    path('camp/<int:camp_id>/', views.camp_analytics, name='camp_analytics'),

    # Chart data endpoints (existing)
    path('api/batch/<int:batch_id>/performance/', views.batch_performance_chart_data, name='batch_performance_data'),
    path('api/user/<int:user_id>/progress/', views.user_progress_chart_data, name='user_progress_data'),

    # New chart data endpoints for enhanced analytics
    path('api/batch/<int:batch_id>/student-comparison/', views.student_comparison_data, name='student_comparison_data'),
    path('api/batch/<int:batch_id>/prepost-comparison/', views.prepost_comparison_data, name='prepost_comparison_data'),

    # AJAX endpoint for dynamic session loading
    path('api/camp/<int:camp_id>/sessions/', views.get_camp_sessions, name='camp_sessions'),
]