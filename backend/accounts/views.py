from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, update_session_auth_hash, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse

from .models import Utilisateur, Client, Expert, Address, Notification
from .forms import UserEditForm, CustomPasswordChangeForm  # Added form imports
from custom_requests.models import Document, Message
from services.email_notifications import EmailNotificationService

# Authentication views
def custom_login_view(request):
    """Custom login view that handles both form and API requests"""
    # Clear all messages on GET requests to prevent accumulation
    if request.method == 'GET':
        storage = messages.get_messages(request)
        storage.used = True
    
    if request.method == 'POST':
        # Check if this is an API call
        if request.content_type == 'application/json':
            try:
                import json
                data = json.loads(request.body)
                email = data.get('email', '')
                password = data.get('password', '')
                
                user = authenticate(request, email=email, password=password)
                
                if user is not None:
                    if not user.is_active:
                        return JsonResponse({
                            'success': False,
                            'message': _('Please verify your email before logging in.')
                        }, status=400)
                    
                    print(f"API login successful for user: {user.email}, account_type: {user.account_type}")
                    login(request, user)
                    redirect_url = request.GET.get('next', '/accounts/dashboard/')
                    print(f"API login redirecting to: {redirect_url}")
                    return JsonResponse({
                        'success': True,
                        'redirect': redirect_url,
                        'user': {
                            'id': user.id,
                            'email': user.email,
                            'name': user.name,
                            'first_name': user.first_name,
                            'account_type': user.account_type,
                        }
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'message': _('Invalid email or password')
                    }, status=400)
                    
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'message': str(e)
                }, status=400)
          # Handle form submission
        email = request.POST.get('email')
        password = request.POST.get('password')
        account_type = request.POST.get('account_type', 'client')  # Default to client
        
        if not email or not password:
            messages.error(request, _('Please provide both email and password'))
            return render(request, 'general/login_modern.html')
          # Try authentication
        user = authenticate(request, email=email, password=password)
        
        if user is not None:
            if not user.is_active:
                messages.warning(request, _('Please verify your email before logging in.'))
                return redirect('accounts:verification_denied')
            
            # Check if the user's account type matches the selected type
            if user.account_type.lower() != account_type.lower():
                if account_type.lower() == 'expert':
                    messages.error(request, _('This email is not registered as an expert account.'))
                else:
                    messages.error(request, _('This email is not registered as a client account.'))
                return render(request, 'general/login_modern.html')
            
            login(request, user)
            # Check for next URL in POST data first, then GET parameters
            next_url = request.POST.get('next') or request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('accounts:dashboard_redirect')
        else:
            messages.error(request, _('Invalid email or password'))
    
    return render(request, 'general/login_modern.html')

# Admin authentication views
def admin_login_view(request):
    """Custom login view specifically for admin users - with enhanced security"""
    
    # Track login attempts for security (to detect brute force attacks)
    client_ip = request.META.get('REMOTE_ADDR', '')
    current_time = timezone.now()
    
    # Simple rate limiting - you would implement this properly in production
    # with a proper rate limiting solution
    
    # Clear any existing messages
    storage = messages.get_messages(request)
    storage.used = True
    
    # If user is already authenticated as admin, redirect to admin dashboard
    if request.user.is_authenticated and request.user.account_type.lower() == 'admin':
        return redirect('admin_dashboard')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        security_code = request.POST.get('security_code')
        
        # Add additional security layer - a fixed security code
        # In production, use a proper 2FA solution instead
        if security_code != '87654321':
            messages.error(request, _("Code de sécurité invalide."))
            print(f"Failed admin login attempt with invalid security code from IP: {client_ip}")
            return redirect('accounts:admin_login_view')
            
        user = authenticate(request, email=email, password=password)
        
        if user is not None and user.account_type.lower() == 'admin':
            print(f"Admin login successful for: {user.email} from IP: {client_ip}")
            login(request, user)
            
            # Log successful admin login for security audit
            return redirect('admin_dashboard')
        else:
            # Either the credentials are wrong or the user is not an admin
            if user is not None and user.account_type.lower() != 'admin':
                messages.error(request, _("Vous n'avez pas les autorisations nécessaires pour accéder au panel administrateur."))
            else:
                messages.error(request, _("Email ou mot de passe incorrect."))
            
            # Log failed login attempt
            print(f"Failed admin login attempt for email: {email} from IP: {client_ip}")
            return redirect('accounts:admin_login_view')
    
    return render(request, 'admin/login.html')

def create_admin_user(request):
    """View to create a new admin user (protected, only accessible to existing admins)"""
    if not request.user.is_authenticated or request.user.account_type.lower() != 'admin':
        raise PermissionDenied
    
    if request.method == 'POST':
        email = request.POST.get('email')
        name = request.POST.get('name')
        first_name = request.POST.get('first_name')
        password = request.POST.get('password')
        
        if email and password:
            try:
                # Check if user already exists
                if Utilisateur.objects.filter(email=email).exists():
                    messages.error(request, _("Un utilisateur avec cet email existe déjà."))
                    return redirect('admin_users')
                  # Create the admin user
                user = Utilisateur.objects.create_user(
                    email=email,
                    name=name,
                    first_name=first_name,
                    password=password,
                    account_type='admin',
                    is_verified=True
                )
                
                # Send welcome email notification
                try:
                    EmailNotificationService.send_welcome_email(user, password)
                except Exception as email_error:
                    print(f"Failed to send welcome email: {email_error}")
                    # Continue without failing the request
                
                messages.success(request, _("Administrateur créé avec succès."))
                return redirect('admin_users')
            except Exception as e:
                messages.error(request, str(e))
                return redirect('admin_users')
    
    # GET request - show the form
    return render(request, 'admin/create_admin.html')

def register_view(request):
    """Handle client registration"""
    # Clear previous messages on GET requests
    if request.method == 'GET':
        storage = messages.get_messages(request)
        storage.used = True
        
    if request.method == 'POST':
        # Get account type from register form
        account_type = request.POST.get('register_account_type', 'client')
        
        # Extract user data from form - matching old registration form field names
        email = request.POST.get('email', '')
        password1 = request.POST.get('password', '')  # From old form
        password2 = request.POST.get('password_confirm', '')  # From old form
        last_name = request.POST.get('last_name', '')  # From old form
        first_name = request.POST.get('first_name', '')
        phone = request.POST.get('phone', '')  # From old form
        residence_country = request.POST.get('residence_country', '')
        last_visit = request.POST.get('last_visit', '')
        terms = request.POST.get('terms', '')
        
        print(f"EXTRACTED DATA: email={email}, password={'***' if password1 else 'EMPTY'}, last_name={last_name}, first_name={first_name}, phone={phone}, account_type={account_type}, residence_country={residence_country}")
        
        # Validate data
        if not all([email, password1, last_name, first_name, phone, residence_country]):
            print(f"VALIDATION FAILED: missing fields - email={bool(email)}, password={bool(password1)}, last_name={bool(last_name)}, first_name={bool(first_name)}, phone={bool(phone)}, residence_country={bool(residence_country)}")
            messages.error(request, _('Veuillez remplir tous les champs obligatoires'))
            return render(request, 'general/login_modern.html')
          
        # Check terms acceptance
        if not terms:
            messages.error(request, _('Vous devez accepter les conditions d\'utilisation'))
            return render(request, 'general/login_modern.html')
          
        # Check if passwords match
        if password1 != password2:
            print(f"PASSWORD MISMATCH: password length={len(password1)}, confirm length={len(password2)}")
            messages.error(request, _('Les mots de passe ne correspondent pas'))
            return render(request, 'general/login_modern.html')          
        
        # Check if user already exists
        if Utilisateur.objects.filter(email=email).exists():
            print(f"USER ALREADY EXISTS: {email}")
            messages.error(request, _('Cette adresse email est déjà enregistrée'))
            return render(request, 'general/login_modern.html')
            
        print("ALL VALIDATIONS PASSED - proceeding to user creation")
        
        try:
            # Create user with is_active=False
            user = Utilisateur.objects.create_user(
                email=email,
                password=password1,  # Use password1
                name=last_name,  # Use last_name as name
                first_name=first_name,
                phone=phone,
                account_type=account_type,
                preferred_languages=request.POST.get('preferred_language', 'fr'),
                is_active=False  # Set user as inactive until email verification
            )
            # Store email in session for email_sent page
            request.session['registered_email'] = email
            
            if account_type == 'expert':
                # Create expert profile
                Expert.objects.create(
                    user=user,
                    specialization=request.POST.get('specialization', ''),
                    years_of_experience=int(request.POST.get('years_of_experience', 0) or 0),
                    is_verified=False  # Expert needs verification by admin
                )
            else:
                # Create client profile
                Client.objects.create(
                    user=user,
                    mre_status=True,
                    origin_country='Maroc',
                    last_visit=last_visit if last_visit else None
                )
            
            # Create address if provided
            if residence_country:
                Address.objects.create(
                    user=user,
                    country=residence_country,
                    address_type='HOME',
                )            
            
            # Send verification email
            try:
                send_verification_email(user, request)
                success_message = _('Inscription réussie ! Un email de vérification a été envoyé à votre adresse email.')
                if account_type == 'expert':
                    success_message += _(' Votre compte expert sera vérifié par notre équipe.')
                messages.success(request, success_message)
                return redirect('accounts:email_sent')
            except Exception as e:
                # If email sending fails, delete the user and show error
                user.delete()
                messages.error(request, _('Erreur lors de l\'envoi de l\'email de vérification. Veuillez réessayer.'))
                print(f"Email sending error: {str(e)}")  # For debugging
                return render(request, 'general/login_modern.html')
        except Exception as e:
            messages.error(request, str(e))
            print(f"REGISTER ERROR: {str(e)}")
            return render(request, 'general/login_modern.html')
    
    # GET request - show registration form (redirect to login page with registration form)
    return render(request, 'general/login_modern.html')


def expert_registration_disabled_view(request):
    """Shows a message that expert registration is disabled and only available via admin"""
    from django.contrib import messages
    from django.shortcuts import render
    
    # Add message in French
    messages.error(request, "L'inscription des experts n'est plus disponible ici. Veuillez contacter l'administrateur pour créer un compte expert.")
    
    # Return to login page with the message
    context = {
        'title': 'Inscription Expert Désactivée',
        'message': "L'inscription des experts se fait uniquement via le panneau d'administration.",
        'admin_only': True
    }
    return render(request, 'general/login_modern.html', context)


def register_expert_view(request):
    """Redirect expert registration to admin panel"""
    # This is kept for backward compatibility but should redirect
    return expert_registration_disabled_view(request)


# Dashboard views
@login_required
def dashboard_redirect_view(request):
    """Redirect users to the appropriate dashboard based on their account type"""
    print(f"Dashboard redirect for user: {request.user.email}, account_type={request.user.account_type}")
    
    # Check account type case-insensitively
    account_type = request.user.account_type.lower()
    
    if account_type == 'admin':
        print("Redirecting to admin dashboard")
        return redirect('admin_dashboard')
    elif account_type == 'expert':
        print("Redirecting to expert dashboard")
        return redirect('expert_dashboard')
    elif account_type == 'client':
        print("Redirecting to client dashboard")
        return redirect('client_dashboard')
    else:
        print(f"Unknown account type: {account_type}, redirecting to home")
        return redirect('home')

# Profile views
@login_required
def profile_view(request):
    """View user's own profile"""
    # Get the user's profile information
    user = request.user
    
    # Get user's address
    try:
        address = Address.objects.get(user=user, address_type='HOME')
    except Address.DoesNotExist:
        address = None
    
    # Get additional profile info based on user type
    if user.account_type == 'CLIENT':
        try:
            profile = Client.objects.get(user=user)
        except Client.DoesNotExist:
            profile = None
        base_template = 'client/base.html'
    elif user.account_type == 'EXPERT':
        try:
            profile = Expert.objects.get(user=user)
        except Expert.DoesNotExist:
            profile = None
        base_template = 'expert/base.html'
    else:
        profile = None
        base_template = 'admin/base.html'
    
    context = {
        'user': user,
        'address': address,
        'profile': profile,
        'base_template': base_template,  # Pass the base template to the context
    }
    
    return render(request, 'accounts/profile.html', context)

@login_required
def edit_profile_view(request):
    user = request.user
    
    if request.method == 'POST':
        try:
            # Update basic user information
            user.name = request.POST.get('name', user.name)
            user.first_name = request.POST.get('first_name', user.first_name)
            user.email = request.POST.get('email', user.email)
            user.phone = request.POST.get('phone', user.phone)
            user.birth_date = request.POST.get('birth_date') or None
            user.residence_country = request.POST.get('residence_country', user.residence_country)
            user.preferred_languages = request.POST.get('preferred_languages', user.preferred_languages)
            
            # Handle profile picture upload
            if 'profile_picture' in request.FILES:
                user.profile_picture = request.FILES['profile_picture']
            
            # Handle password change if provided
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            
            if new_password:
                if new_password == confirm_password:
                    if len(new_password) >= 8:
                        user.set_password(new_password)
                        update_session_auth_hash(request, user)  # Keep user logged in
                        messages.success(request, _('Mot de passe mis à jour avec succès.'))
                    else:
                        messages.error(request, _('Le mot de passe doit contenir au moins 8 caractères.'))
                        # Redirect to appropriate dashboard
                        if user.account_type == 'expert':
                            return redirect('expert_dashboard')
                        elif user.account_type == 'admin':
                            return redirect('admin_dashboard')
                        else:
                            return redirect('client_dashboard')
                else:
                    messages.error(request, _('Les mots de passe ne correspondent pas.'))
                    # Redirect to appropriate dashboard
                    if user.account_type == 'expert':
                        return redirect('expert_dashboard')
                    elif user.account_type == 'admin':
                        return redirect('admin_dashboard')
                    else:
                        return redirect('client_dashboard')
            
            user.save()
            
            # Update client-specific information
            if user.account_type == 'client':
                try:
                    client_profile = user.client_profile
                    client_profile.mre_status = request.POST.get('mre_status') == 'on'
                    client_profile.origin_country = request.POST.get('origin_country', client_profile.origin_country)
                    
                    last_visit = request.POST.get('last_visit')
                    if last_visit:
                        from datetime import datetime
                        client_profile.last_visit = datetime.strptime(last_visit, '%Y-%m-%d').date()
                    
                    client_profile.save()
                except Exception as e:
                    messages.warning(request, _('Profil client non trouvé, création en cours...'))
                    Client.objects.create(
                        user=user,
                        mre_status=request.POST.get('mre_status') == 'on',
                        origin_country=request.POST.get('origin_country', 'Maroc'),
                        last_visit=request.POST.get('last_visit') or None
                    )
            
            # Update expert-specific information  
            elif user.account_type == 'expert':
                try:
                    expert_profile = user.expert_profile
                    expert_profile.specialty = request.POST.get('specialty', expert_profile.specialty)
                    expert_profile.competencies = request.POST.get('competencies', expert_profile.competencies)
                    expert_profile.spoken_languages = request.POST.get('spoken_languages', expert_profile.spoken_languages)
                    expert_profile.biography = request.POST.get('biography', expert_profile.biography)
                    expert_profile.availability = request.POST.get('availability', expert_profile.availability)
                    
                    if request.POST.get('years_of_experience'):
                        try:
                            expert_profile.years_of_experience = int(request.POST.get('years_of_experience'))
                        except ValueError:
                            pass
                    
                    if request.POST.get('hourly_rate'):
                        try:
                            expert_profile.hourly_rate = float(request.POST.get('hourly_rate'))
                        except ValueError:
                            pass
                    
                    expert_profile.save()
                except Exception as e:
                    messages.warning(request, _('Profil expert non trouvé, création en cours...'))
                    Expert.objects.create(
                        user=user,
                        specialty=request.POST.get('specialty', ''),
                        competencies=request.POST.get('competencies', ''),
                        spoken_languages=request.POST.get('spoken_languages', 'fr'),
                        biography=request.POST.get('biography', ''),
                        availability=request.POST.get('availability', ''),
                        years_of_experience=int(request.POST.get('years_of_experience', 0)),
                        hourly_rate=float(request.POST.get('hourly_rate', 0))
                    )
            
            messages.success(request, _('Votre profil a été mis à jour avec succès.'))
            
            # Redirect to appropriate dashboard
            if user.account_type == 'expert':
                return redirect('expert_dashboard')
            elif user.account_type == 'admin':
                return redirect('admin_dashboard')
            else:
                return redirect('client_dashboard')
            
        except Exception as e:
            messages.error(request, _('Une erreur est survenue lors de la mise à jour de votre profil.'))
            # Redirect to appropriate dashboard
            if user.account_type == 'expert':
                return redirect('expert_dashboard')
            elif user.account_type == 'admin':
                return redirect('admin_dashboard')
            else:
                return redirect('client_dashboard')
    
    # If it's a GET request, redirect to appropriate dashboard
    if user.account_type == 'expert':
        return redirect('expert_dashboard')
    elif user.account_type == 'admin':
        return redirect('admin_dashboard')
    else:
        return redirect('client_dashboard')

    profile_specific = None
    if user.account_type == 'CLIENT':
        try:
            profile_specific = Client.objects.get(user=user)
        except Client.DoesNotExist:
            pass
    elif user.account_type == 'EXPERT':
        try:
            profile_specific = Expert.objects.get(user=user)
        except Expert.DoesNotExist:
            pass

    context = {
        'user_form': user_form,
        'password_form': password_form,
        'user': user,
        'address': address,
        'profile_specific': profile_specific, # Changed from 'profile' to 'profile_specific'
        'countries': settings.COUNTRIES,
        'account_type': user.account_type # Pass account_type for template logic
    }
    return render(request, 'accounts/edit_profile.html', context)

# Client specific views
@login_required
def client_profile_view(request):
    """View for client profile"""
    # Check if user is a client
    if request.user.account_type != 'CLIENT':
        raise PermissionDenied
    
    return profile_view(request)

@login_required
def client_documents_view(request):
    """View client's documents"""
    # Check if user is a client
    if request.user.account_type != 'CLIENT':
        raise PermissionDenied
    
    # Get client's documents
    documents = Document.objects.filter(user=request.user).order_by('-uploaded_at')
    
    context = {
        'documents': documents,
    }
    
    return render(request, 'accounts/client_documents.html', context)

# Expert specific views
@login_required
def expert_profile_view(request):
    """View for expert profile"""
    # Check if user is an expert
    if request.user.account_type != 'EXPERT':
        raise PermissionDenied
    
    return profile_view(request)

@login_required
def expert_availability_view(request):
    """Manage expert's availability"""
    # Check if user is an expert
    if request.user.account_type != 'EXPERT':
        raise PermissionDenied
    
    expert = get_object_or_404(Expert, user=request.user)
    
    if request.method == 'POST':
        # Update availability status
        status = request.POST.get('availability_status')
        if status in ['AVAILABLE', 'BUSY', 'UNAVAILABLE']:
            expert.availability_status = status
            expert.save()
        
        return redirect('accounts:expert_profile')
    
    context = {
        'expert': expert,
    }
    
    return render(request, 'accounts/expert_availability.html', context)

@login_required
def expert_services_view(request):
    """Manage services offered by expert"""
    # Check if user is an expert
    if request.user.account_type != 'EXPERT':
        raise PermissionDenied
    
    expert = get_object_or_404(Expert, user=request.user)
    
    # Get services offered by expert
    services = expert.services.all()
    
    context = {
        'expert': expert,
        'services': services,
    }
    
    return render(request, 'accounts/expert_services.html', context)

# Admin specific views
@login_required
def admin_users_view(request):
    """Admin view for user management"""
    # Check if user is an admin
    if request.user.account_type != 'ADMIN':
        raise PermissionDenied
    
    # Get all users
    users = Utilisateur.objects.all().order_by('-date_joined')
    
    context = {
        'users': users,
    }
    
    return render(request, 'accounts/admin_users.html', context)

@login_required
def admin_user_detail_view(request, user_id):
    """Admin view for user details"""
    # Check if user is an admin
    if request.user.account_type != 'ADMIN':
        raise PermissionDenied
    
    # Get the user
    user = get_object_or_404(Utilisateur, id=user_id)
    
    # Get user's address
    try:
        address = Address.objects.get(user=user, address_type='HOME')
    except Address.DoesNotExist:
        address = None
    
    # Get additional profile info based on user type
    if user.account_type == 'CLIENT':
        try:
            profile = Client.objects.get(user=user)
        except Client.DoesNotExist:
            profile = None
    elif user.account_type == 'EXPERT':
        try:
            profile = Expert.objects.get(user=user)
        except Expert.DoesNotExist:
            profile = None
    else:
        profile = None
    
    context = {
        'target_user': user,  # Use 'target_user' to avoid conflict with 'user' (the admin)
        'address': address,
        'profile': profile,
    }
    
    return render(request, 'accounts/admin_user_detail.html', context)

@login_required
def admin_create_user_view(request):
    """Admin view to create a new user"""
    # Check if user is an admin
    if request.user.account_type != 'ADMIN':
        raise PermissionDenied
    
    if request.method == 'POST':
        # Extract user data
        email = request.POST.get('email', '')
        password = request.POST.get('password', '')
        name = request.POST.get('name', '')
        first_name = request.POST.get('first_name', '')
        phone = request.POST.get('phone', '')
        user_type = request.POST.get('user_type', 'CLIENT')
        
        # Create user
        user = Utilisateur.objects.create_user(
            email=email,
            password=password,
            name=name,
            first_name=first_name,
            phone=phone,
            account_type=user_type,
        )
        
        # Create profile based on user type
        if user_type == 'CLIENT':
            Client.objects.create(
                user=user,
                preferred_language=request.POST.get('preferred_language', 'fr'),
            )
        elif user_type == 'EXPERT':
            Expert.objects.create(
                user=user,
                specialty=request.POST.get('specialty', ''),
                biography=request.POST.get('bio', ''),
                spoken_languages=request.POST.get('languages', 'fr') or 'fr',
                hourly_rate=0  # Default value
            )
          # Create address if provided
        street = request.POST.get('street', '')
        if street:
            Address.objects.create(
                user=user,
                street=street,
                city=request.POST.get('city', ''),
                postal_code=request.POST.get('postal_code', ''),
                country=request.POST.get('country', ''),
                address_type='HOME',
            )
        
        # Send welcome email notification
        try:
            EmailNotificationService.send_welcome_email(user, password)
        except Exception as email_error:
            print(f"Failed to send welcome email: {email_error}")
            # Continue without failing the request
        
        return redirect('accounts:admin_users')
    
    context = {
        'countries': settings.COUNTRIES,
    }
    
    return render(request, 'accounts/admin_create_user.html', context)

# API endpoints
@csrf_exempt
@login_required
def api_profile(request):
    """API endpoint to get user profile"""
    user = request.user
    
    # Get user's address
    try:
        address = Address.objects.get(user=user, address_type='HOME')
        address_data = {
            'street': address.street,
            'city': address.city,
            'postal_code': address.postal_code,
            'country': address.country,
        }
    except Address.DoesNotExist:
        address_data = {}
    
    # Get additional profile info based on user type
    if user.account_type == 'CLIENT':
        try:
            profile = Client.objects.get(user=user)
            profile_data = {
                'preferred_language': profile.preferred_language,
            }
        except Client.DoesNotExist:
            profile_data = {}
    elif user.account_type == 'EXPERT':
        try:
            profile = Expert.objects.get(user=user)
            profile_data = {
                'title': profile.title,
                'specialty': profile.specialty,
                'bio': profile.bio,
                'experience_years': profile.experience_years,
                'languages': profile.languages,
                'availability_status': profile.availability_status,
            }
        except Expert.DoesNotExist:
            profile_data = {}
    else:
        profile_data = {}
    
    # Prepare response data
    user_data = {
        'id': user.id,
        'email': user.email,
        'name': user.name,
        'first_name': user.first_name,
        'phone': user.phone,
        'account_type': user.account_type,
        'date_joined': user.date_joined.isoformat(),
        'is_active': user.is_active,
        'address': address_data,
        'profile': profile_data,
    }
    
    return JsonResponse({
        'success': True,
        'user': user_data
    })

@csrf_exempt
@login_required
def api_update_profile(request):
    """API endpoint to update user profile"""
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'message': _('Method not allowed')
        }, status=405)
    
    try:
        user = request.user
        
        # Update basic user data from form data
        if request.POST.get('name'):
            user.name = request.POST.get('name')
        if request.POST.get('first_name'):
            user.first_name = request.POST.get('first_name')
        if request.POST.get('email'):
            user.email = request.POST.get('email')
        if request.POST.get('phone'):
            user.phone = request.POST.get('phone')
        if request.POST.get('residence_country'):
            user.residence_country = request.POST.get('residence_country')
        if request.POST.get('birth_date'):
            try:
                from datetime import datetime
                birth_date = datetime.strptime(request.POST.get('birth_date'), '%Y-%m-%d').date()
                user.birth_date = birth_date
            except ValueError:
                pass  # Invalid date format, skip
        
        # Handle profile picture upload with validation
        if 'profile_picture' in request.FILES:
            profile_picture = request.FILES['profile_picture']
            
            # Validate file size (max 5MB)
            if profile_picture.size > 5 * 1024 * 1024:
                return JsonResponse({
                    'success': False,
                    'message': _('Profile picture must be less than 5MB')
                }, status=400)
            
            # Validate file type
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif']
            if profile_picture.content_type not in allowed_types:
                return JsonResponse({
                    'success': False,
                    'message': _('Profile picture must be a JPEG, PNG, or GIF image')
                }, status=400)
            
            user.profile_picture = profile_picture
        
        # Handle password change if provided
        if request.POST.get('current_password') and request.POST.get('new_password'):
            if user.check_password(request.POST.get('current_password')):
                user.set_password(request.POST.get('new_password'))
            else:
                return JsonResponse({
                    'success': False,
                    'message': _('Current password is incorrect')
                }, status=400)
        
        user.save()
        
        # Update additional profile info based on user type
        if user.account_type == 'CLIENT' or user.account_type == 'client':
            client_defaults = {}
            if request.POST.get('origin_country'):
                client_defaults['origin_country'] = request.POST.get('origin_country')
            if request.POST.get('mre_status') is not None:
                client_defaults['mre_status'] = request.POST.get('mre_status') == 'on'
            if request.POST.get('last_visit'):
                try:
                    from datetime import datetime
                    last_visit = datetime.strptime(request.POST.get('last_visit'), '%Y-%m-%d').date()
                    client_defaults['last_visit'] = last_visit
                except ValueError:
                    pass  # Invalid date format, skip
            
            if client_defaults:
                Client.objects.update_or_create(
                    user=user,
                    defaults=client_defaults
                )
        
        elif user.account_type == 'EXPERT' or user.account_type == 'expert':
            expert_defaults = {}
            if request.POST.get('specialty'):
                expert_defaults['specialty'] = request.POST.get('specialty')
            if request.POST.get('biography'):
                expert_defaults['biography'] = request.POST.get('biography')
            if request.POST.get('competencies'):
                expert_defaults['competencies'] = request.POST.get('competencies')
            if request.POST.get('years_of_experience'):
                try:
                    expert_defaults['years_of_experience'] = int(request.POST.get('years_of_experience'))
                except ValueError:
                    pass
            if request.POST.get('spoken_languages'):
                expert_defaults['spoken_languages'] = request.POST.get('spoken_languages')
            if request.POST.get('hourly_rate'):
                try:
                    expert_defaults['hourly_rate'] = float(request.POST.get('hourly_rate'))
                except ValueError:
                    pass
            if request.POST.get('availability'):
                expert_defaults['availability'] = request.POST.get('availability')
            
            if expert_defaults:
                Expert.objects.update_or_create(
                    user=user,
                    defaults=expert_defaults
                )
        
        # Get the updated profile picture URL if it was uploaded
        profile_picture_url = None
        if user.profile_picture:
            profile_picture_url = user.profile_picture.url
        
        return JsonResponse({
            'success': True,
            'message': _('Profile updated successfully'),
            'profile_picture_url': profile_picture_url
        })
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Profile update error: {error_details}")  # For debugging
        
        return JsonResponse({
            'success': False,
            'message': _('Error updating profile: ') + str(e)
        }, status=500)

def send_verification_email(user, request):
    """Send verification email to user"""
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    verification_url = request.build_absolute_uri(
        reverse('accounts:verify_email', kwargs={'uidb64': uid, 'token': token})
    )
    
    try:
        # Use the new email notification service
        EmailNotificationService.send_verification_email(user, verification_url)
        print(f"Verification email sent to {user.email}")  # For debugging
    except Exception as e:
        print(f"Error sending verification email: {str(e)}")  # For debugging
        raise  # Re-raise the exception to handle it in the calling function

def email_sent(request):
    """Show email sent confirmation page"""
    # Get the user's email from the session
    user_email = request.session.get('registered_email')
    context = {
        'user_email': user_email
    }
    return render(request, 'accounts/email_sent.html', context)

def verify_email(request, uidb64, token):
    """Handle email verification"""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = Utilisateur.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Utilisateur.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        return render(request, 'accounts/verification_success.html')
    else:
        messages.error(request, _('Le lien de vérification est invalide ou a expiré.'))
        return redirect('accounts:verification_denied')

def verification_denied(request):
    """Show verification denied page"""
    return render(request, 'accounts/verification_denied.html')

def resend_verification(request):
    """Handle resending verification email"""
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = Utilisateur.objects.get(email=email)
            if not user.is_active:
                send_verification_email(user, request)
                messages.success(request, _('Un email de vérification a été renvoyé. Veuillez vérifier votre boîte de réception.'))
                return redirect('accounts:email_sent')
            else:
                messages.info(request, _('Votre compte est déjà vérifié. Vous pouvez vous connecter maintenant.'))
                return redirect('accounts:login')
        except Utilisateur.DoesNotExist:
            messages.error(request, _('Aucun compte trouvé avec cette adresse email.'))
    return redirect('accounts:verification_denied')

def password_reset_request(request):
    """Handle password reset request"""
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = Utilisateur.objects.get(email=email, is_active=True)
            # Generate token and UID
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            reset_url = request.build_absolute_uri(
                reverse('accounts:password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
            )
            
            # Send email
            context = {
                'reset_url': reset_url,
                'user': user
            }
            html_message = render_to_string('accounts/email/password_reset_email.html', context)
            plain_message = f"""
            Bonjour,
            
            Vous avez demandé la réinitialisation de votre mot de passe. Cliquez sur le lien ci-dessous pour créer un nouveau mot de passe :
            
            {reset_url}
            
            Ce lien expirera dans 24 heures.
            
            Si vous n'avez pas demandé cette réinitialisation, veuillez ignorer cet email.
            
            Cordialement,
            L'équipe Adval Services
            """
            
            send_mail(
                'Réinitialisation de votre mot de passe - Adval Services',
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                html_message=html_message,
                fail_silently=False,
            )
            
            return redirect('accounts:password_reset_done')
        except Utilisateur.DoesNotExist:
            # Don't reveal that the user doesn't exist
            return redirect('accounts:password_reset_done')
    
    return render(request, 'accounts/password_reset_request.html')

def password_reset_done(request):
    """Show password reset email sent confirmation"""
    return render(request, 'accounts/password_reset_done.html')

def password_reset_confirm(request, uidb64, token):
    """Handle password reset confirmation"""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = Utilisateur.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Utilisateur.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            new_password1 = request.POST.get('new_password1')
            new_password2 = request.POST.get('new_password2')
            
            if new_password1 != new_password2:
                messages.error(request, 'Les mots de passe ne correspondent pas.')
                return render(request, 'accounts/password_reset_confirm.html')
            
            if len(new_password1) < 8:
                messages.error(request, 'Le mot de passe doit contenir au moins 8 caractères.')
                return render(request, 'accounts/password_reset_confirm.html')
            
            user.set_password(new_password1)
            user.save()
            messages.success(request, 'Votre mot de passe a été réinitialisé avec succès. Vous pouvez maintenant vous connecter.')
            return redirect('accounts:login')
        
        return render(request, 'accounts/password_reset_confirm.html', {'validlink': True})
    
    return render(request, 'accounts/password_reset_confirm.html', {'validlink': False})

def password_reset_complete(request):
    """Show password reset complete confirmation"""
    return render(request, 'accounts/password_reset_complete.html')

@login_required
def admin_edit_profile_view(request):
    """View for admin profile editing"""
    # Check if user is an admin
    if request.user.account_type != 'ADMIN':
        raise PermissionDenied
    
    user = request.user
    user_form = UserEditForm(instance=user)
    
    if request.method == 'POST':        
        user_form = UserEditForm(request.POST, request.FILES, instance=user)
        
        if user_form.is_valid():
            # Save the user form
            user = user_form.save()
            
            # Handle password change if provided
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            
            if new_password and confirm_password:
                if new_password == confirm_password:
                    if len(new_password) >= 8:
                        user.set_password(new_password)
                        user.save()
                        messages.success(request, _('Votre profil et mot de passe ont été mis à jour avec succès.'))
                        
                        # Update session to prevent logout
                        from django.contrib.auth import update_session_auth_hash
                        update_session_auth_hash(request, user)
                    else:
                        messages.error(request, _('Le mot de passe doit contenir au moins 8 caractères.'))
                        return render(request, 'admin/edit_profile.html', {'user_form': user_form, 'user': user})
                else:
                    messages.error(request, _('Les mots de passe ne correspondent pas.'))
                    return render(request, 'admin/edit_profile.html', {'user_form': user_form, 'user': user})
            else:
                messages.success(request, _('Votre profil a été mis à jour avec succès.'))
            
            # Force session update
            request.session.modified = True
            
            # Redirect to profile page with cache-busting
            import time
            import random
            cache_buster = f"{int(time.time())}_{random.randint(1000, 9999)}"
            return redirect(f"{reverse('admin_profile')}?v={cache_buster}")
        else:
            # Show specific form errors
            for field, errors in user_form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    
    context = {
        'user_form': user_form,
        'user': user,
    }
    return render(request, 'admin/edit_profile.html', context)

@require_http_methods(["GET", "POST"])
def custom_logout_view(request):
    logout(request)
    return redirect('accounts:login')

def register_test_view(request):
    """Test registration view"""
    return render(request, 'general/register_test.html')
