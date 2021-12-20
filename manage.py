#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'undead_mongoose.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
        
    sentry_sdk.init(
        dsn="https://81d42f218e87445eba781aeb0356f596@o118727.ingest.sentry.io/6115401",
        integrations=[DjangoIntegration()],

        traces_sample_rate=1.0,
        send_default_pii=True
    )
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
