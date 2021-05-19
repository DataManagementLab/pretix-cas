import cas
from django.utils.translation import ugettext_lazy as _

from pretix.base.auth import BaseAuthBackend
from pretix.settings import config
from pretix.helpers.urls import build_absolute_uri


class CasAuthBackend(BaseAuthBackend):
    """
    This class implements the interface for pluggable authentication modules used by pretix.
    """

    """
    A short and unique identifier for this authentication backend.
    This should only contain lowercase letters and in most cases will
    be the same as your package name.
    """
    identifier = 'cas_sso_auth'

    """
    A human-readable name of this authentication backend.
    """
    @property
    def verbose_name(self):
        return config.get('pretix_cas', 'cas_server_name', fallback=_('CAS SSO'))

    def request_authenticate(self, request):
        """
        This method will be called when the user opens the login form. If the user already has a valid session
        according to your login mechanism, for example a cookie set by a different system or HTTP header set by a
        reverse proxy, you can directly return a ``User`` object that will be logged in.

        ``request`` will contain the current request.
        You are expected to either return a ``User`` object (if login was successful) or ``None``.
        """
        return

    def authentication_url(self, request):
        """
        This method will be called to populate the URL for the authentication method's tab on the login page.
        """

        # This is the absolute URL of the view that receives the ticket from the client (generated by the CAS Server).
        return_address = build_absolute_uri('plugins:pretix_cas:cas.response')

        # The CASClient is created on every request because the domain of the pretix instance is not fixed.
        cas_client = cas.CASClient(
            version=config.get('pretix_cas', 'cas_version', fallback='CAS_2_SAML_1_0'),
            server_url=config.get('pretix_cas', 'cas_server_url', fallback='https://sso.tu-darmstadt.de'),
            service_url=return_address
        )
        return cas_client.get_login_url()
