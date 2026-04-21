from django.apps import AppConfig


class JobsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.jobs'
    label = 'jobs'

    def ready(self):
        # Scheduler is started on first user login, not on server boot.
        # See apps/accounts/views.py → login view.
        pass