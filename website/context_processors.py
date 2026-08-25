"""Context processors exposed to every template."""
from .models import SiteSetting


def site_settings(request):
    """Make the singleton SiteSetting available as ``{{ site }}``."""
    try:
        return {'site': SiteSetting.get()}
    except Exception:
        # Migrations not applied yet — don't crash the admin.
        return {'site': None}
