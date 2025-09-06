from django.db import migrations

def update_services_to_french(apps, schema_editor):
    Service = apps.get_model('services', 'Service')
    
    # French translations for services
    service_translations = {
        'Document Request Service': 'Service de Demande de Documents',
        'Passport Services': 'Services de Passeport',
        'ID Card Services': 'Services de Carte d\'Identité',
        'Hotel Booking Service': 'Service de Réservation d\'Hôtel',
        'Tour Package Service': 'Service de Forfait Touristique',
        'Car Rental Service': 'Service de Location de Voiture',
        'Property Search Service': 'Service de Recherche Immobilière',
        'Property Management Service': 'Service de Gestion Immobilière',
        'Tax Declaration Service': 'Service de Déclaration Fiscale',
        'Tax Consultation Service': 'Service de Consultation Fiscale',
        'Investment Advice Service': 'Service de Conseil en Investissement',
        'Portfolio Management Service': 'Service de Gestion de Portefeuille',
    }
    
    for old_title, new_title in service_translations.items():
        Service.objects.filter(title=old_title).update(title=new_title)

def reverse_update_services(apps, schema_editor):
    # Reverse operation - update back to English
    Service = apps.get_model('services', 'Service')
    
    service_translations = {
        'Service de Demande de Documents': 'Document Request Service',
        'Services de Passeport': 'Passport Services',
        'Services de Carte d\'Identité': 'ID Card Services',
        'Service de Réservation d\'Hôtel': 'Hotel Booking Service',
        'Service de Forfait Touristique': 'Tour Package Service',
        'Service de Location de Voiture': 'Car Rental Service',
        'Service de Recherche Immobilière': 'Property Search Service',
        'Service de Gestion Immobilière': 'Property Management Service',
        'Service de Déclaration Fiscale': 'Tax Declaration Service',
        'Service de Consultation Fiscale': 'Tax Consultation Service',
        'Service de Conseil en Investissement': 'Investment Advice Service',
        'Service de Gestion de Portefeuille': 'Portfolio Management Service',
    }
    
    for french_title, english_title in service_translations.items():
        Service.objects.filter(title=french_title).update(title=english_title)

class Migration(migrations.Migration):
    
    dependencies = [
        ('services', '0001_initial'),  # Replace with your latest migration
    ]
    
    operations = [
        migrations.RunPython(update_services_to_french, reverse_update_services),
    ]
