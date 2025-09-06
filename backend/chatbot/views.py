# filepath: c:\\Users\\Airzo\\Desktop\\sb-style_whit Notification Mail\\sb_style responsive\\sb_style responsive\\backend\\chatbot\\views.py
# filepath: c:\\Users\\Airzo\\Desktop\\sb-style_whit Notification Mail\\sb_style responsive\\sb_style responsive\\backend\\chatbot\\views_fixed.py
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count, Avg, Sum, F # Added F
from django.utils import timezone
from django.core.paginator import Paginator
from django.conf import settings
from django.utils.translation import gettext_lazy as _ # Added _
from django.db import transaction
import json
import uuid
import time
import requests
import re
from datetime import datetime, timedelta

from .models import ChatSession, ChatMessage, ChatFeedback, ChatAnalytics, ChatbotConfiguration


class ChatbotView(View):
    """Vue principale pour l'interface du chatbot"""
    
    def get(self, request):
        """Afficher l'interface chatbot"""
        context = {
            'user_is_client': request.user.is_authenticated,
            'show_chatbot': True,
        }
        return render(request, 'chatbot/chatbot.html', context)


@method_decorator(csrf_exempt, name='dispatch')
class ChatAPIView(View):
    """API pour les interactions du chatbot"""
    
    def post(self, request):
        """Traiter un message utilisateur"""
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '').strip()
            session_id = data.get('session_id')
            
            if not user_message:
                return JsonResponse({'error': 'Message requis'}, status=400)
            
            # Créer ou récupérer la session
            session = self.get_or_create_session(request, session_id)
            
            # Enregistrer le message utilisateur
            user_msg = ChatMessage.objects.create(
                session=session,
                message_type='user',
                content=user_message,
                domain_category=self.classify_domain(user_message)
            )
            
            # Générer la réponse du bot
            start_time = time.time()
            bot_response = self.generate_bot_response(user_message, session)
            response_time = int((time.time() - start_time) * 1000)
            
            # Enregistrer la réponse du bot
            bot_msg = ChatMessage.objects.create(
                session=session,
                message_type='bot',
                content=bot_response,
                response_time_ms=response_time,
                domain_category=user_msg.domain_category,
                api_model_used='gpt-4o'
            )
            
            # Mettre à jour les analytics
            self.update_analytics(user_msg.domain_category)
            
            return JsonResponse({
                'response': bot_response,
                'session_id': session.session_id,
                'message_id': bot_msg.id,
                'response_time': response_time
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    def get_or_create_session(self, request, session_id=None):
        """Créer ou récupérer une session de chat"""
        if session_id:
            try:
                session = ChatSession.objects.get(session_id=session_id, is_active=True)
                session.updated_at = timezone.now()
                session.save()
                return session
            except ChatSession.DoesNotExist:
                pass
        
        # Créer une nouvelle session
        session = ChatSession.objects.create(
            user=request.user if request.user.is_authenticated else None,
            session_id=str(uuid.uuid4()),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            ip_address=self.get_client_ip(request)
        )
        return session
    
    def get_client_ip(self, request):
        """Récupérer l'IP du client"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def classify_domain(self, message):
        """Classifier le domaine de la question"""
        message_lower = message.lower()
        
        # Mots-clés par domaine
        keywords = {
            'fiscalite': ['impôt', 'taxe', 'déclaration', 'fiscal', 'tva', 'ir', 'is', 'convention'],
            'immobilier': ['maison', 'appartement', 'terrain', 'achat', 'vente', 'location', 'immobilier'],
            'investissement': ['investir', 'placement', 'bourse', 'opcvm', 'action', 'obligation', 'projet'],
            'administration': ['consulat', 'passeport', 'visa', 'état civil', 'document', 'carte'],
            'formation': ['formation', 'diplôme', 'certification', 'cours', 'apprentissage', 'métier']
        }
        
        for domain, words in keywords.items():
            if any(word in message_lower for word in words):
                return domain
        
        return 'other'
    
    def generate_bot_response(self, user_message, session):
        """Générer une réponse du bot avec un système de fallback local"""
        print(f"DEBUG: Chatbot: Entered generate_bot_response for session {session.session_id}")
        print(f"DEBUG: Chatbot: User message: '{user_message}'")
        
        # Check if OpenAI configuration is available
        endpoint = getattr(settings, 'AZURE_OPENAI_ENDPOINT', '')
        api_key = getattr(settings, 'AZURE_OPENAI_API_KEY', '')
        
        if not endpoint or not api_key:
            print("INFO: Chatbot: Using local fallback response - no OpenAI configuration")
            return self.get_intelligent_fallback_response(user_message)

        # If OpenAI is configured, use the original Azure implementation
        return self.get_azure_response(user_message, session)
    
    def get_intelligent_fallback_response(self, user_message):
        """Générer une réponse intelligente basée sur des mots-clés locaux"""
        message_lower = user_message.lower()
        
        # Réponses basées sur les mots-clés
        if any(word in message_lower for word in ['bonjour', 'salut', 'hello', 'bonsoir']):
            return _("""Bonjour ! Je suis l'assistant virtuel de ServicesBLADI. 
            
Je peux vous aider avec :
• Les services disponibles au Maroc
• Les démarches administratives
• Les questions sur les documents
• L'orientation vers les bons services

Comment puis-je vous aider aujourd'hui ?""")
        
        elif any(word in message_lower for word in ['service', 'services', 'démarche', 'demarche']):
            return _("""ServicesBLADI offre de nombreux services au Maroc :

• **Services administratifs** : cartes d'identité, passeports, actes de naissance
• **Services juridiques** : conseils légaux, rédaction de contrats
• **Services de formation** : certifications, cours professionnels
• **Services de santé** : consultations, examens médicaux

Vous pouvez consulter la liste complète des services sur notre plateforme ou poser une question plus spécifique.""")
        
        elif any(word in message_lower for word in ['contact', 'telephone', 'téléphone', 'email', 'adresse']):
            return _("""Pour nous contacter :

• **Via la plateforme** : Utilisez notre système de messagerie intégré
• **Demande de service** : Créez une demande directement sur le site
• **Support technique** : Utilisez le chat en ligne

Notre équipe d'experts est disponible pour vous accompagner dans vos démarches.""")
        
        elif any(word in message_lower for word in ['prix', 'tarif', 'coût', 'cout', 'payement', 'paiement']):
            return _("""Les tarifs varient selon le type de service :

• **Consultation de base** : Gratuite
• **Services administratifs** : Variables selon la complexité
• **Services juridiques** : Devis personnalisé
• **Formations** : Tarifs préférentiels disponibles

Pour connaître le tarif exact de votre service, je vous recommande de créer une demande sur la plateforme.""")
        
        elif any(word in message_lower for word in ['merci', 'thanks', 'remercie']):
            return _("""Je vous en prie ! N'hésitez pas si vous avez d'autres questions.
            
L'équipe ServicesBLADI est toujours là pour vous accompagner dans vos démarches.""")
        
        else:
            # Réponse générale pour les questions non reconnues
            return _(f"""Je comprends que vous me demandez à propos de "{user_message}".

Bien que je ne puisse pas donner une réponse spécifique à cette question pour le moment, je peux vous orienter :

• **Pour des services spécialisés** : Consultez notre catalogue de services
• **Pour des questions complexes** : Créez une demande auprès d'un expert
• **Pour de l'aide immédiate** : Contactez notre support

Puis-je vous aider avec autre chose ou souhaitez-vous que je vous oriente vers un service particulier ?""")

    def get_azure_response(self, user_message, session):
        """Méthode originale pour Azure OpenAI (conservée pour compatibilité future)"""
        try:
            # Récupérer la configuration Azure OpenAI depuis les settings
            endpoint = getattr(settings, 'AZURE_OPENAI_ENDPOINT', '')
            api_key = getattr(settings, 'AZURE_OPENAI_API_KEY', '')
            api_version = getattr(settings, 'AZURE_OPENAI_API_VERSION', '2024-02-15-preview')
            model = getattr(settings, 'AZURE_OPENAI_MODEL', 'gpt-4o')
            
            print(f"DEBUG: Chatbot: Azure Endpoint: {'SET' if endpoint else 'NOT SET'}")
            print(f"DEBUG: Chatbot: Azure API Key: {'SET' if api_key else 'NOT SET'}")
            print(f"DEBUG: Chatbot: Azure API Version: {api_version}")
            print(f"DEBUG: Chatbot: Azure Model: {model}")

            if not endpoint or not api_key:
                print("ERROR: Chatbot: Azure OpenAI endpoint or API key is missing in settings.")
                return self.get_fallback_response("Missing Azure Configuration")

            # Vérifier si la question est similaire aux questions précédentes
            if self.is_question_repeated(user_message, session):
                print("DEBUG: Chatbot: Repeated question detected.")
                return _("""Je remarque que vous avez posé une question similaire. 

Pour vous aider au mieux, pourriez-vous :
• Préciser votre question
• Donner plus de détails sur votre situation
• Me dire si ma réponse précédente n\'était pas claire

Je suis là pour vous aider avec précision !""")
            
            # Simple fallback since Azure is disabled
            return self.get_fallback_response("Azure OpenAI Disabled")
        except Exception as e:
            print(f"ERROR: Chatbot: Unexpected error in Azure response: {type(e).__name__} - {str(e)}")
            return self.get_fallback_response(f"Unexpected Server Error: {type(e).__name__}")

    def get_fallback_response(self, error_type="Unknown Error"):
        """Retourner une réponse de secours générique avec le type d'erreur pour le débogage."""
        print(f"DEBUG: Chatbot: Using fallback response due to: {error_type}")
        # Log this specific fallback event
        ChatAnalytics.objects.update_or_create(
            date=timezone.now().date(), 
            defaults={'fallback_responses': F('fallback_responses') + 1}
        )
        # Show the error type in the fallback message for debugging
        fallback_message = getattr(settings, 'CHATBOT_FALLBACK_MESSAGE', 
                                 _(f"Je rencontre une difficulté technique temporaire pour traiter votre demande. Veuillez réessayer dans quelques instants. [Erreur: {error_type}]")
        )
        return fallback_message
    
    def get_content_policy_violation_response(self):
        print("DEBUG: Chatbot: Content policy violation detected.")
        return _("\"Je ne peux pas répondre à cette demande car elle semble enfreindre notre politique de contenu. Veuillez reformuler votre question ou essayer un sujet différent.\"")
    
    def get_system_prompt(self, user):
        """Construire le prompt système personnalisé"""
        client_status = "client inscrit" if user and user.is_authenticated else "nouveau visiteur"
        
        return f"""Tu es un expert des services aux Marocains Résidant à l'Étranger (MRE). 

DOMAINES D'EXPERTISE EXCLUSIFS:
- 📊 Fiscalité (impôts, déclarations, conventions fiscales)
- 🏠 Immobilier au Maroc (achat, vente, investissement)
- 💰 Investissements (OPCVM, bourse, projets)
- 📋 Administration (documents, visas, consulats)
- 🎓 Formation professionnelle (certifications, reconversion)

INSTRUCTIONS STRICTES:
1. Réponds UNIQUEMENT aux questions liées à ces 5 domaines
2. Si la question est hors sujet, réponds poliment que tu ne peux traiter que les sujets MRE
3. Si tu ne peux pas répondre précisément, propose une assistance personnalisée
4. L'utilisateur est actuellement: {client_status}

LOGIQUE CONDITIONNELLE:
- Si nouveau visiteur → propose inscription sur la plateforme
- Si client inscrit → propose de remplir une demande de service

STYLE DE RÉPONSE:
- Reste professionnel mais chaleureux
- Sois concis et précis
- Utilise des puces pour organiser l'information
- Propose toujours une action concrète

Réponds en français uniquement."""
    
    def update_analytics(self, domain_category):
        """Mettre à jour les analytics quotidiennes"""
        today = timezone.now().date()
        analytics, created = ChatAnalytics.objects.get_or_create(date=today)
        
        analytics.total_messages += 1
          # Incrémenter le compteur de domaine
        if domain_category == 'fiscalite':
            analytics.fiscalite_questions += 1
        elif domain_category == 'immobilier':
            analytics.immobilier_questions += 1
        elif domain_category == 'investissement':
            analytics.investissement_questions += 1
        elif domain_category == 'administration':
            analytics.administration_questions += 1
        elif domain_category == 'formation':
            analytics.formation_questions += 1
        else:
            analytics.off_topic_questions += 1
        
        analytics.save()

    def is_question_repeated(self, user_message, session):
        """Détecte si la question de l'utilisateur est similaire à la précédente dans la session, envoyée très récemment (30s)."""
        # Get the last user message (excluding the current one being saved)
        recent_messages = ChatMessage.objects.filter(session=session, message_type='user').order_by('-timestamp')[:2]
        if len(recent_messages) == 2:
            last_message = recent_messages[1]
            last_content = last_message.content.strip().lower()
            last_time = last_message.timestamp
            now = timezone.now()
            # Only consider repeated if last message is identical and sent within 30 seconds
            if user_message.strip().lower() == last_content and (now - last_time).total_seconds() < 30:
                return True
        return False


@method_decorator(csrf_exempt, name='dispatch')
class ChatFeedbackView(View):
    """API pour les retours utilisateur"""
    
    def post(self, request):
        """Enregistrer un feedback utilisateur"""
        try:
            data = json.loads(request.body)
            message_id = data.get('message_id')
            feedback_type = data.get('feedback_type')
            comment = data.get('comment', '')
            
            if not message_id or not feedback_type:
                return JsonResponse({'error': 'Données requises manquantes'}, status=400)
            
            try:
                message = ChatMessage.objects.get(id=message_id, message_type='bot')
            except ChatMessage.DoesNotExist:
                return JsonResponse({'error': 'Message non trouvé'}, status=404)
            
            # Créer ou mettre à jour le feedback
            feedback, created = ChatFeedback.objects.get_or_create(
                message=message,
                defaults={
                    'feedback_type': feedback_type,
                    'comment': comment,
                    'ip_address': self.get_client_ip(request)
                }
            )
            
            if not created:
                feedback.feedback_type = feedback_type
                feedback.comment = comment
                feedback.save()
            
            return JsonResponse({'status': 'success'})
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    def get_client_ip(self, request):
        """Récupérer l'IP du client"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


@login_required
def chatbot_analytics_view(request):
    """Vue pour les analytics du chatbot (admin seulement)"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Non autorisé'}, status=403)
    
    # Analytics des 30 derniers jours
    thirty_days_ago = timezone.now().date() - timedelta(days=30)
    analytics = ChatAnalytics.objects.filter(date__gte=thirty_days_ago).order_by('-date')
    
    # Statistiques globales
    total_sessions = ChatSession.objects.count()
    total_messages = ChatMessage.objects.count()
    total_feedback = ChatFeedback.objects.count()
    
    # Répartition par domaine
    domain_stats = ChatMessage.objects.filter(
        timestamp__gte=thirty_days_ago,
        message_type='user'
    ).values('domain_category').annotate(
        count=Count('id')
    ).order_by('-count')
    
    context = {
        'analytics': analytics,
        'total_sessions': total_sessions,
        'total_messages': total_messages,
        'total_feedback': total_feedback,
        'domain_stats': domain_stats,
    }
    
    return render(request, 'chatbot/analytics.html', context)
