from django.dispatch import receiver
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from ephios.core.signals import register_signup_methods, administration_settings_section, register_event_bulk_action

from ephios_signup_beachguard.signup import BeachguardSignupMethod


@receiver(register_signup_methods)
def register_beachguard_signup(sender, **kwargs):
    return [BeachguardSignupMethod]

@receiver(administration_settings_section)
def register_beachguard_settingsview(sender, request, **kwargs):
    return [
        {
            "label": _("Beachguard signup"),
            "url": reverse("signup_beachguard:sections"),
            "active": request.resolver_match.url_name == "sections",
        },
    ]


@receiver(register_event_bulk_action)
def register_pdf_export_action(sender, **kwargs):
    return [
        dict(url=reverse("signup_beachguard:pdf_export"), label=_("Export roster for selected"), icon="fa-file-pdf")
    ]
