from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q

from custom_requests.models import Notification


@login_required
@require_http_methods(["GET"])
def get_notifications(request):
    """API endpoint to get user notifications with pagination"""
    try:
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 10))
        
        notifications = Notification.objects.filter(
            user=request.user
        ).order_by('-created_at')
        
        paginator = Paginator(notifications, per_page)
        page_obj = paginator.get_page(page)
        
        notifications_data = []
        for notification in page_obj:
            notifications_data.append({
                'id': notification.id,
                'type': notification.type,
                'title': notification.title,
                'content': notification.content,
                'is_read': notification.is_read,
                'created_at': notification.created_at.isoformat(),
                'time_ago': get_time_ago(notification.created_at),
                'icon': get_notification_icon(notification.type),
                'color': get_notification_color(notification.type),
                'redirect_url': notification.get_redirect_url(),
            })
        
        return JsonResponse({
            'success': True,
            'notifications': notifications_data,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
            'total_count': paginator.count,
            'unread_count': notifications.filter(is_read=False).count()
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def mark_notification_read(request, notification_id):
    """Mark a specific notification as read"""
    try:
        notification = Notification.objects.get(
            id=notification_id,
            user=request.user
        )
        notification.is_read = True
        notification.save()
        
        return JsonResponse({
            'success': True,
            'message': _('Notification marked as read')
        })
        
    except Notification.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': _('Notification not found')
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def mark_all_notifications_read(request):
    """Mark all user notifications as read"""
    try:
        updated_count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).update(is_read=True)
        
        return JsonResponse({
            'success': True,
            'message': _('All notifications marked as read'),
            'updated_count': updated_count
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
@require_http_methods(["DELETE"])
def delete_notification(request, notification_id):
    """Delete a specific notification"""
    try:
        notification = Notification.objects.get(
            id=notification_id,
            user=request.user
        )
        notification.delete()
        
        return JsonResponse({
            'success': True,
            'message': _('Notification deleted')
        })
        
    except Notification.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': _('Notification not found')
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def notification_counts(request):
    """Get notification counts for the user"""
    try:
        unread_count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()
        
        total_count = Notification.objects.filter(
            user=request.user
        ).count()
        
        return JsonResponse({
            'success': True,
            'unread_count': unread_count,
            'total_count': total_count
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def notification_click(request, notification_id):
    """Handle notification click and redirect"""
    try:
        notification = Notification.objects.get(
            id=notification_id,
            user=request.user
        )
        
        # Mark notification as read if not already
        if not notification.is_read:
            notification.is_read = True
            notification.save()
        
        # Return redirect URL
        return JsonResponse({
            'success': True,
            'redirect_url': notification.get_redirect_url(),
            'message': _('Notification marked as read')
        })
        
    except Notification.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': _('Notification not found')
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


def get_notification_icon(notification_type):
    """Get the appropriate icon for notification type"""
    icons = {
        'info': '<i class="bi bi-info-circle text-sm"></i>',
        'success': '<i class="bi bi-check-circle text-sm"></i>',
        'warning': '<i class="bi bi-exclamation-triangle text-sm"></i>',
        'error': '<i class="bi bi-x-circle text-sm"></i>',
        'request_update': '<i class="bi bi-file-text text-sm"></i>',
        'appointment': '<i class="bi bi-calendar-event text-sm"></i>',
        'appointment_update': '<i class="bi bi-calendar-check text-sm"></i>',
        'message': '<i class="bi bi-chat-dots text-sm"></i>',
        'document': '<i class="bi bi-file-earmark-pdf text-sm"></i>',
        'system': '<i class="bi bi-gear text-sm"></i>',
        'request': '<i class="bi bi-file-earmark-text text-sm"></i>',
    }
    return icons.get(notification_type, '<i class="bi bi-bell text-sm"></i>')


def get_notification_color(notification_type):
    """Get the appropriate color class for notification type"""
    colors = {
        'info': 'bg-blue-500',
        'success': 'bg-green-500',
        'warning': 'bg-yellow-500',
        'error': 'bg-red-500',
        'request_update': 'bg-blue-500',
        'appointment': 'bg-green-500',
        'appointment_update': 'bg-yellow-500',
        'message': 'bg-purple-500',
        'document': 'bg-red-500',
        'system': 'bg-gray-500',
        'request': 'bg-teal-500',
    }
    return colors.get(notification_type, 'bg-blue-500')


def get_time_ago(created_at):
    """Get human readable time ago"""
    now = timezone.now()
    diff = now - created_at
    
    if diff.days > 0:
        return f"il y a {diff.days} jour{'s' if diff.days > 1 else ''}"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"il y a {hours} heure{'s' if hours > 1 else ''}"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"il y a {minutes} minute{'s' if minutes > 1 else ''}"
    else:
        return "à l'instant"


def create_notification(user, notification_type, title, content, related_object=None):
    """Helper function to create notifications"""
    notification_data = {
        'user': user,
        'type': notification_type,
        'title': title,
        'content': content,
    }
    
    # Add related object based on type
    if related_object:
        if hasattr(related_object, 'service_type'):  # ServiceRequest
            notification_data['related_service_request'] = related_object
        elif hasattr(related_object, 'date_time'):  # RendezVous
            notification_data['related_rendez_vous'] = related_object
        elif hasattr(related_object, 'content'):  # Message
            notification_data['related_message'] = related_object
    
    return Notification.objects.create(**notification_data)
