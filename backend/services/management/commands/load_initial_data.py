from django.core.management.base import BaseCommand
from services.models import Service, ServiceCategory, ServiceType, AdministrativeService
from django.db import transaction
from datetime import timedelta


class Command(BaseCommand):
    help = 'Load initial services data into the database'

    def handle(self, *args, **options):
        self.stdout.write("Loading initial services data...")
        
        try:
            with transaction.atomic():
                # Create service categories first
                categories_data = [
                    {
                        'name': 'Administrative',
                        'name_fr': 'Administratif',
                        'name_ar': 'إداري',
                        'description': 'Administrative services',
                        'description_fr': 'Services administratifs',
                        'description_ar': 'الخدمات الإدارية',
                        'slug': 'administrative',
                        'icon': 'fas fa-file-alt'
                    },
                    {
                        'name': 'Legal',
                        'name_fr': 'Juridique',
                        'name_ar': 'قانوني',
                        'description': 'Legal services',
                        'description_fr': 'Services juridiques',
                        'description_ar': 'الخدمات القانونية',
                        'slug': 'legal',
                        'icon': 'fas fa-gavel'
                    },
                    {
                        'name': 'Business',
                        'name_fr': 'Entreprise',
                        'name_ar': 'أعمال',
                        'description': 'Business services',
                        'description_fr': 'Services d\'entreprise',
                        'description_ar': 'الخدمات التجارية',
                        'slug': 'business',
                        'icon': 'fas fa-briefcase'
                    },
                    {
                        'name': 'Education',
                        'name_fr': 'Éducation',
                        'name_ar': 'تعليم',
                        'description': 'Educational services',
                        'description_fr': 'Services éducatifs',
                        'description_ar': 'الخدمات التعليمية',
                        'slug': 'education',
                        'icon': 'fas fa-graduation-cap'
                    },
                    {
                        'name': 'Immigration',
                        'name_fr': 'Immigration',
                        'name_ar': 'هجرة',
                        'description': 'Immigration services',
                        'description_fr': 'Services d\'immigration',
                        'description_ar': 'خدمات الهجرة',
                        'slug': 'immigration',
                        'icon': 'fas fa-globe'
                    }
                ]
                
                # Create categories
                for cat_data in categories_data:
                    category, created = ServiceCategory.objects.get_or_create(
                        slug=cat_data['slug'],
                        defaults=cat_data
                    )
                    if created:
                        self.stdout.write(f'Created category: {category.name}')
                
                # Create service types
                service_types_data = [
                    {
                        'category_slug': 'administrative',
                        'name': 'Passport Services',
                        'name_fr': 'Services de Passeport',
                        'name_ar': 'خدمات جواز السفر',
                        'description': 'Passport-related services',
                        'description_fr': 'Services liés au passeport',
                        'description_ar': 'الخدمات المتعلقة بجواز السفر',
                        'price': 200.00
                    },
                    {
                        'category_slug': 'administrative',
                        'name': 'ID Card Services',
                        'name_fr': 'Services de Carte d\'Identité',
                        'name_ar': 'خدمات بطاقة الهوية',
                        'description': 'National ID card services',
                        'description_fr': 'Services de carte d\'identité nationale',
                        'description_ar': 'خدمات بطاقة الهوية الوطنية',
                        'price': 50.00
                    },
                    {
                        'category_slug': 'administrative',
                        'name': 'Civil Records',
                        'name_fr': 'État Civil',
                        'name_ar': 'السجلات المدنية',
                        'description': 'Civil records services',
                        'description_fr': 'Services d\'état civil',
                        'description_ar': 'خدمات السجلات المدنية',
                        'price': 15.00
                    },
                    {
                        'category_slug': 'legal',
                        'name': 'Legal Consultation',
                        'name_fr': 'Consultation Juridique',
                        'name_ar': 'استشارة قانونية',
                        'description': 'General legal consultation',
                        'description_fr': 'Consultation juridique générale',
                        'description_ar': 'استشارة قانونية عامة',
                        'price': 100.00
                    },
                    {
                        'category_slug': 'business',
                        'name': 'Business Registration',
                        'name_fr': 'Immatriculation d\'Entreprise',
                        'name_ar': 'تسجيل الأعمال',
                        'description': 'Business registration services',
                        'description_fr': 'Services d\'immatriculation d\'entreprise',
                        'description_ar': 'خدمات تسجيل الأعمال',
                        'price': 300.00
                    }
                ]
                
                for st_data in service_types_data:
                    category = ServiceCategory.objects.get(slug=st_data['category_slug'])
                    st_data_clean = st_data.copy()
                    del st_data_clean['category_slug']
                    st_data_clean['category'] = category
                    
                    service_type, created = ServiceType.objects.get_or_create(
                        category=category,
                        name=st_data['name'],
                        defaults=st_data_clean
                    )
                    if created:
                        self.stdout.write(f'Created service type: {service_type.name}')
                
                # Create administrative services
                admin_category = ServiceCategory.objects.get(slug='administrative')
                passport_type = ServiceType.objects.get(category=admin_category, name='Passport Services')
                id_type = ServiceType.objects.get(category=admin_category, name='ID Card Services')
                civil_type = ServiceType.objects.get(category=admin_category, name='Civil Records')
                
                admin_services = [
                    {
                        'service_type': passport_type,
                        'title': 'Demande de passeport',
                        'description': 'Service pour demander un nouveau passeport ou renouveler un passeport existant',
                        'price': 200.00,
                        'duration': timedelta(days=15),
                        'is_active': True,
                        'document_type': 'Passeport',
                        'processing_time': timedelta(days=15),
                        'requirements': 'Carte d\'identité nationale, Photos d\'identité, Justificatif de domicile'
                    },
                    {
                        'service_type': id_type,
                        'title': 'Demande de carte d\'identité nationale',
                        'description': 'Service pour obtenir une nouvelle carte d\'identité nationale',
                        'price': 50.00,
                        'duration': timedelta(days=10),
                        'is_active': True,
                        'document_type': 'Carte d\'identité',
                        'processing_time': timedelta(days=10),
                        'requirements': 'Acte de naissance, Photos d\'identité, Justificatif de domicile'
                    },
                    {
                        'service_type': civil_type,
                        'title': 'Demande d\'acte de naissance',
                        'description': 'Service pour obtenir une copie d\'acte de naissance',
                        'price': 10.00,
                        'duration': timedelta(days=3),
                        'is_active': True,
                        'document_type': 'Acte de naissance',
                        'processing_time': timedelta(days=3),
                        'requirements': 'Pièce d\'identité du demandeur ou des parents'
                    },
                    {
                        'service_type': civil_type,
                        'title': 'Demande d\'acte de mariage',
                        'description': 'Service pour obtenir une copie d\'acte de mariage',
                        'price': 15.00,
                        'duration': timedelta(days=3),
                        'is_active': True,
                        'document_type': 'Acte de mariage',
                        'processing_time': timedelta(days=3),
                        'requirements': 'Pièces d\'identité des époux'
                    },
                    {
                        'service_type': civil_type,
                        'title': 'Demande de casier judiciaire',
                        'description': 'Service pour obtenir un extrait de casier judiciaire',
                        'price': 20.00,
                        'duration': timedelta(days=5),
                        'is_active': True,
                        'document_type': 'Casier judiciaire',
                        'processing_time': timedelta(days=5),
                        'requirements': 'Carte d\'identité, Formulaire de demande'
                    }
                ]
                
                # Create administrative services
                created_services = 0
                for service_data in admin_services:
                    service, created = AdministrativeService.objects.get_or_create(
                        title=service_data['title'],
                        defaults=service_data
                    )
                    if created:
                        created_services += 1
                        self.stdout.write(f'Created service: {service.title}')
                
                # Create some basic services using the base Service model for other categories
                legal_category = ServiceCategory.objects.get(slug='legal')
                legal_type = ServiceType.objects.get(category=legal_category, name='Legal Consultation')
                
                business_category = ServiceCategory.objects.get(slug='business')
                business_type = ServiceType.objects.get(category=business_category, name='Business Registration')
                
                basic_services = [
                    {
                        'service_type': legal_type,
                        'title': 'Consultation juridique générale',
                        'description': 'Consultation avec un avocat pour conseil juridique général',
                        'price': 100.00,
                        'duration': timedelta(days=1),
                        'is_active': True,
                    },
                    {
                        'service_type': business_type,
                        'title': 'Création d\'entreprise',
                        'description': 'Assistance complète pour la création d\'une nouvelle entreprise',
                        'price': 800.00,
                        'duration': timedelta(days=30),
                        'is_active': True,
                    }
                ]
                
                for service_data in basic_services:
                    service, created = Service.objects.get_or_create(
                        title=service_data['title'],
                        defaults=service_data
                    )
                    if created:
                        created_services += 1
                        self.stdout.write(f'Created service: {service.title}')
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully loaded {created_services} services into the database'
                    )
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error loading services: {str(e)}')
            )
            raise
