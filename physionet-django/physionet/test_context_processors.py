from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse

from physionet.context_processors import dataset_apps_config


class TestDatasetAppsConfig(TestCase):
    """
    Tests for the context processor that guards the published project page's extension
    point. The flag has to reach templates whether or not the applications package is
    installed, which is why it is defined here rather than in that package.
    """

    def test_context_processor_is_installed(self):
        self.assertIn(
            'physionet.context_processors.dataset_apps_config',
            settings.TEMPLATES[0]['OPTIONS']['context_processors'],
        )

    @override_settings(ENABLE_DATASET_APPS=False)
    def test_flag_is_false_when_the_feature_is_disabled(self):
        self.assertEqual(dataset_apps_config(None)['dataset_apps_enabled'], False)

    @override_settings(ENABLE_DATASET_APPS=True)
    def test_flag_is_true_when_the_feature_is_enabled(self):
        self.assertEqual(dataset_apps_config(None)['dataset_apps_enabled'], True)

    def test_flag_reaches_the_template_context(self):
        response = self.client.get(reverse('home'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['dataset_apps_enabled'], settings.ENABLE_DATASET_APPS)
