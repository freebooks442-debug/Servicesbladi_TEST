"""
URL configuration for servicesbladi project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect, render
from django.http import JsonResponse



# Direct imports removed - handled through app URLs

# Add a redirect for the secure admin login
def admin_login_redirect(request):
    return redirect('accounts:admin_login_view')

# Simple status check
def status_check(request):
    return JsonResponse({"status": "ok", "message": "Django server is working"})

# Media test page
def media_test_page(request):
    return render(request, 'media_test.html')

# Custom error handlers
def custom_404_view(request, exception):
    return render(request, '404.html', status=404)

def custom_500_view(request):
    return render(request, '500.html', status=500)

urlpatterns = [
    path('django-admin/', admin.site.urls),  # Renamed Django admin URL to avoid conflicts
      # Admin URL explicit redirect
    path('admin/', admin_login_redirect),
    
    path('status/', status_check, name='status_check'),
    path('media-test/', media_test_page, name='media_test'),

    # Include URLs from each app
    path('accounts/', include('accounts.urls')),
    path('services/', include('services.urls')),    path('requests/', include('custom_requests.urls')),
    path('resources/', include('resources.urls')),
    path('messaging/', include('messaging.urls')),
    path('chatbot/', include('chatbot.urls')),
    path('notifications/', include('notifications.urls')),
    
    # Frontend URLs (existing HTML templates integration)
    path('', include('servicesbladi.frontend_urls')),
    
    # Language change
    path('i18n/', include('django.conf.urls.i18n')),
]

# Add static and media URLs for development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Customize admin site titles
admin.site.site_header = _('ServicesBLADI Administration')
admin.site.site_title = _('ServicesBLADI Admin Portal')
admin.site.index_title = _('Welcome to ServicesBLADI Admin Portal')

# Custom error handlers
handler404 = 'servicesbladi.urls.custom_404_view'
handler500 = 'servicesbladi.urls.custom_500_view'
