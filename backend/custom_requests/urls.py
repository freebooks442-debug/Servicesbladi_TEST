from django.urls import path, include
from . import views
from . import message_views
from . import client_views
from . import admin_views
from . import expert_views

app_name = 'custom_requests'

urlpatterns = [
    # Client request views
    path('client/', views.client_requests_view, name='client_requests'),
    path('client/create/<int:service_id>/', views.create_request_view, name='create_request'),
    path('client/create/<str:service_type>/', views.create_request_by_type_view, name='create_request_by_type'),
    path('client/detail/<int:request_id>/', views.request_detail_view, name='request_detail'),
    path('client/edit/<int:request_id>/', views.edit_request_view, name='edit_request'),
    path('client/cancel/<int:request_id>/', views.cancel_request_view, name='cancel_request'),
    
    # Appointment views
    path('appointments/', views.client_appointments_view, name='client_appointments'),
    path('appointments/create/', views.create_appointment_view, name='create_appointment'),
    path('appointments/detail/<int:appointment_id>/', views.appointment_detail_view, name='appointment_detail'),
    path('appointments/cancel/<int:appointment_id>/', views.cancel_appointment_view, name='cancel_appointment'),    # Expert views
    path('expert/', expert_views.expert_requests_view, name='expert_requests'),
    path('expert/demande/<int:request_id>/', views.request_detail_view, name='expert_request_detail'), # Updated name
    path('expert/requests/<int:request_id>/take/', expert_views.expert_take_request, name='expert_take_request'),
    path('expert/requests/<int:request_id>/update-status/', expert_views.expert_update_request_status, name='expert_update_request_status'),
    path('expert/appointments/', expert_views.expert_appointments_view, name='expert_appointments'),
    path('expert/documents/', expert_views.expert_documents_view, name='expert_documents'),
    path('expert/upload_document/', expert_views.expert_upload_document, name='expert_upload_document'),
    path('expert/add_appointment/', views.expert_create_appointment_view, name='expert_add_appointment'),
    path('expert/add_resource/', views.upload_document_view, name='expert_add_resource'),
    
    # Document views
    path('documents/', views.documents_view, name='documents'),
    path('documents/upload/', views.upload_document_view, name='upload_document'),
    path('documents/delete/<int:document_id>/', views.delete_document_view, name='delete_document'),
    path('documents/download/<int:document_id>/', views.download_document_view, name='download_document'),
    path('documents/view/<int:document_id>/', views.view_document_view, name='view_document'),
    
    # Messaging views
    path('messages/', views.messages_view, name='messages'),
    path('client/send_message/<int:recipient_id>/', message_views.client_send_message, name='client_send_message'),
    path('client/check_messages/', message_views.client_check_messages, name='client_check_messages'),
    path('expert/send_message/<int:client_id>/', message_views.expert_send_message, name='expert_send_message'),
    path('expert/check_messages/', message_views.expert_check_messages, name='expert_check_messages'),
    path('messages/send/', views.send_message_view, name='send_message'),
    
    # API endpoints
    path('api/client/requests/', views.api_client_requests, name='api_client_requests'),
    path('api/request/<int:request_id>/', views.api_request_detail, name='api_request_detail'),
    path('api/appointments/', views.api_client_appointments, name='api_appointments'),
    path('api/expert/requests/', views.api_expert_requests, name='api_expert_requests'),    path('api/documents/upload/', views.api_upload_document, name='api_upload_document'),
    path('api/messages/', views.api_messages, name='api_messages'),
    path('api/client/appointments/', client_views.client_appointments_api, name='client_appointments_api'),
    path('api/client/appointments/<int:appointment_id>/cancel/', client_views.cancel_appointment_api, name='cancel_appointment_api'),
    
    # AJAX endpoints
    path('ajax/create-request/', views.ajax_create_request, name='ajax_create_request'),
    
    # Admin views
    path('admin/demande/<int:request_id>/', admin_views.admin_request_detail, name='admin_request_detail'),
    path('admin/documents/', admin_views.admin_documents_view, name='admin_documents'),
    path('admin/documents/verify/<int:document_id>/', admin_views.admin_verify_document, name='admin_verify_document'),
    path('admin/documents/reject/<int:document_id>/', admin_views.admin_reject_document, name='admin_reject_document'),
    path('admin/documents/delete/<int:document_id>/', admin_views.admin_delete_document, name='admin_delete_document'),
]