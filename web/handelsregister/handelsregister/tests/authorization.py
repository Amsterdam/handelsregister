import time
import jwt

from django.conf import settings

from authorization_django import levels as authorization_levels


class AuthorizationSetup(object):
    """
    Helper methods to setup JWT tokens and authorization levels

    sets the following attributes:

    token_scope_hr
    """

    def setUpAuthorization(self):
        """
        SET

        token_scope_hr

        to use with:

        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer {}'.format(self.token_scope_hr))

        """
        # NEW STYLE AUTH
        key = settings.DATAPUNT_AUTHZ['JWT_SECRET_KEY']
        algorithm = settings.DATAPUNT_AUTHZ['JWT_ALGORITHM']

        now = int(time.time())

        token_scope_hr_r = jwt.encode({
            'scopes' : [authorization_levels.SCOPE_HR_R],
            'iat': now, 'exp': now + 600}, key, algorithm=algorithm)

        self.token_scope_hr_r  = str(token_scope_hr_r, 'utf-8')