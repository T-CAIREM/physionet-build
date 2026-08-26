from django.test import SimpleTestCase, override_settings

from physionet.checks import dataset_apps_isolation


class TestDatasetAppsIsolationCheck(SimpleTestCase):
    """
    Tests for the system check that guards the same-site mitigations the dataset
    applications depend on.
    """

    def warning_ids(self):
        return [warning.id for warning in dataset_apps_isolation(app_configs=None)]

    @override_settings(
        ENABLE_DATASET_APPS=False,
        DATASET_APPS_DOMAIN='apps.example.org',
        SESSION_COOKIE_DOMAIN='.example.org',
        CSRF_COOKIE_DOMAIN='.example.org',
        CSRF_TRUSTED_ORIGINS=['https://chat.apps.example.org'],
        CORS_ALLOW_ALL_ORIGINS=True,
        CORS_ALLOW_CREDENTIALS=True,
    )
    def test_nothing_is_reported_when_the_feature_is_disabled(self):
        self.assertEqual(self.warning_ids(), [])

    @override_settings(ENABLE_DATASET_APPS=True, DATASET_APPS_DOMAIN='apps.example.org')
    def test_nothing_is_reported_for_the_default_settings(self):
        self.assertEqual(self.warning_ids(), [])

    @override_settings(ENABLE_DATASET_APPS=True, SESSION_COOKIE_DOMAIN='.example.org')
    def test_session_cookie_domain_is_reported(self):
        self.assertIn('physionet.W001', self.warning_ids())

    @override_settings(ENABLE_DATASET_APPS=True, CSRF_COOKIE_DOMAIN='.example.org')
    def test_csrf_cookie_domain_is_reported(self):
        self.assertIn('physionet.W002', self.warning_ids())

    @override_settings(
        ENABLE_DATASET_APPS=True,
        DATASET_APPS_DOMAIN='apps.example.org',
        CSRF_TRUSTED_ORIGINS=['https://chat.apps.example.org', 'https://www.example.org'],
    )
    def test_trusted_application_origin_is_reported(self):
        self.assertIn('physionet.W003', self.warning_ids())

    @override_settings(
        ENABLE_DATASET_APPS=True,
        DATASET_APPS_DOMAIN='apps.example.org',
        CSRF_TRUSTED_ORIGINS=['https://www.example.org'],
    )
    def test_unrelated_trusted_origin_is_not_reported(self):
        self.assertNotIn('physionet.W003', self.warning_ids())

    @override_settings(
        ENABLE_DATASET_APPS=True, DATASET_APPS_DOMAIN='', CSRF_TRUSTED_ORIGINS=['https://a.example.org']
    )
    def test_no_application_domain_reports_no_origins(self):
        self.assertNotIn('physionet.W003', self.warning_ids())

    @override_settings(ENABLE_DATASET_APPS=True, CORS_ALLOW_ALL_ORIGINS=True)
    def test_cors_allow_all_origins_is_reported(self):
        self.assertIn('physionet.W004', self.warning_ids())

    @override_settings(ENABLE_DATASET_APPS=True, CORS_ALLOW_CREDENTIALS=True)
    def test_cors_allow_credentials_is_reported(self):
        self.assertIn('physionet.W005', self.warning_ids())
