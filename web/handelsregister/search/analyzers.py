"""
A collection of custom elastic search filters and analyzers
that are used throughout.
"""

import elasticsearch_dsl as es

from elasticsearch_dsl import analysis, tokenizer


####################################
#            Filters               #
####################################

# Replaces the number street shortening with the actual word
synonym_filter = analysis.token_filter(
    'synonyms',
    type='synonym',
    synonyms=[
        '1e, eerste => 1e, eerste',
        '2e, tweede => 2e, tweede',
        '3e, derde  => 3e, derde',
        '4e, vierde => 4e, vierde',
    ]
)

# Change dash and dot to space
naam_stripper = analysis.char_filter(
    'naam_stripper',
    type='mapping',
    mappings=[
        "-=>' '",  # change '-' to separator
        ".=>' '",  # change '.' to separator
        "/=>' '",  # change '/' to separator
    ]
)

# Create edge ngram filtering to postcode
edge_ngram_filter = analysis.token_filter(
    'edge_ngram_filter',
    type='edge_ngram',
    min_gram=1,
    max_gram=15
)

####################################
#           Analyzers              #
####################################

adres = es.analyzer(
    'adres',
    tokenizer='standard',
    filter=['lowercase', 'asciifolding', synonym_filter],
    # fi`lter=['lowercase', 'asciifolding'],
    char_filter=[naam_stripper],
)

autocomplete = es.analyzer(
    'autocomplete',
    tokenizer='standard',
    filter=['lowercase', edge_ngram_filter]
)
