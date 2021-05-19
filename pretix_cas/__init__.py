from django.utils.translation import gettext_lazy as _

from pretix.base.plugins import PluginConfig


class PluginApp(PluginConfig):
    name = 'pretix_cas'
    verbose_name = 'Apereo CAS authentication backend for pretix'

    class PretixPluginMeta:
        name = _('CAS backend')
        author = 'BP 2019/20 Gruppe 45'
        description = _('Enables users to log into Pretix using Apereo CAS SSO servers')
        visible = True
        version = '0.9.1'
        compatibility = "pretix>=3.4.0"

    def ready(self):
        from . import signals  # NOQA


default_app_config = 'pretix_cas.PluginApp'
