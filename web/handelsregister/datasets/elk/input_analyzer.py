"""
Analyze the query input from user before starting the
search
"""
import string
import re


_REPLACE_TABLE = "".maketrans(
    string.punctuation, len(string.punctuation) * " ")


class InputQAnalyzer(object):
    """
    The InoutQAnalyzer takes a plain query string and performs various analyses
    on it.  It contains various is_XXX methods that are used to determine if
    this query could refer to an XXX.
    """

    def __init__(self, query: str):
        self.query = query
        self._cleaned_query = query.translate(_REPLACE_TABLE).lower()
        self._tokens = re.findall('[^0-9 ]+|\\d+', self._cleaned_query)
        self._token_count = len(self._tokens)

        self._huisnummer_index = None
        for i, token in enumerate(self._tokens[1:]):
            if token.isdigit():
                self._huisnummer_index = i + 1
                break
