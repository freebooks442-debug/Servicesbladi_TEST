import time
import random

def language_context(request):
    """
    Context processor that adds the current language code to the template context.
    This allows JavaScript to access the current language.
    """
    return {
        'LANGUAGE_CODE': getattr(request, 'LANGUAGE_CODE', 'fr')
    }

def cache_version_context(request):
    """
    Add cache version information to the template context
    to prevent cached pages from different versions.
    """
    # Timestamp actuel si pas encore défini
    if not hasattr(request, 'request_time'):
        request.request_time = int(time.time())
    
    # Version de cache si pas dans la session
    if 'cache_version' not in request.session:
        cache_version = f"{request.request_time}.{random.randint(1000, 9999)}"
        request.session['cache_version'] = cache_version
        request.session.modified = True
    
    return {
        'cache_version': request.session.get('cache_version', ''),
        'request_time': request.request_time,
        'timestamp': int(time.time()),
    }