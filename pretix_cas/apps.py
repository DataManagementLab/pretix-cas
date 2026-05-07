from django.utils.translation import gettext_lazy as _

try:
    from pretix.base.plugins import PluginConfig
except ImportError:
    raise RuntimeError("Please use pretix 2.7 or above to run this plugin!")

class PluginApp(PluginConfig):
    name = 'pretix_cas'
    verbose_name = 'Apereo CAS authentication backend for pretix'

    class PretixPluginMeta:
        name = _('CAS backend')
        author = 'Benjamin Haettasch & TU Darmstadt BP Informatik 2019/20 Group 45'
        description = _('Enables users to log into Pretix using Apereo CAS SSO servers')
        visible = True
        version = '1.3.0a'
        compatibility = "pretix>=2024.7.0"

    def ready(self):
        from . import signals  # NOQA
