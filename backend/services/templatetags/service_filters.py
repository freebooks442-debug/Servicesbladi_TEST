from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def translate_service_name(service_title):
    """
    Translate service names to proper French equivalents.
    This filter handles the translation from English/mixed service names to consistent French names.
    """
    # Define the translation mapping
    service_translations = {
        # English to French translations
        'Test Service': None,  # Remove this service
        'Administrative Basic Service': 'Administratif',
        'Services Administratifs': 'Administratif',
        'Tourism Basic Service': 'Tourisme',
        'Real Estate Basic Service': 'Immobilier', 
        'Investment Basic Service': 'Investissement',
        'Fiscal Basic Service': 'Fiscal',
        
        # Handle variations that might exist
        'Administrative Service': 'Administratif',
        'Tourism Service': 'Tourisme',
        'Real Estate Service': 'Immobilier',
        'Investment Service': 'Investissement',
        'Fiscal Service': 'Fiscal',
        
        # Already correct French names (no change needed)
        'Administratif': 'Administratif',
        'Tourisme': 'Tourisme',
        'Immobilier': 'Immobilier',
        'Investissement': 'Investissement',
        'Fiscal': 'Fiscal',
    }
    
    # Check if we have a translation for this service
    if service_title in service_translations:
        translated = service_translations[service_title]
        if translated is None:
            # This service should be hidden (like Test Service)
            return ''
        return translated
    
    # If no translation found, return the original title
    # but try to clean it up by removing common English words
    cleaned_title = service_title
    
    # Remove "Basic" and "Service" from the end
    if cleaned_title.endswith(' Basic Service'):
        cleaned_title = cleaned_title.replace(' Basic Service', '')
    elif cleaned_title.endswith(' Service'):
        cleaned_title = cleaned_title.replace(' Service', '')
    elif cleaned_title.endswith(' Basic'):
        cleaned_title = cleaned_title.replace(' Basic', '')
    
    # Handle specific translations for common words
    word_translations = {
        'Administrative': 'Administratif',
        'Tourism': 'Tourisme',
        'Real Estate': 'Immobilier',
        'Investment': 'Investissement',
        'Fiscal': 'Fiscal'
    }
    
    for english_word, french_word in word_translations.items():
        if cleaned_title == english_word:
            return french_word
    
    return cleaned_title


@register.filter
def should_display_service(service_title):
    """
    Check if a service should be displayed (filters out Test Service and other unwanted services)
    """
    hidden_services = ['Test Service', '']
    return service_title not in hidden_services


@register.simple_tag
def get_service_display_name(service):
    """
    Get the proper French display name for a service object
    """
    if hasattr(service, 'title'):
        translated_name = translate_service_name(service.title)
        return translated_name if should_display_service(translated_name) else None
    return None
