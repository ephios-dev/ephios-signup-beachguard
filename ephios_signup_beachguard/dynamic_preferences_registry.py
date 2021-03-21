from dynamic_preferences.preferences import Section
from dynamic_preferences.registries import global_preferences_registry
from ephios.extra.preferences import DictPreference

beachguard_section = Section("beachguard")


@global_preferences_registry.register
class BeachguardSectionsPreference(DictPreference):
    name = "sections"
    section = beachguard_section
    default = []
