from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('api/get/', views.get_notifications, name='get_notifications'),
    path('api/counts/', views.notification_counts, name='notification_counts'),
    path('api/mark-read/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),
    path('api/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('api/delete/<int:notification_id>/', views.delete_notification, name='delete_notification'),
    path('api/click/<int:notification_id>/', views.notification_click, name='notification_click'),
]
