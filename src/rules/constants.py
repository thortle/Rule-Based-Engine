"""
Lexical Indicators - Shared Constants for Semantic Rules

This module contains lexical resources used across different semantic rules
to identify temporal expressions, prepositions, relative pronouns, etc.

Design principle: Centralize constants to avoid duplication and ease maintenance.
"""

from typing import Set


# Temporal expressions
TEMPORAL_WORDS: Set[str] = {
    # Time units
    'h', 'heure', 'heures', 'minute', 'minutes', 'seconde', 'secondes',
    
    # Parts of day
    'matin', 'midi', 'après-midi', 'soir', 'nuit', 'minuit',
    
    # Days of week
    'lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi', 'dimanche',
    'jour', 'jours', 'journée',
    
    # Months
    'janvier', 'février', 'mars', 'avril', 'mai', 'juin',
    'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre',
    
    # Time periods
    'mois', 'an', 'ans', 'année', 'années', 'semaine', 'semaines',
    
    # Temporal references
    'hier', 'aujourd\'hui', 'demain', 'maintenant',
    'ce', 'cette', 'dernier', 'dernière', 'prochain', 'prochaine'
}

# Prepositions (French)
PREPOSITIONS: Set[str] = {
    'à', 'de', 'en', 'dans', 'sur', 'sous', 'pour', 'par', 'avec',
    'sans', 'chez', 'vers', 'contre', 'depuis', 'pendant', 'avant',
    'après', 'devant', 'derrière', 'entre', 'parmi', 'selon'
}

# Relative pronouns
RELATIVE_PRONOUNS: Set[str] = {
    'qui', 'que', 'qu\'', 'dont', 'où', 'lequel', 'laquelle',
    'lesquels', 'lesquelles', 'auquel', 'duquel', 'auxquels'
}

# Quantity/measurement words
QUANTITY_WORDS: Set[str] = {
    'kilo', 'kilos', 'gramme', 'grammes', 'litre', 'litres',
    'mètre', 'mètres', 'centimètre', 'kilomètre',
    'heure', 'heures', 'minute', 'minutes', 'jour', 'jours'
}
