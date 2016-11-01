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

    def get_id(self) -> str:
        """
        We expect only digits
        """

        if not self._token_count or self._token_count > 1:
            return ""

        first = self._tokens[0]

        if first.isdigit():
            return first

        return ""

    def get_handelsnaam(self) -> str:
        """
        Get the querystring
        """
        # could be anything...
        return self._cleaned_query
