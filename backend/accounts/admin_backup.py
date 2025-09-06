from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.shortcuts import redirect
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import Utilisateur, Client, Expert, Admin

class UtilisateurAdmin(UserAdmin):
    """Admin configuration for Utilisateur model"""
    list_display = ('email', 'name', 'first_name', 'account_type', 'is_verified', 'is_active')
    list_filter = ('account_type', 'is_verified', 'is_active', 'is_staff', 'is_superuser')
    search_fields = ('email', 'name', 'first_name')
    ordering = ('email',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('name', 'first_name', 'phone', 'birth_date')}),
        (_('Location'), {'fields': ('residence_country',)}),
        (_('Preferences'), {'fields': ('preferred_languages',)}),
        (_('Account'), {'fields': ('account_type', 'is_verified', 'registration_date')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'name', 'first_name', 'account_type'),
        }),
    )

class ClientAdmin(admin.ModelAdmin):
    """Admin configuration for Client model"""
    list_display = ('get_name', 'get_email', 'mre_status', 'origin_country')
    list_filter = ('mre_status', 'origin_country')
    search_fields = ('user__name', 'user__first_name', 'user__email')
    
    def get_name(self, obj):
        return f"{obj.user.name} {obj.user.first_name}"
    get_name.short_description = _('Name')
    
    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = _('Email')

class ExpertAdmin(admin.ModelAdmin):
    """Admin configuration for Expert model"""
    list_display = ('get_name', 'get_email', 'specialty', 'hourly_rate')
    list_filter = ('specialty',)
    search_fields = ('user__name', 'user__first_name', 'user__email', 'specialty')
    
    # Fields to display in the form
    fields = ('user', 'specialty', 'competencies', 'spoken_languages', 'biography', 'hourly_rate', 'years_of_experience', 'availability')
    
    # Raw ID fields for better UX when selecting user
    raw_id_fields = ('user',)
    
    # Disable any default redirects
    save_as = False
    save_as_continue = False
    save_on_top = True
    
    # Override form processing to prevent redirects
    def get_form(self, request, obj=None, **kwargs):
        """Override form to prevent any redirect actions"""
        form = super().get_form(request, obj, **kwargs)
        # Remove any action attributes that might cause redirects
        return form
    
    def get_form_kwargs(self, request, obj, **kwargs):
        """Override form kwargs to prevent redirects"""
        return super().get_form_kwargs(request, obj, **kwargs)
    
    def form_valid(self, form):
        """Override form validation to control redirect"""
        response = super().form_valid(form)
        return HttpResponseRedirect(reverse('admin:accounts_expert_changelist'))
        
    def get_success_url(self):
        """Ensure success URL always goes to changelist"""
        return reverse('admin:accounts_expert_changelist')
        
    # Override all possible redirect methods
    def response_add(self, request, obj, post_url_continue=None):
        """Override response after adding to stay on the same page with French message"""
        messages.success(request, f"Expert '{obj.user.name} {obj.user.first_name}' a été créé avec succès.")
        # Always force staying on expert list page, ignore any continue parameters
        return HttpResponseRedirect(reverse('admin:accounts_expert_changelist'))
    
    def response_change(self, request, obj):
        """Override response after changing to stay on the same page with French message"""
        messages.success(request, f"Expert '{obj.user.name} {obj.user.first_name}' a été modifié avec succès.")
        # Always force staying on expert list page
        return HttpResponseRedirect(reverse('admin:accounts_expert_changelist'))
        
    def response_post_save_add(self, request, obj):
        """Override to prevent any unwanted redirects after save"""
        return self.response_add(request, obj)
        
    def response_post_save_change(self, request, obj):
        """Override to prevent any unwanted redirects after save"""  
        return self.response_change(request, obj)
        
    def response_delete(self, request, obj_display, obj_id):
        """Override delete response to stay on changelist"""
        messages.success(request, f"Expert '{obj_display}' a été supprimé avec succès.")
        return HttpResponseRedirect(reverse('admin:accounts_expert_changelist'))

class AdminModelAdmin(admin.ModelAdmin):
    """Admin configuration for Admin model"""
    list_display = ('get_name', 'get_email', 'level', 'last_login')
    list_filter = ('level',)
    search_fields = ('user__name', 'user__first_name', 'user__email')
    
    def get_name(self, obj):
        return f"{obj.user.name} {obj.user.first_name}"
    get_name.short_description = _('Name')
    
    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = _('Email')

# Register models with their admin configurations
admin.site.register(Utilisateur, UtilisateurAdmin)
admin.site.register(Client, ClientAdmin)
admin.site.register(Expert, ExpertAdmin)
admin.site.register(Admin, AdminModelAdmin)
