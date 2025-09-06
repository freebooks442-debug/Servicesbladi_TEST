from django.urls import path
from . import views

app_name = 'chatbot'

urlpatterns = [
    # Interface principale du chatbot
    path('', views.ChatbotView.as_view(), name='chatbot'),
    
    # API endpoints
    path('api/chat/', views.ChatAPIView.as_view(), name='chat_api'),
    path('api/feedback/', views.ChatFeedbackView.as_view(), name='feedback_api'),
    
    # Analytics (admin only)
    path('analytics/', views.chatbot_analytics_view, name='analytics'),
]
