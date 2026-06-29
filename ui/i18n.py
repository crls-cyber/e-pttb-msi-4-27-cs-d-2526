"""Internationalization (i18n) system for UI."""
import json
import os
from flask import request, session

SUPPORTED_LANGUAGES = ['en', 'fr']
DEFAULT_LANGUAGE = 'en'

def get_locale():
    """Determine the user's preferred language."""
    # 1. Check URL path first (allows switching language)
    if request.path.startswith('/fr/'):
        session['lang'] = 'fr'
        return 'fr'
    elif request.path.startswith('/en/'):
        session['lang'] = 'en'
        return 'en'
    # 2. Check session
    if 'lang' in session and session['lang'] in SUPPORTED_LANGUAGES:
        return session['lang']
    lang = request.accept_languages.best_match(SUPPORTED_LANGUAGES)
    if lang:
        session['lang'] = lang
        return lang
    
    # 4. Default
    session['lang'] = DEFAULT_LANGUAGE
    return DEFAULT_LANGUAGE

def get_translations():
    """Load translations for the current locale."""
    lang = get_locale()
    translations_file = os.path.join(
        os.path.dirname(__file__),
        'translations',
        f'{lang}.json'
    )
    
    try:
        with open(translations_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def t(key, default=None):
    """Translate a key with support for nested keys (e.g., 'nav.dashboard')."""
    translations = get_translations()
    
    # Support nested keys like 'nav.dashboard'
    keys = key.split('.')
    value = translations
    
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            return default if default is not None else key
    
    return value
