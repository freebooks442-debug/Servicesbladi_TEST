from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.utils import timezone

from accounts.models import Client, Utilisateur, Expert
from services.models import Service, ServiceCategory
from .models import ServiceRequest, Document, RendezVous, Notification, Message

def get_service_icon(service):
    """Helper function to get appropriate icon for a service"""
    if service.service_type and service.service_type.category and service.service_type.category.icon:
        return service.service_type.category.icon
    
    # Default icons based on service type if available
    service_type_name = ''
    if service.service_type:
        service_type_name = service.service_type.name.lower()
    
    if 'tourisme' in service_type_name or 'tourism' in service_type_name:
        return 'airplane'
    elif 'administrative' in service_type_name or 'admin' in service_type_name:
        return 'file-earmark-text'
    elif 'immobilier' in service_type_name or 'real estate' in service_type_name:
        return 'house-door'
    elif 'fiscal' in service_type_name or 'tax' in service_type_name:
        return 'calculator'
    elif 'investissement' in service_type_name or 'investment' in service_type_name:
        return 'graph-up'
    
    return 'file-earmark-text'  # Default icon

@login_required
def client_dashboard_view(request):
    """
    View function for the client dashboard.
    
    This view acts as the central hub for clients to view their service requests,
    documents, upcoming appointments, and notifications. It provides:
    - Counts of active and completed service requests
    - Count of available documents
    - Recent notifications with unread notification count
    - List of upcoming appointments
    - Available services that can be requested
    - Recent documents uploaded by or for the client
    - Recent service requests submitted by the client
    
    Args:
        request: The HTTP request object
        
    Returns:
        Rendered dashboard template with context data or redirects to home if client profile not found
    """
    print(f"Starting client_dashboard_view for user {request.user.email}, account_type={request.user.account_type}")
    
    try:
        # Debug more details about the user
        print(f"User details: id={request.user.id}, email={request.user.email}, name={request.user.name}, account_type={request.user.account_type}")
        
        # Check if client profile exists - using case-insensitive check for account_type
        if request.user.account_type.lower() != 'client':
            print(f"User account type is {request.user.account_type}, not client. Redirecting to home.")
            return redirect('home')
        
        # Check if client profile exists
        client_exists = Client.objects.filter(user=request.user).exists()
        print(f"Client profile exists for user: {client_exists}")
        
        if not client_exists:
            # Query by email directly for debugging
            client_by_email = Client.objects.filter(user__email=request.user.email)
            print(f"Client profile by email check: {client_by_email.exists()}")
            print(f"Client profile not found for user {request.user.email}, redirecting to home")
            return redirect('home')
        
        # Get client profile
        client_profile = Client.objects.get(user=request.user)
        print(f"Found client profile for {client_profile}")
        
        # Count of active service requests
        active_requests = ServiceRequest.objects.filter(
            client=request.user,
            status__in=['new', 'in_progress', 'pending_info']
        ).count()
        print(f"Active requests count: {active_requests}")
        
        # Count of completed service requests
        completed_requests = ServiceRequest.objects.filter(
            client=request.user,
            status='completed'
        ).count()
        print(f"Completed requests count: {completed_requests}")
        
        # Count of documents
        documents_count = Document.objects.filter(
            Q(service_request__client=request.user) |
            Q(rendez_vous__client=request.user) |
            Q(uploaded_by=request.user)
        ).distinct().count()
        print(f"Documents count: {documents_count}")
        
        # Get recent notifications
        notifications = Notification.objects.filter(
            user=request.user
        ).order_by('-created_at')[:5]
        print(f"Retrieved {len(notifications)} notifications")
        
        # Count unread notifications
        unread_notifications_count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()
        print(f"Unread notifications count: {unread_notifications_count}")
        
        # Get upcoming appointments
        upcoming_appointments = RendezVous.objects.filter(
            client=request.user,
            date_time__gte=timezone.now(),
            status__in=['scheduled', 'confirmed']
        ).order_by('date_time')[:3]
        print(f"Retrieved {len(upcoming_appointments)} upcoming appointments")
        
        # Get available services
        available_services = Service.objects.filter(is_active=True).select_related('service_type__category')
        print(f"Retrieved {len(available_services)} available services")
        
        # Enrich services with icons
        services_with_icons = []
        for service in available_services:
            service.icon = get_service_icon(service)
            services_with_icons.append(service)
        
        # Get recent documents
        recent_documents = Document.objects.filter(
            Q(service_request__client=request.user) |
            Q(rendez_vous__client=request.user) |
            Q(uploaded_by=request.user)
        ).distinct().order_by('-upload_date')[:3]
        print(f"Retrieved {len(recent_documents)} recent documents")
        
        # Get recent service requests
        recent_requests = ServiceRequest.objects.filter(
            client=request.user
        ).order_by('-created_at')[:3]
        print(f"Retrieved {len(recent_requests)} recent requests")
        
        # Prepare context for template
        context = {
            'active_requests': active_requests,
            'completed_requests': completed_requests,
            'documents_count': documents_count,
            'notifications': notifications,
            'unread_notifications_count': unread_notifications_count,
            'upcoming_appointments': upcoming_appointments,
            'available_services': services_with_icons,
            'recent_documents': recent_documents,
            'recent_requests': recent_requests,
            'resources_count': 8,  # Placeholder value - replace with actual count when Resource model is available
            'client': client_profile,
            'user': request.user
        }
        
        print("Rendering dashboard with context")
        return render(request, 'client/dashboard.html', context)
        
    except Exception as e:
        # Log any other exceptions
        print(f"Error in client_dashboard_view: {str(e)}")
        return render(request, 'client/dashboard.html', {'error': str(e)})

@login_required
def expert_dashboard_view(request):
    """
    View function for the expert dashboard.
    
    This view acts as the central hub for experts to view their assigned service requests,
    documents, upcoming appointments, and notifications. It provides:
    - Counts of active and completed service requests
    - Count of available documents
    - Recent notifications with unread notification count
    - List of upcoming appointments
    - Available services that the expert can provide
    - Recent documents uploaded by or for the expert
    - Recent service requests assigned to the expert
    
    Args:
        request: The HTTP request object
        
    Returns:
        Rendered dashboard template with context data or redirects to home if expert profile not found
    """
    print(f"Starting expert_dashboard_view for user {request.user.email}")
    
    try:
        # Check if account type is expert - case insensitive
        if request.user.account_type.lower() != 'expert':
            print(f"User account type is {request.user.account_type}, not expert. Redirecting to home.")
            return redirect('home')
            
        # Get expert profile
        expert_profile = Expert.objects.get(user=request.user)
        print(f"Found expert profile for {expert_profile}")
        
        # Count of total service requests
        total_requests = ServiceRequest.objects.filter(
            expert=expert_profile.user
        ).count()
        print(f"Total requests count: {total_requests}")
        
        # Count of pending service requests
        pending_requests = ServiceRequest.objects.filter(
            expert=expert_profile.user,
            status__in=['new', 'pending', 'pending_info']
        ).count()
        print(f"Pending requests count: {pending_requests}")
        
        # Count of completed service requests
        completed_requests = ServiceRequest.objects.filter(
            expert=expert_profile.user,
            status='completed'
        ).count()
        print(f"Completed requests count: {completed_requests}")
        
        # Count of documents
        documents_count = Document.objects.filter(
            Q(service_request__expert=expert_profile.user) |
            Q(rendez_vous__expert=expert_profile.user) |
            Q(uploaded_by=request.user)
        ).distinct().count()
        print(f"Documents count: {documents_count}")
        
        # Get recent notifications
        notifications = Notification.objects.filter(
            user=request.user
        ).order_by('-created_at')[:5]
        print(f"Retrieved {len(notifications)} notifications")
        
        # Count unread notifications
        unread_notifications_count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()
        print(f"Unread notifications count: {unread_notifications_count}")
        
        # Get upcoming appointments
        upcoming_appointments = RendezVous.objects.filter(
            expert=expert_profile.user,
            date_time__gte=timezone.now(),
            status__in=['scheduled', 'confirmed']
        ).order_by('date_time')[:3]
        print(f"Retrieved {len(upcoming_appointments)} upcoming appointments")
        
        # Count upcoming appointments
        upcoming_appointments_count = RendezVous.objects.filter(
            expert=expert_profile.user,
            date_time__gte=timezone.now(),
            status__in=['scheduled', 'confirmed']
        ).count()
        print(f"Upcoming appointments count: {upcoming_appointments_count}")
        
        # Get services related to this expert's specialty
        expert_services = Service.objects.filter(
            is_active=True,
            service_type__category__name__icontains=expert_profile.specialty
        ).select_related('service_type__category')
        print(f"Retrieved {len(expert_services)} expert services")
        
        # Enrich services with icons
        services_with_icons = []
        for service in expert_services:
            service.icon = get_service_icon(service)
            services_with_icons.append(service)
        
        # Get recent documents
        recent_documents = Document.objects.filter(
            Q(service_request__expert=expert_profile.user) |
            Q(rendez_vous__expert=expert_profile.user) |
            Q(uploaded_by=request.user)
        ).distinct().order_by('-upload_date')[:3]
        print(f"Retrieved {len(recent_documents)} recent documents")
        
        # Get recent service requests
        recent_requests = ServiceRequest.objects.filter(
            expert=expert_profile.user
        ).order_by('-created_at')[:3]
        print(f"Retrieved {len(recent_requests)} recent requests")
        
        # Prepare context for template
        context = {
            'total_requests': total_requests,
            'pending_requests': pending_requests,
            'completed_requests': completed_requests,
            'upcoming_appointments': upcoming_appointments_count,
            'documents_count': documents_count,
            'notifications': notifications,
            'unread_notifications_count': unread_notifications_count,
            'upcoming_appointments_list': upcoming_appointments,
            'expert_services': services_with_icons,
            'recent_documents': recent_documents,
            'recent_requests': recent_requests,
            'resources_count': 8,  # Placeholder value - replace with actual count when Resource model is available
            'expert': expert_profile,
            'user': request.user
        }
        
        print("Rendering dashboard with context")
        return render(request, 'expert/dashboard.html', context)
        
    except Expert.DoesNotExist:
        # If expert profile doesn't exist, redirect to home
        print(f"Expert profile not found for user {request.user.email}, redirecting to home")
        return redirect('home')
    except Exception as e:
        # Log any other exceptions
        print(f"Error in expert_dashboard_view: {str(e)}")
        return render(request, 'expert/dashboard.html', {'error': str(e)})

@login_required
def admin_dashboard_view(request):
    """View function for the admin dashboard."""
    # Check if account type is admin - case insensitive
    if not request.user.is_authenticated or request.user.account_type.lower() != 'admin':
        print(f"User account type is {getattr(request.user, 'account_type', 'not authenticated')}, not admin. Redirecting to admin login.")
        return redirect('accounts:admin_login_view')
    
    try:
        from django.db.models import Count
        from django.utils import timezone
        from datetime import timedelta
        from accounts.models import Utilisateur, Client, Expert
        from resources.models import Resource
        from custom_requests.models import ServiceRequest, RendezVous, Document, Message
        
        # Get user statistics
        total_users = Utilisateur.objects.count()
        total_clients = Client.objects.count()
        total_experts = Expert.objects.count()
        total_admins = Utilisateur.objects.filter(account_type__iexact='admin').count()
        
        # Get service statistics
        total_requests = ServiceRequest.objects.count()
        pending_requests = ServiceRequest.objects.filter(status__in=['new', 'pending_info']).count()
        completed_requests = ServiceRequest.objects.filter(status='completed').count()
        
        # Get appointment statistics
        total_appointments = RendezVous.objects.count()
        upcoming_appointments = RendezVous.objects.filter(
            date_time__gte=timezone.now()
        ).count()
        
        # Get document statistics
        total_documents = Document.objects.count()
        
        # Get resource statistics
        total_resources = Resource.objects.count()
        
        # Get recent activity
        recent_users = Utilisateur.objects.order_by('-date_joined')[:5]
        recent_requests = ServiceRequest.objects.order_by('-created_at')[:5]
        recent_appointments = RendezVous.objects.order_by('-created_at')[:5]
        
        # Activity by date (last 7 days)
        today = timezone.now().date()
        last_week = today - timedelta(days=7)
        
        # Daily signups for the last 7 days
        daily_signups = []
        for i in range(7):
            day = last_week + timedelta(days=i+1)
            count = Utilisateur.objects.filter(
                date_joined__year=day.year,
                date_joined__month=day.month,
                date_joined__day=day.day
            ).count()
            daily_signups.append({'date': day.strftime('%d/%m'), 'count': count})        # Get services data for chart
        from services.models import Service
        service_requests = ServiceRequest.objects.values('service__title').annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        
        # Rename the field for template compatibility
        service_requests_data = [
            {
                'name': item['service__title'] or 'Unknown Service',
                'count': item['count']
            }
            for item in service_requests        ]
        
        context = {
            'user': request.user,
            # Direct variables for the template
            'total_users': total_users,
            'total_clients': total_clients,
            'total_experts': total_experts,
            'total_admins': total_admins,
            'total_requests': total_requests,
            'pending_requests': pending_requests,
            'completed_requests': completed_requests,
            'total_appointments': total_appointments,            'recent_users': recent_users,
            'recent_requests': recent_requests,
            'service_requests': service_requests_data,
            'daily_signups': daily_signups,
            'user_type_counts': {
                'client': total_clients,
                'expert': total_experts,
                'admin': total_admins
            },
            # Keep the original structured data as well
            'stats': {
                'users': {
                    'total': total_users,
                    'clients': total_clients,
                    'experts': total_experts,
                    'admins': total_admins
                },
                'services': {
                    'total': total_requests,
                    'pending': pending_requests,
                    'completed': completed_requests
                },
                'appointments': {
                    'total': total_appointments,
                    'upcoming': upcoming_appointments
                },
                'documents': total_documents,
                'resources': total_resources
            },
            'recent': {
                'users': recent_users,
                'requests': recent_requests,
                'appointments': recent_appointments
            },
            'charts': {
                'daily_signups': daily_signups
            }
        }
        return render(request, 'admin/dashboard.html', context)
    
    except Exception as e:
        # Log any exceptions
        print(f"Error in admin_dashboard_view: {str(e)}")
        context = {
            'user': request.user,
            'error': str(e)
        }
        return render(request, 'admin/dashboard.html', context)