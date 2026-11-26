from django.apps import AppConfig
from django.db.models.signals import post_migrate


def _create_views(sender, using="default", **kwargs):
    from . import sqlqueries

    sqlqueries.create_views(using)


class AnalyticsConfig(AppConfig):
    name = "apps.analytics"
    label = "analytics"

    def ready(self):
        # Las vistas SQL se recrean al terminar cada `migrate`.
        post_migrate.connect(_create_views, sender=self, dispatch_uid="seov_create_sql_views")