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
        setattr(self.configuration, "sections", global_preferences_registry.manager()["beachguard__sections"])

    @property
    def configuration_form_class(self):
        class ConfigurationForm(super().configuration_form_class):
            sections = None

        return ConfigurationForm

    def render_configuration_form(self, *args, form=None, **kwargs):
        form = form or self.get_configuration_form(*args, **kwargs)
        template = Template(
            template_string="{% load crispy_forms_filters %}{{ form|crispy }}"
        ).render(Context({"form": form}))
        return template
