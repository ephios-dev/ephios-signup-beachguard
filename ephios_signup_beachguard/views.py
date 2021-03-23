import io

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.forms import HiddenInput, Field
from django.http import FileResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.formats import date_format
from django.utils.translation import gettext as _
from django.views.generic import FormView
from dynamic_preferences.registries import global_preferences_registry
from ephios.core.models import Shift, AbstractParticipation
from ephios.core.views.settings import SettingsViewMixin
from ephios.plugins.basesignup.signup.section_based import SectionBasedConfigurationForm
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

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


@login_required
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
    story = []
    shifts = Shift.objects.filter(signup_method_slug=BeachguardSignupMethod.slug).order_by("start_time")

    # create a matrix of sections and shifts which contain the corresponding participations.
    # this is a separate step to calculate the number of rows we need for each section.
    participations = {}
    for section in global_preferences_registry.manager()["beachguard__sections"]:
        participations[section["uuid"]] = {}
        for shift in shifts:
            participations[section["uuid"]][shift.pk] = AbstractParticipation.objects.filter(
                shift=shift, data__dispatched_section_uuid=section["uuid"]
            )
        participations[section["uuid"]]["row_count"] = max(len(max(participations[section["uuid"]].values(), key=lambda key: len(key))), section["min_count"])
        participations[section["uuid"]]["title"] = section["title"]

    # sort the sections ascending by row_count to create a nice look in the export
    participations = {k: v for k, v in sorted(participations.items(), key=lambda item: item[1]["row_count"])}

    # build the table header with the section names
    columns = []
    header = [""]
    for section_uuid, section_participations in participations.items():
        header.extend([Paragraph(section_participations["title"])] * section_participations["row_count"])
    columns.append(header)

    # finally build the table contents
    for shift in shifts:
        column = [Paragraph(date_format(shift.start_time, "SHORT_DATE_FORMAT"))]
        for section_uuid, section_participations in participations.items():
            participant_rows = []
            for participation in section_participations[shift.pk]:
                participant_rows.append(Paragraph(f"{participation.participant.first_name} {participation.participant.last_name}"))
            if len(participant_rows) < section_participations["row_count"]:
                participant_rows.extend([Paragraph("")] * (section_participations["row_count"] - len(participant_rows)))
            column.extend(participant_rows)
        columns.append(column)

    table = Table(columns)
    table.setStyle(
        TableStyle(
            [
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.black),
                ("BOX", (0, 0), (-1, -1), 0.25, colors.black),
            ]
        )
    )
    story.append(table)
    p.build(story)
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=False, filename="beachguard.pdf")
