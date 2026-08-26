from django.apps import AppConfig


class PhysionetConfig(AppConfig):
    name = 'physionet'

    def ready(self):
        from physionet import checks  # noqa: F401
