from django.apps import AppConfig


class PainelConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "painel"
    verbose_name = "Painel dos Noivos"

    def ready(self):
        from . import signals  # noqa: F401
