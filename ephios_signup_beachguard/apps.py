from ephios.core.plugins import PluginConfig
from django.utils.translation import gettext_lazy as _

class PluginApp(PluginConfig):
    name = "ephios_signup_beachguard"

    class EphiosPluginMeta:
        name = _("Lifeguard Signup")
        author = "Julian Baumann <julian@ephios.de>"
        description = _("This plugin provides a signup method for beach guards where there are regular shifts which all share the same configuration")

    def ready(self):
        from . import signals  # NOQA
