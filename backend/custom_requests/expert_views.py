from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q, Count
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

from accounts.models import Utilisateur, Expert, Client
from custom_requests.models import ServiceRequest, Document, RendezVous, Message, Notification
from services.email_notifications import EmailNotificationService

@login_required
def expert_documents_view(request):
    """View function for expert document management."""
    if request.user.account_type.lower() != 'expert':
        return redirect('home')

    try:
        expert = Expert.objects.get(user=request.user)
        
        # Get documents associated with this expert
        documents = Document.objects.filter(
            Q(service_request__expert=expert.user) |
            Q(rendez_vous__expert=expert.user) |
            Q(uploaded_by=request.user)
        ).distinct().order_by('-upload_date')
        
        # Get this expert's requests for the dropdown
        my_requests = ServiceRequest.objects.filter(expert=expert.user).order_by('-created_at')
        
        context = {
            'documents': documents,
            'expert': expert,
            'my_requests': my_requests
        }
        
        return render(request, 'expert/documents.html', context)
    
    except Expert.DoesNotExist:
        return redirect('home')

@login_required
def expert_appointments_view(request):
    """View function for expert appointments."""
    if request.user.account_type.lower() != 'expert':
        return redirect('home')
        
    try:
        expert = Expert.objects.get(user=request.user)
        # Get appointments for this expert
        appointments = RendezVous.objects.filter(
            expert=expert.user
        ).order_by('date_time')
        
        # Get all clients for the form dropdown
        clients = Client.objects.all()
        
        context = {
            'appointments': appointments,
            'expert': expert,
            'clients': clients        }
        
        return render(request, 'expert/rendezvous.html', context)
    
    except Expert.DoesNotExist:
        return redirect('home')

@login_required
def expert_messages_view(request):
    """View function for expert messages."""
    if request.user.account_type.lower() != 'expert':
        return redirect('home')

    try:
        expert = Expert.objects.get(user=request.user)
        
        # Get all clients who have had appointments or service requests with this expert
        clients = Client.objects.filter(
            Q(servicerequest__expert=expert.user) |
            Q(rendezvous__expert=expert.user)
        ).distinct()
        
        # Get active client if any
        active_client_id = request.GET.get('client')
        active_client = None
        messages = []
        
        if active_client_id:
            active_client = get_object_or_404(Client, id=active_client_id)
            
            # Get messages between expert and client
            messages = Message.objects.filter(
                (Q(sender=request.user) & Q(recipient=active_client.user)) |
                (Q(sender=active_client.user) & Q(recipient=request.user))
            ).order_by('sent_at')
            
            # Mark messages as read
            unread_messages = messages.filter(recipient=request.user, is_read=False)
            for message in unread_messages:
                message.is_read = True
                message.save()
        
        context = {
            'clients': clients,
            'active_client': active_client,
            'messages': messages,
            'expert': expert
        }
        
        return render(request, 'expert/messages.html', context)
    
    except Expert.DoesNotExist:
        return redirect('home')

@login_required
def expert_appointment_detail(request, appointment_id):
    """View function for expert appointment detail."""
    if request.user.account_type.lower() != 'expert':
        return redirect('home')

    try:
        expert = Expert.objects.get(user=request.user)
        
        # Get appointment details
        appointment = get_object_or_404(RendezVous, id=appointment_id, expert=expert.user)
        
        # Get documents related to this appointment
        documents = Document.objects.filter(rendez_vous=appointment).order_by('-upload_date')
        
        context = {
            'appointment': appointment,
            'documents': documents,
            'expert': expert
        }
        
        return render(request, 'expert/appointment_detail.html', context)
    
    except Expert.DoesNotExist:
        return redirect('home')

@login_required
def expert_requests_view(request):
    """View function for expert requests."""
    if request.user.account_type.lower() != 'expert':
        return redirect('home')

    try:
        expert = Expert.objects.get(user=request.user)
        
        # Get ALL service requests so experts can see everything
        all_requests = ServiceRequest.objects.all().order_by('-created_at')
        
        # Separate them by assignment status for display
        assigned_to_me = all_requests.filter(expert=expert.user)
        assigned_to_others = all_requests.filter(expert__isnull=False).exclude(expert=expert.user)
        unassigned = all_requests.filter(expert__isnull=True)
        
        context = {
            'requests': all_requests,  # All requests for the main display
            'assigned_to_me': assigned_to_me,
            'assigned_to_others': assigned_to_others,
            'unassigned': unassigned,
            'expert': expert
        }
        
        return render(request, 'expert/demandes.html', context)
    
    except Expert.DoesNotExist:
        return redirect('home')

@login_required
def expert_resources_view(request):
    """View function for expert resources."""
    print(f"=== EXPERT RESOURCES VIEW DEBUG ===")
    print(f"User: {request.user}")
    print(f"Is authenticated: {request.user.is_authenticated}")
    print(f"Account type: {getattr(request.user, 'account_type', 'No account_type')}")
    
    if request.user.account_type.lower() not in ['expert', 'admin']:
        print(f"Access denied - redirecting to home")
        return redirect('home')

    try:
        if request.user.account_type.lower() == 'expert':
            expert = Expert.objects.get(user=request.user)
            print(f"Expert found: {expert}")
        else:
            expert = None
            print(f"Admin user - no expert profile needed")
        
        # Import here to avoid circular import
        from resources.models import Resource, ResourceFile, ResourceLink
        
        # Get filter parameters
        category = request.GET.get('category', '')
        search_query = request.GET.get('search', '')
        sort_by = request.GET.get('sort', 'recent')
        
        # Base queryset
        resources = Resource.objects.all()
        
        # Apply filters
        if category:
            resources = resources.filter(category=category)
            
        if search_query:
            resources = resources.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        
        # Apply sorting
        if sort_by == 'name':
            resources = resources.order_by('title')
        elif sort_by == 'popular':
            resources = resources.order_by('-view_count')
        else:  # default to recent
            resources = resources.order_by('-created_at')
        
        # Get resource categories for filtering
        resource_categories = Resource.CATEGORIES
        
        context = {
            'resources': resources,
            'expert': expert,
            'resource_categories': resource_categories,
            'formats': Resource.FORMAT_TYPES,
            'current_category': category,
            'current_search': search_query,
            'current_sort': sort_by
        }
        
        return render(request, 'expert/ressources.html', context)
    
    except Expert.DoesNotExist:
        messages.error(request, _('Expert profile not found.'))
        return redirect('home')
    except Exception as e:
        messages.error(request, _(f'An error occurred: {str(e)}'))
        return redirect('home')

@login_required
def expert_request_detail(request, request_id):
    """View to display detailed information about a specific service request for expert"""
    
    # Check if user is expert
    if request.user.account_type.lower() != 'expert':
        return redirect('home')
    
    try:        # Get the service request
        service_request = get_object_or_404(ServiceRequest, id=request_id)
        
        # Get client information including phone number
        client = get_object_or_404(Utilisateur, id=service_request.client.id)
        
        # Get service type information
        service = service_request.service
        service_type = service.service_type if hasattr(service, 'service_type') else None
        
        # Get documents for this service request
        documents = Document.objects.filter(service_request=service_request).order_by('-upload_date')
        
        # Get messages related to this service request
        messages_list = Message.objects.filter(service_request=service_request).order_by('sent_at')
        
        # Get appointments related to this service request
        appointments = RendezVous.objects.filter(service_request=service_request).order_by('date_time')
        
        context = {
            'service_request': service_request,
            'documents': documents,
            'messages_list': messages_list,
            'appointments': appointments,
            'client': client,
            'service_type': service_type        }
        
        return render(request, 'expert/request_detail.html', context)
    
    except Exception as e:
        messages.error(request, f"Erreur: {str(e)}")
        return redirect('expert_demandes')

@login_required
def expert_send_message(request):
    """Handle sending a message from expert to client or admin"""
    
    # Check if user is expert
    if request.user.account_type.lower() != 'expert':
        return redirect('home')
    
    if request.method != 'POST':
        return redirect('expert_demandes')
    
    try:
        # Get form data
        recipient_id = request.POST.get('recipient_id')
        content = request.POST.get('content')
        service_request_id = request.POST.get('service_request_id')
        
        if not recipient_id or not content:
            messages.error(request, "Le destinataire et le contenu sont obligatoires.")
            if service_request_id:
                return redirect('expert_request_detail', request_id=service_request_id)
            return redirect('expert_demandes')
        
        # Get the recipient
        recipient = get_object_or_404(Utilisateur, id=recipient_id)
        
        # Get the service request if available
        service_request = None
        if service_request_id:
            service_request = get_object_or_404(ServiceRequest, id=service_request_id)
            
            # Check if this expert is assigned to this request
            if service_request.expert != request.user:
                messages.error(request, "Vous n'êtes pas autorisé à envoyer des messages pour cette demande.")
                return redirect('expert_demandes')
        
        # Create the message
        message = Message.objects.create(
            sender=request.user,
            recipient=recipient,
            content=content,
            service_request=service_request
        )
        
        # Create notification for recipient
        Notification.objects.create(
            user=recipient,
            type='message',
            title=_('Nouveau message'),
            content=_(f'Vous avez reçu un nouveau message de {request.user.first_name} {request.user.name}.'),
            related_message=message,
            related_service_request=service_request
        )
        
        messages.success(request, _('Message envoyé avec succès.'))
        
        # Redirect back to appropriate page
        if service_request_id:
            return redirect('expert_request_detail', request_id=service_request_id)
        return redirect('expert_demandes')
        
    except Exception as e:
        messages.error(request, f"Erreur lors de l'envoi du message: {str(e)}")
        if service_request_id:
            return redirect('expert_request_detail', request_id=service_request_id)
        return redirect('expert_demandes')

@login_required
def expert_upload_document(request):
    """Handle document upload from expert"""
    
    # Check if user is expert
    if request.user.account_type.lower() != 'expert':
        return redirect('home')
    
    if request.method != 'POST':
        return redirect('expert_demandes')
    
    # Check if this is an AJAX request
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', '')
    
    try:
        # Get form data
        name = request.POST.get('name')
        document_type = request.POST.get('type')
        service_request_id = request.POST.get('service_request_id')
        
        if not name or not document_type or not service_request_id or 'file' not in request.FILES:
            error_msg = "Tous les champs sont obligatoires (nom, type, demande et fichier)."
            if is_ajax:
                return JsonResponse({'success': False, 'message': error_msg})
            
            messages.error(request, error_msg)
            return redirect('custom_requests:expert_documents')
        
        # Get the service request
        try:
            service_request = get_object_or_404(ServiceRequest, id=service_request_id)
            
            # Check if this expert is assigned to this request
            if service_request.expert != request.user:
                error_msg = "Vous n'êtes pas autorisé à télécharger des documents pour cette demande."
                if is_ajax:
                    return JsonResponse({'success': False, 'message': error_msg})
                
                messages.error(request, error_msg)
                return redirect('custom_requests:expert_documents')
        except:
            error_msg = "Demande non trouvée."
            if is_ajax:
                return JsonResponse({'success': False, 'message': error_msg})
            
            messages.error(request, error_msg)
            return redirect('custom_requests:expert_documents')
        
        # Get the file
        file = request.FILES['file']
        
        # Create the document
        document = Document.objects.create(
            name=name,
            type=document_type,
            service_request=service_request,
            uploaded_by=request.user,
            file=file
        )
        
        # Create notification for client
        notification = Notification.objects.create(
            user=service_request.client,
            type='document',
            title='Nouveau document',
            content=f'Un nouveau document "{name}" a été téléchargé pour votre demande "{service_request.title}".',
            related_service_request=service_request
        )
        
        # Send email notification to client (if service exists)
        try:
            EmailNotificationService.send_document_uploaded_notification(
                request.user, service_request.client, document, service_request
            )
        except Exception as email_error:
            pass  # Fail silently if email service is not available
        
        success_msg = 'Document téléchargé avec succès.'
        
        if is_ajax:
            return JsonResponse({'success': True, 'message': success_msg})
        
        messages.success(request, success_msg)
        
        # Redirect to the request detail page
        if service_request_id:
            return redirect('expert_request_detail', request_id=service_request_id)
        else:
            return redirect('custom_requests:expert_documents')
        
    except Exception as e:
        error_msg = f"Erreur lors du téléchargement du document: {str(e)}"
        
        if is_ajax:
            return JsonResponse({'success': False, 'message': error_msg})
        
        messages.error(request, error_msg)
        if 'service_request_id' in locals() and service_request_id:
            return redirect('expert_request_detail', request_id=service_request_id)
        return redirect('custom_requests:expert_documents')

@login_required
def expert_update_request_status(request, request_id):
    """Update the status of a service request by expert"""
    
    # Check if user is expert
    if request.user.account_type.lower() != 'expert':
        return redirect('home')
    
    if request.method != 'POST':
        return redirect('expert_request_detail', request_id=request_id)
    
    try:
        # Get the service request
        service_request = get_object_or_404(ServiceRequest, id=request_id)
        
        # Check if this expert is assigned to this request
        if service_request.expert != request.user:
            messages.error(request, "Vous n'êtes pas autorisé à mettre à jour cette demande.")
            return redirect('expert_demandes')
        
        # Get the new status
        new_status = request.POST.get('status')
        comment = request.POST.get('comment', '')
        
        # Verify that the status is valid for experts
        valid_statuses = ['in_progress', 'pending_info', 'completed']
        if new_status not in valid_statuses:
            messages.error(request, "Statut invalide.")
            return redirect('expert_request_detail', request_id=request_id)
        
        # Update the request status
        service_request.status = new_status
        service_request.save()
        
        # Add comment as message if provided
        if comment:
            Message.objects.create(
                sender=request.user,
                recipient=service_request.client,
                content=_('Statut mis à jour: ') + comment,
                service_request=service_request
            )
          # Create notification for client
        status_display = dict(ServiceRequest.STATUS_CHOICES).get(new_status, new_status)
        Notification.objects.create(
            user=service_request.client,
            type='request_update',
            title=_('Statut de demande mis à jour'),
            content=_(f'Le statut de votre demande "{service_request.title}" a été mis à jour à "{status_display}".'),
            related_service_request=service_request
        )
        
        # Send email notification to client
        EmailNotificationService.send_request_status_update(
            service_request.client, request.user, service_request, new_status
        )
        
        messages.success(request, _('Statut mis à jour avec succès.'))
        
        return redirect('expert_request_detail', request_id=request_id)
        
    except Exception as e:
        messages.error(request, f"Erreur lors de la mise à jour du statut: {str(e)}")
        return redirect('expert_request_detail', request_id=request_id)

@login_required
def expert_schedule_appointment(request):
    """Handle scheduling of appointment by expert"""
    
    # Check if user is expert
    if request.user.account_type.lower() != 'expert':
        return redirect('home')
    
    if request.method != 'POST':
        return redirect('expert_demandes')
    
    try:
        # Get form data
        service_request_id = request.POST.get('service_request_id')
        date_time_str = request.POST.get('date_time')
        duration = request.POST.get('duration')
        appointment_type = request.POST.get('type')
        notes = request.POST.get('notes', '')
        
        if not service_request_id or not date_time_str or not duration or not appointment_type:
            messages.error(request, "Tous les champs sont obligatoires.")
            return redirect('expert_request_detail', request_id=service_request_id)
        
        # Get the service request
        service_request = get_object_or_404(ServiceRequest, id=service_request_id)
        
        # Check if this expert is assigned to this request
        if service_request.expert != request.user:
            messages.error(request, "Vous n'êtes pas autorisé à planifier des rendez-vous pour cette demande.")
            return redirect('expert_demandes')
        
        # Convert date_time from string to datetime
        from datetime import datetime
        date_time = datetime.strptime(date_time_str, '%Y-%m-%dT%H:%M')
        
        # Create the appointment
        appointment = RendezVous.objects.create(
            client=service_request.client,
            expert=request.user,
            service_request=service_request,
            date_time=date_time,
            duration=duration,
            type=appointment_type,
            notes=notes,
            status='scheduled'
        )
          # Create notification for client
        Notification.objects.create(
            user=service_request.client,
            type='appointment',
            title=_('Nouveau rendez-vous'),
            content=_(f'Un rendez-vous a été planifié pour votre demande "{service_request.title}" le {date_time.strftime("%d/%m/%Y à %H:%M")}.'),
            related_service_request=service_request
        )
        
        # Send email notification to client about new appointment
        EmailNotificationService.send_appointment_notification(
            client=service_request.client,
            expert=request.user,
            appointment=appointment,
            notification_type='created'
        )
        
        messages.success(request, _('Rendez-vous planifié avec succès.'))
        
        return redirect('expert_request_detail', request_id=service_request_id)
        
    except Exception as e:
        messages.error(request, f"Erreur lors de la planification du rendez-vous: {str(e)}")
        if service_request_id:
            return redirect('expert_request_detail', request_id=service_request_id)
        return redirect('expert_demandes')

@login_required
def expert_update_appointment(request):
    """Handle updating of appointment status by expert"""
    
    # Check if user is expert
    if request.user.account_type.lower() != 'expert':
        return redirect('home')
    
    if request.method != 'POST':
        return redirect('expert_demandes')
    
    try:
        # Get form data
        appointment_id = request.POST.get('appointment_id')
        status = request.POST.get('status')
        
        if not appointment_id or not status:
            messages.error(request, "L'identifiant du rendez-vous et le statut sont obligatoires.")
            return redirect('expert_demandes')
        
        # Get the appointment
        appointment = get_object_or_404(RendezVous, id=appointment_id)
        
        # Check if this expert is assigned to this appointment
        if appointment.expert != request.user:
            messages.error(request, "Vous n'êtes pas autorisé à mettre à jour ce rendez-vous.")
            return redirect('expert_demandes')
        
        # Check if status is valid
        if status not in ['completed', 'cancelled']:
            messages.error(request, "Statut invalide.")
            return redirect('expert_request_detail', request_id=appointment.service_request.id)
        
        # Update the appointment status
        appointment.status = status
        appointment.save()
          # Create notification for client
        status_display = 'terminé' if status == 'completed' else 'annulé'
        Notification.objects.create(
            user=appointment.client,
            type='appointment_update',
            title=_('Statut de rendez-vous mis à jour'),
            content=_(f'Votre rendez-vous du {appointment.date_time.strftime("%d/%m/%Y à %H:%M")} a été marqué comme {status_display}.'),
            related_service_request=appointment.service_request
        )
        
        # Send email notification to client about appointment status update
        if status == 'completed':
            # Use document upload template for completed appointments since we don't have a specific completion template
            EmailNotificationService.send_request_status_update(
                client=appointment.client,
                request_obj=appointment.service_request if appointment.service_request else None,
                new_status='completed',
                updated_by=request.user
            )
        elif status == 'cancelled':
            # For cancelled appointments, we'll use the appointment notification with a custom message
            context = {
                'client_name': f"{appointment.client.name} {appointment.client.first_name}",
                'expert_name': f"{request.user.name} {request.user.first_name}",
                'appointment_date': appointment.date_time.strftime("%d/%m/%Y"),
                'appointment_time': appointment.date_time.strftime("%H:%M"),
                'cancellation_reason': 'Annulé par l\'expert',
                'site_name': 'Services Bladi',
                'site_url': 'https://servicesbladi.com'
            }
            
            EmailNotificationService.send_templated_email(
                'appointment_cancelled',
                context,
                _("Rendez-vous annulé"),
                appointment.client.email
            )
        
        messages.success(request, _(f'Rendez-vous marqué comme {status_display} avec succès.'))
        
        return redirect('expert_request_detail', request_id=appointment.service_request.id)
        
    except Exception as e:
        messages.error(request, f"Erreur lors de la mise à jour du rendez-vous: {str(e)}")
        return redirect('expert_demandes')

@login_required
def expert_take_request(request, request_id):
    """Allow expert to take an unassigned request."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Method not allowed'})
        
    if request.user.account_type.lower() != 'expert':
        return JsonResponse({'success': False, 'message': 'Access denied'})

    try:
        expert = Expert.objects.get(user=request.user)
        service_request = get_object_or_404(ServiceRequest, id=request_id)
        
        # Check if request is unassigned
        if service_request.expert is not None:
            return JsonResponse({'success': False, 'message': 'Cette demande est déjà assignée'})
        
        # Assign the request to this expert
        service_request.expert = expert.user
        service_request.save()
        
        # Create notification for client
        try:
            notification = Notification.objects.create(
                user=service_request.client,
                title="Expert assigné à votre demande",
                message=f"L'expert {expert.user.name} {expert.user.first_name} a pris en charge votre demande: {service_request.title}",
                notification_type='assignment'
            )
        except:
            pass  # Don't fail if notification creation fails
        
        return JsonResponse({'success': True, 'message': 'Demande prise en charge avec succès'})
        
    except Expert.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Profil expert non trouvé'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': 'Erreur lors de la prise en charge'})

@login_required
def expert_update_request_status(request, request_id):
    """Allow expert to update the status of their assigned request."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Method not allowed'})
        
    if request.user.account_type.lower() != 'expert':
        return JsonResponse({'success': False, 'message': 'Access denied'})

    try:
        expert = Expert.objects.get(user=request.user)
        service_request = get_object_or_404(ServiceRequest, id=request_id)
        
        # Check if request is assigned to this expert
        if service_request.expert != expert.user:
            return JsonResponse({'success': False, 'message': 'Vous n\'êtes pas assigné à cette demande'})
        
        # Parse the new status from request body
        try:
            data = json.loads(request.body)
            new_status = data.get('status')
        except:
            return JsonResponse({'success': False, 'message': 'Données invalides'})
        
        # Validate status transitions
        valid_statuses = ['new', 'pending_info', 'in_progress', 'completed', 'cancelled', 'rejected']
        if new_status not in valid_statuses:
            return JsonResponse({'success': False, 'message': 'Statut invalide'})
        
        # Check valid transitions based on current status
        current_status = service_request.status
        valid_transitions = {
            'new': ['in_progress', 'pending_info', 'rejected'],
            'pending_info': ['in_progress', 'rejected'],
            'in_progress': ['completed', 'pending_info'],
            'completed': [],  # Can't change from completed
            'cancelled': [],  # Can't change from cancelled
            'rejected': []    # Can't change from rejected
        }
        
        if new_status not in valid_transitions.get(current_status, []):
            return JsonResponse({'success': False, 'message': 'Transition de statut non autorisée'})
        
        # Update the status
        service_request.status = new_status
        service_request.updated_at = timezone.now()
        service_request.save()
        
        # Create notification for client
        status_messages = {
            'in_progress': f"Votre demande '{service_request.title}' est maintenant en cours de traitement.",
            'completed': f"Votre demande '{service_request.title}' a été terminée avec succès.",
            'pending_info': f"Des informations supplémentaires sont requises pour votre demande '{service_request.title}'.",
            'rejected': f"Votre demande '{service_request.title}' a été rejetée."
        }
        
        if new_status in status_messages:
            try:
                notification = Notification.objects.create(
                    user=service_request.client,
                    title="Mise à jour de votre demande",
                    message=status_messages[new_status],
                    notification_type='status_update'
                )
            except:
                pass  # Don't fail if notification creation fails
        
        return JsonResponse({'success': True, 'message': 'Statut mis à jour avec succès'})
        
    except Expert.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Profil expert non trouvé'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': 'Erreur lors de la mise à jour du statut'})
