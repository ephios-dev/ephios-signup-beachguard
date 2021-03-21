from django.contrib import messages
from django.forms import HiddenInput, Field
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.generic import FormView
from dynamic_preferences.registries import global_preferences_registry
from ephios.core.views.settings import SettingsViewMixin
from ephios.plugins.basesignup.signup.section_based import SectionBasedConfigurationForm


class BeachguardSectionSettingsView(SettingsViewMixin, FormView):
    template_name = "signup_beachguard/sections.html"

    def get_form(self, form_class=None):
        form = SectionBasedConfigurationForm(
            self.request.POST or None,
            initial={"sections": global_preferences_registry.manager()["beachguard__sections"]}
        )
        form.fields["sections"] = Field(widget=HiddenInput, required=False)
        return form

    def form_valid(self, form):
        global_preferences_registry.manager()["beachguard__sections"] = form.cleaned_data["sections"]
        messages.success(self.request, _("Sections saved successfully."))
        return redirect(reverse("signup_beachguard:sections"))
