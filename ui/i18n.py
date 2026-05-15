"""Internationalization helper for Flask UI."""
import json
import os
from flask import session, request

TRANSLATIONS_DIR = os.path.join(os.path.dirname(__file__), 'translations')
SUPPORTED_LANGUAGES = ['en', 'fr']
DEFAULT_LANGUAGE = 'en'

_translations_cache = {}

def load_translations(lang):
    """Load translations for a given language."""
    if lang not in _translations_cache:
        filepath = os.path.join(TRANSLATIONS_DIR, f'{lang}.json')
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                _translations_cache[lang] = json.load(f)
        else:
            _translations_cache[lang] = {}
    return _translations_cache[lang]

def get_locale():
    """Get current locale from session or request."""
    # 1. Check session
    if 'lang' in session:
        lang = session['lang']
        if lang in SUPPORTED_LANGUAGES:
            return lang
    
    # 2. Check URL prefix
    if request.path.startswith('/fr/'):
        return 'fr'
    elif request.path.startswith('/en/'):
        return 'en'
    
    # 3. Check browser Accept-Language header
    lang = request.accept_languages.best_match(SUPPORTED_LANGUAGES)
    if lang:
        return lang
    
    # 4. Default
    return DEFAULT_LANGUAGE

def get_translations():
    """Get translations for current locale."""
    locale = get_locale()
    return load_translations(locale)

def t(key, **kwargs):
    """Translate a key. Supports nested keys with dot notation.
    
    Example:
        t('nav.dashboard')  # Returns "Dashboard" in EN or "Tableau de bord" in FR
        t('hello', name='John')  # Supports formatting
    """
    translations = get_translations()
    
    # Support nested keys (e.g., 'nav.dashboard')
    keys = key.split('.')
    value = translations
    for k in keys:
        if isinstance(value, dict):
            value = value.get(k, key)
        else:
            return key
    
    # Format if kwargs provided
    if kwargs and isinstance(value, str):
        try:
            return value.format(**kwargs)
        except:
            return value
    
    return value if value else key
