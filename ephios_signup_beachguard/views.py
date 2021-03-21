import io

from django.contrib import messages
from django.forms import HiddenInput, Field
from django.http import FileResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views import View
from django.views.generic import FormView
from dynamic_preferences.registries import global_preferences_registry
from ephios.core.models import Shift, AbstractParticipation
from ephios.core.views.settings import SettingsViewMixin
from ephios.plugins.basesignup.signup.section_based import SectionBasedConfigurationForm
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

from ephios_signup_beachguard.signup import BeachguardSignupMethod


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


def pdf_export(request, *args, **kwargs):
    buffer = io.BytesIO()
    p = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        title="ephios beachguard export",
        leftMargin=1 * cm,
        rightMargin=1 * cm,
        topMargin=1 * cm,
        bottomMargin=1 * cm,
    )
    style = getSampleStyleSheet()
    story = [
        Paragraph("Events", style["Heading1"]),
        Spacer(height=0.5 * cm, width=19 * cm),
    ]
    shifts = Shift.objects.filter(signup_method_slug=BeachguardSignupMethod.slug)
    sections = global_preferences_registry.manager()["beachguard__sections"]

    for shift in shifts:
        story.append(Paragraph(shift.get_start_end_time_display(), style["Heading2"]))
        for section in sections:
            section_participants = [f"{participation.participant.first_name} {participation.participant.last_name}" for participation in AbstractParticipation.objects.filter(
                shift=shift, data__dispatched_section_uuid=section["uuid"]
            )]
            story.append(Paragraph(f"{section['title']}: {', '.join(section_participants)}"))

    p.build(story)
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=False, filename="beachguard.pdf")
