from django.forms import Form
from django.template import Context, Template
from django.utils.translation import gettext_lazy as _
from dynamic_preferences.registries import global_preferences_registry
from ephios.plugins.basesignup.signup.section_based import SectionBasedSignupMethod


class BeachguardSignupMethod(SectionBasedSignupMethod):
    slug = "beachguard"
    verbose_name = _("Signup for beachguard events")
    description = _(
        """This plugin provides a signup method for beach guards where there are regular shifts which all share the same configuration"""
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        setattr(
            self.configuration,
            "sections",
            global_preferences_registry.manager()["beachguard__sections"],
        )

    @property
    def configuration_form_class(self):
        class ConfigurationForm(super().configuration_form_class):
            template_name = "core/signup_configuration_form.html"
            sections = None

        return ConfigurationForm
