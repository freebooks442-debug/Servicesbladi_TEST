from django.core.management.base import BaseCommand
from services.models import Service

class Command(BaseCommand):
    help = 'Update service titles to French'
    
    def handle(self, *args, **options):
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
        
        self.stdout.write("=== Updating Services to French ===")
        
        services = Service.objects.all()
        self.stdout.write(f"Found {services.count()} services")
        
        updated_count = 0
        for service in services:
            old_title = service.title
            if old_title in service_translations:
                new_title = service_translations[old_title]
                service.title = new_title
                service.save()
                self.stdout.write(f"Updated: {old_title} → {new_title}")
                updated_count += 1
            else:
                self.stdout.write(f"No translation found for: {old_title}")
        
        self.stdout.write(f"\n✅ Updated {updated_count} services to French!")
        
        # Show final results
        self.stdout.write("\n=== Final Service List ===")
        services = Service.objects.all().order_by('id')
        for service in services:
            self.stdout.write(f"ID: {service.id}, Title: {service.title}")
