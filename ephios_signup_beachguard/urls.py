from django.urls import path

from ephios_signup_beachguard.views import BeachguardSectionSettingsView

app_name = "signup_beachguard"
urlpatterns = [
    path("settings/beachguard/", BeachguardSectionSettingsView.as_view(), name="sections"),
]
