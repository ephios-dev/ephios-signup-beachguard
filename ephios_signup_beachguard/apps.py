from ephios.core.plugins import PluginConfig


class PluginApp(PluginConfig):
    name = "ephios_signup_beachguard"

    class EphiosPluginMeta:
        name = "ephios_signup_beachguard"
        author = "Julian Baumann <julian@ephios.de>"
        description = "This plugin provides a signup method for beach guards where there are regular shifts which all share the same configuration"

    def ready(self):
        from . import signals  # NOQA
