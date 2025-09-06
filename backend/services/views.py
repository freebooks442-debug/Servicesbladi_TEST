from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.csrf import csrf_exempt
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings

from .models import ServiceCategory, ServiceType, Service, TourismService, AdministrativeService
from .models import InvestmentService, RealEstateService, FiscalService
from accounts.models import Expert, Utilisateur

def all_services_view(request):
    """View for the main services page showing all categories"""
    categories = ServiceCategory.objects.all()
    
    # If no categories exist yet, create default ones
    if not categories.exists():
        categories = create_default_categories()
    
    featured_services = Service.objects.filter(
        is_active=True
    ).select_related('expert', 'expert__user', 'service_type')[:6]
    
    context = {
        'categories': categories,
        'featured_services': featured_services,
        'page_title': 'Our Services'
    }
    
    return render(request, 'general/index.html', context)

def create_default_categories():
    """Helper function to create default service categories"""
    categories = [
        {
            'name': 'Tourism',
            'name_fr': 'Tourisme',
            'name_ar': 'سياحة',
            'description': 'Explore Morocco through our guided tours and experiences',
            'description_fr': 'Explorez le Maroc à travers nos visites guidées et expériences',
            'description_ar': 'اكتشف المغرب من خلال جولاتنا وتجاربنا المصحوبة بمرشدين',
            'slug': 'tourism',
            'icon': 'bi bi-globe'
        },
        {
            'name': 'Administrative',
            'name_fr': 'Administratif',
            'name_ar': 'إداري',
            'description': 'Administrative procedures and document processing services',
            'description_fr': 'Procédures administratives et services de traitement de documents',
            'description_ar': 'الإجراءات الإدارية وخدمات معالجة المستندات',
            'slug': 'administrative',
            'icon': 'bi bi-file-earmark-text'
        },
        {
            'name': 'Fiscal',
            'name_fr': 'Fiscal',
            'name_ar': 'ضريبي',
            'description': 'Tax planning and fiscal advisory services',
            'description_fr': 'Services de planification fiscale et de conseil',
            'description_ar': 'خدمات التخطيط الضريبي والاستشارات المالية',
            'slug': 'fiscal',
            'icon': 'bi bi-calculator'
        },
        {
            'name': 'Real Estate',
            'name_fr': 'Immobilier',
            'name_ar': 'عقارات',
            'description': 'Real estate consulting and property management services',
            'description_fr': "Services de conseil immobilier et de gestion de propriétés",
            'description_ar': 'خدمات استشارات العقارات وإدارة الممتلكات',
            'slug': 'real-estate',
            'icon': 'bi bi-house'
        },
        {
            'name': 'Investment',
            'name_fr': 'Investissement',
            'name_ar': 'استثمار',
            'description': 'Investment opportunities and financial advisory services',
            'description_fr': "Opportunités d'investissement et services de conseil financier",
            'description_ar': 'فرص الاستثمار وخدمات الاستشارات المالية',
            'slug': 'investment',
            'icon': 'bi bi-graph-up-arrow'
        },
    ]
    
    created_categories = []
    for cat_data in categories:
        category = ServiceCategory.objects.create(**cat_data)
        created_categories.append(category)
    
    return created_categories

def tourism_services_view(request):
    """View for tourism services"""
    tourism_services = TourismService.objects.filter(is_active=True)
    
    context = {
        'services': tourism_services,
        'title': 'Services Touristiques',
        'description': 'Découvrez nos services d\'accompagnement pour vos voyages au Maroc',
    }
    
    return render(request, 'general/Tourisme.html', context)

def administrative_services_view(request):
    """View for administrative services"""
    admin_services = AdministrativeService.objects.filter(is_active=True)
    
    context = {
        'services': admin_services,
        'title': 'Services Administratifs',
        'description': 'Simplifiez vos démarches administratives au Maroc',
    }
    
    return render(request, 'general/Administrative.html', context)

def fiscal_services_view(request):
    """View for fiscal services"""
    fiscal_services = FiscalService.objects.filter(is_active=True)
    
    context = {
        'services': fiscal_services,
        'title': 'Services Fiscaux',
        'description': 'Optimisez votre situation fiscale entre votre pays de résidence et le Maroc',
    }
    
    return render(request, 'general/Fiscale.html', context)

def real_estate_services_view(request):
    """View for real estate services"""
    real_estate_services = RealEstateService.objects.filter(is_active=True)
    
    context = {
        'services': real_estate_services,
        'title': 'Services Immobiliers',
        'description': 'Trouvez, achetez ou gérez votre bien immobilier au Maroc',
    }
    
    return render(request, 'general/Immobilier.html', context)

def investment_services_view(request):
    """View for investment services"""
    investment_services = InvestmentService.objects.filter(is_active=True)
    
    context = {
        'services': investment_services,
        'title': 'Services d\'Investissement',
        'description': 'Accompagnement dans vos projets d\'investissement au Maroc',
    }
    
    return render(request, 'general/Investisment.html', context)

def contact_view(request):
    """View for contact page and form handling"""
    if request.method == 'POST':
        try:
            # Récupérer les données du formulaire
            name = request.POST.get('name', '').strip()
            email = request.POST.get('email', '').strip()
            subject = request.POST.get('subject', '').strip()
            message_text = request.POST.get('message', '').strip()
            
            # Validation basique
            if not all([name, email, subject, message_text]):
                # Si c'est une requête AJAX, renvoyer une erreur
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return HttpResponse('Tous les champs sont requis.', status=400)
                messages.error(request, 'Tous les champs sont requis.')
                return render(request, 'general/contact.html')
            
            # Import ContactMessage model
            from custom_requests.models import ContactMessage
            from accounts.models import Utilisateur
            
            # Sauvegarder le message dans la base de données
            contact_message = ContactMessage.objects.create(
                name=name,
                email=email,
                subject=subject,
                message=message_text
            )
            
            # Envoyer TOUJOURS à l'adresse de contact définie
            expert_emails = [getattr(settings, 'SERVICESBLADI_CONTACT_EMAIL', settings.DEFAULT_FROM_EMAIL)]
            
            # Préparer le contenu de l'email pour les experts
            email_subject = f"Nouveau message de contact ServicesBladi: {subject}"
            email_message = f"""
Nouveau message de contact reçu sur ServicesBladi:

Nom: {name}
Email: {email}
Sujet: {subject}

Message:
{message_text}

---
Envoyé le: {contact_message.created_at.strftime('%d/%m/%Y à %H:%M')}
ID du message: {contact_message.id}

Vous pouvez répondre directement à cette personne à l'adresse: {email}
            """
              # Envoyer l'email aux experts
            try:
                send_mail(
                    subject=email_subject,
                    message=email_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=expert_emails,
                    fail_silently=False,
                )
                
            except Exception as e:
                # Continue même si l'email échoue
                print(f"Erreur d'envoi d'email de contact: {e}")
            
            # Si c'est une requête AJAX, renvoyer "OK"
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return HttpResponse('OK')
            
            # Sinon, rediriger avec un message de succès
            messages.success(request, 'Votre message a été envoyé avec succès! Nous vous répondrons dans les plus brefs délais.')
                
        except Exception as e:
            # Si c'est une requête AJAX, renvoyer une erreur
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return HttpResponse('Une erreur est survenue lors de l\'envoi de votre message.', status=500)
            
            messages.error(request, 'Une erreur est survenue lors de l\'envoi de votre message. Veuillez réessayer.')
            print(f"Erreur de traitement du formulaire de contact: {e}")
            
        return redirect('contact')
    
    return render(request, 'general/contact.html')
