from django.urls import path

from ephios_signup_beachguard.views import BeachguardSectionSettingsView, pdf_export

app_name = "signup_beachguard"
urlpatterns = [
    path("settings/beachguard/", BeachguardSectionSettingsView.as_view(), name="sections"),
    path("beachguard/pdf/", pdf_export, name="pdf_export")
]
