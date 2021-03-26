import io
from datetime import date
from math import ceil

from django.db.models import Q
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
from ephios.core.models import Event, Shift, AbstractParticipation
from ephios.core.views.settings import SettingsViewMixin
from ephios.plugins.basesignup.signup.section_based import SectionBasedConfigurationForm
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
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
    events = request.POST.getlist("bulk_action")
    shifts = Shift.objects.filter(signup_method_slug=BeachguardSignupMethod.slug, event__in=events).order_by("start_time")
    events_with_other_methods = Event.objects.filter(Q(id__in=events), ~Q(shifts__in=shifts))
    if not events or not shifts:
        messages.info(request, _("No events with the beachguard signup method have been selected."))
        return redirect(reverse("core:event_list"))

    buffer = io.BytesIO()
    p = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        title=_("Roster"),
        leftMargin=0.6 * cm,
        rightMargin=1 * cm,
        topMargin=0.2 * cm,
        bottomMargin=0.5 * cm,
    )
    style = getSampleStyleSheet()
    story = [Paragraph("Roster", style=style["Title"])]

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
    header = [""]
    for section_uuid, section_participations in participations.items():
        header.extend([section_participations["title"]] * section_participations["row_count"])


    for chunk in range(0, ceil(shifts.count()/9)):
        columns = []
        columns.append(header)

        # finally build the table contents
        for shift in shifts[chunk*9:(chunk+1)*9]:
            column = [date_format(shift.start_time, "DATE_FORMAT")]
            for section_uuid, section_participations in participations.items():
                participant_rows = []
                for participation in section_participations[shift.pk]:
                    last_name = participation.participant.last_name
                    if len(participation.participant.first_name) + len(last_name) > 17:
                        last_name = "{initals}.".format(initals=last_name[0])
                    participant_name = "{first} {last}".format(first=participation.participant.first_name, last=last_name)
                    participant_rows.append(participant_name)
                if len(participant_rows) < section_participations["row_count"]:
                    participant_rows.extend([""] * (section_participations["row_count"] - len(participant_rows)))
                column.extend(participant_rows)
            columns.append(column)

        table = Table([list(x) for x in zip(*columns)], colWidths=[2.8 * cm]*10, hAlign="LEFT")
        table.setStyle(
            TableStyle(
                [
                    ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.black),
                    ("BOX", (0, 0), (-1, -1), 0.25, colors.black),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 1),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ]
            )
        )
        story.append(table)
        story.append(Spacer(width=20*cm, height=0.4*cm))

    story.append(Paragraph(_("Other events: {description}").format(description=", ".join([f"{event.title} ({date_format(event.get_start_time(), format='SHORT_DATETIME_FORMAT')} - {date_format(event.get_end_time(), format='SHORT_DATETIME_FORMAT')})" for event in events_with_other_methods]))))
    story.append(Spacer(width=20 * cm, height=0.1 * cm))
    story.append(Paragraph(_("as of: {date}").format(date=date_format(date.today(), format="SHORT_DATE_FORMAT"))))

    p.build(story)
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=False, filename="ephios.pdf")
