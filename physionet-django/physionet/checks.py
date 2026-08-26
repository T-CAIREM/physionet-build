"""
Project-wide Django system checks.
"""
from urllib.parse import urlsplit

from django.conf import settings
from django.core import checks


def _origin_is_under(origin, domain):
    """
    Checks if an origin (as written in CSRF_TRUSTED_ORIGINS) names the given domain or a
    host below it. Wildcards are stripped before comparison.
    """
    host = urlsplit(origin).hostname or origin
    host = host.lstrip('*').lstrip('.').lower()
    domain = domain.lstrip('*').lstrip('.').lower()

    return bool(domain) and (host == domain or host.endswith('.' + domain))


@checks.register(checks.Tags.security)
def dataset_apps_isolation(app_configs, **kwargs):
    """
    Applications are served from their own origins, which are hosts under the platform's
    own registrable domain. That is an origin boundary, not a site boundary, so anything
    scoped to the site rather than to the host is shared with them. These settings each
    widen the portal's own scope to those origins, and none of them is needed for the
    applications to work.
    """
    if not getattr(settings, 'ENABLE_DATASET_APPS', False):
        return []

    errors = []
    apps_domain = getattr(settings, 'DATASET_APPS_DOMAIN', '')

    if getattr(settings, 'SESSION_COOKIE_DOMAIN', None):
        errors.append(
            checks.Warning(
                'SESSION_COOKIE_DOMAIN is set while dataset applications are enabled.',
                hint='A domain-scoped session cookie is sent to every host under that domain, '
                'including the application origins. Leave it unset so the cookie stays host-only.',
                id='physionet.W001',
            )
        )

    if getattr(settings, 'CSRF_COOKIE_DOMAIN', None):
        errors.append(
            checks.Warning(
                'CSRF_COOKIE_DOMAIN is set while dataset applications are enabled.',
                hint='A domain-scoped CSRF cookie is readable by every host under that domain, '
                'including the application origins. Leave it unset so the cookie stays host-only.',
                id='physionet.W002',
            )
        )

    trusted_origins = getattr(settings, 'CSRF_TRUSTED_ORIGINS', []) or []
    offending_origins = [origin for origin in trusted_origins if _origin_is_under(origin, apps_domain)]
    if offending_origins:
        errors.append(
            checks.Warning(
                'CSRF_TRUSTED_ORIGINS contains application origins: {}.'.format(', '.join(offending_origins)),
                hint='Trusting an application origin lets it post authenticated state-changing requests '
                'to the portal. Applications talk to the portal with bearer tokens, not cookies, '
                'so they never need to be trusted here.',
                id='physionet.W003',
            )
        )

    if getattr(settings, 'CORS_ALLOW_ALL_ORIGINS', False):
        errors.append(
            checks.Warning(
                'CORS_ALLOW_ALL_ORIGINS is enabled while dataset applications are enabled.',
                hint='Allow the application origins explicitly instead; a wildcard also admits every '
                'other origin on the internet.',
                id='physionet.W004',
            )
        )

    if getattr(settings, 'CORS_ALLOW_CREDENTIALS', False):
        errors.append(
            checks.Warning(
                'CORS_ALLOW_CREDENTIALS is enabled while dataset applications are enabled.',
                hint='Application requests to the portal carry a bearer token, never the portal session '
                'cookie. Enabling credentialed cross-origin requests turns an application origin '
                'into a confused deputy for the signed-in user.',
                id='physionet.W005',
            )
        )

    return errors
