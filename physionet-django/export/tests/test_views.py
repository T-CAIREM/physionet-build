from datetime import timedelta

from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from oauth2_provider.models import get_access_token_model, get_application_model
from rest_framework.test import APIClient
from rest_framework import status

from project.models import PublishedProject, ProjectType, AccessPolicy
from user.models import User

Application = get_application_model()
AccessToken = get_access_token_model()


class TestRateLimiting(TestCase):
    """Test rate limiting on API endpoints"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()

        # Create test project
        self.project = PublishedProject.objects.create(
            slug='test-project',
            version='1.0.0',
            title='Test Project',
            abstract='Test abstract',
            access_policy=AccessPolicy.CREDENTIALED
        )

        # Create test resource type
        self.resource_type = ProjectType.objects.create(
            name='TestType'
        )

    def test_anonymous_rate_limit(self):
        """Test rate limiting for anonymous users"""
        url = reverse('published_project_list')

        # Make requests up to the limit
        for _ in range(20):
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Next request should be rate limited
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_authenticated_rate_limit(self):
        """Test rate limiting for authenticated users"""
        url = reverse('published_project_list')

        # Create and authenticate test user
        self.client.force_authenticate(user=self.project.authors.first())

        # Make requests up to the limit
        for _ in range(100):
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Next request should be rate limited
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_search_rate_limit(self):
        """Test rate limiting on search endpoint"""
        url = reverse('published_project_search')

        # Make requests up to the limit
        for _ in range(20):
            response = self.client.get(url, {'search_term': 'test'})
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Next request should be rate limited
        response = self.client.get(url, {'search_term': 'test'})
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_project_detail_rate_limit(self):
        """Test rate limiting on project detail endpoint"""
        url = reverse('published_project_detail',
                      kwargs={'project_slug': 'demopsn', 'version': '1.0'})

        # Make requests up to the limit
        for _ in range(20):
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Next request should be rate limited
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)


class TestAPIFieldSerialization(TestCase):
    """Test that new API fields are correctly serialized"""

    def setUp(self):
        """Set up test data"""
        from project.models import CoreProject, PublishedTopic, License
        from datetime import datetime
        from django.utils import timezone as tz

        self.client = APIClient()

        # Create core project
        self.core_project = CoreProject.objects.create()

        # Create license
        self.license, _ = License.objects.get_or_create(
            slug='test-license-slug',
            defaults={
                'name': 'Test License For API',
                'version': '1.0'
            }
        )

        # Create project types for testing
        self.db_type = ProjectType.objects.get_or_create(
            id=0,
            defaults={'name': 'Database', 'description': 'Test database type'}
        )[0]
        self.sw_type = ProjectType.objects.get_or_create(
            id=1,
            defaults={'name': 'Software', 'description': 'Test software type'}
        )[0]
        self.ch_type = ProjectType.objects.get_or_create(
            id=2,
            defaults={'name': 'Challenge', 'description': 'Test challenge type'}
        )[0]
        self.md_type = ProjectType.objects.get_or_create(
            id=3,
            defaults={'name': 'Model', 'description': 'Test model type'}
        )[0]

        # Create published project
        self.project = PublishedProject.objects.create(
            slug='test-api-project',
            version='1.0.0',
            title='Test API Project',
            abstract='Test abstract for API',
            short_description='Short desc',
            resource_type=self.db_type,
            access_policy=AccessPolicy.CREDENTIALED,
            core_project=self.core_project,
            license=self.license,
            publish_datetime=tz.make_aware(datetime(2024, 1, 1))
        )

        # Create and add topics
        self.topic1 = PublishedTopic.objects.create(
            description='critical care'
        )
        self.topic2 = PublishedTopic.objects.create(
            description='ehr'
        )
        self.project.topics.add(self.topic1, self.topic2)

    def test_published_project_list_includes_new_fields(self):
        """Test that list endpoint includes resource_type, access_policy, topics"""
        url = reverse('published_project_list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Find our test project in the results
        data = response.json()
        results = data.get('results', data) if isinstance(data, dict) else data
        test_project = next(
            (p for p in results if p['slug'] == 'test-api-project'),
            None
        )

        self.assertIsNotNone(test_project, "Test project not found in API response")

        # Verify new fields exist and have correct values
        self.assertEqual(test_project['resource_type'], 'Database')
        self.assertEqual(test_project['access_policy'], 'Credentialed')
        self.assertIn('critical care', test_project['topics'])
        self.assertIn('ehr', test_project['topics'])
        self.assertEqual(len(test_project['topics']), 2)
        self.assertIsNotNone(test_project.get('source_url'))

    def test_published_project_detail_includes_new_fields(self):
        """Test that detail endpoint includes resource_type, access_policy, topics"""
        url = reverse('published_project_detail',
                      kwargs={'project_slug': 'test-api-project',
                              'version': '1.0.0'})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        # Verify new fields exist and have correct values
        self.assertEqual(data['resource_type'], 'Database')
        self.assertEqual(data['access_policy'], 'Credentialed')
        self.assertIn('critical care', data['topics'])
        self.assertIn('ehr', data['topics'])
        self.assertEqual(len(data['topics']), 2)
        self.assertIsNotNone(data.get('source_url'))

    def test_access_policy_values(self):
        """Test all access policy values serialize correctly"""
        from datetime import datetime
        from django.utils import timezone as tz
        from project.models import CoreProject

        test_cases = [
            (AccessPolicy.OPEN, 'Open'),
            (AccessPolicy.RESTRICTED, 'Restricted'),
            (AccessPolicy.CREDENTIALED, 'Credentialed'),
            (AccessPolicy.CONTRIBUTOR_REVIEW, 'Contributor Review'),
        ]

        for policy_value, expected_name in test_cases:
            with self.subTest(policy=policy_value):
                # Create a new core project for each iteration to avoid uniqueness constraints
                # on (core_project, version) if version is kept constant
                core_project = CoreProject.objects.create(doi=None)

                project = PublishedProject.objects.create(
                    slug=f'test-policy-{policy_value}',
                    version='1.0.0',
                    title=f'Test Policy {policy_value}',
                    abstract='Test',
                    resource_type=self.db_type,
                    access_policy=policy_value,
                    core_project=core_project,
                    license=self.license,
                    publish_datetime=tz.make_aware(datetime(2024, 1, 1))
                )

                url = reverse('published_project_detail',
                              kwargs={'project_slug': project.slug,
                                      'version': project.version})
                response = self.client.get(url)

                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(response.json()['access_policy'], expected_name)

    def test_resource_type_values(self):
        """Test all resource type values serialize correctly"""
        from datetime import datetime
        from django.utils import timezone as tz
        from project.models import CoreProject

        type_data = [
            (self.db_type, 'Database'),
            (self.sw_type, 'Software'),
            (self.ch_type, 'Challenge'),
            (self.md_type, 'Model'),
        ]

        for project_type, type_name in type_data:
            with self.subTest(resource_type=type_name):
                # Create a new core project for each iteration
                core_project = CoreProject.objects.create(doi=None)

                project = PublishedProject.objects.create(
                    slug=f'test-type-{project_type.id}',
                    version='1.0.0',
                    title=f'Test Type {type_name}',
                    abstract='Test',
                    resource_type=project_type,
                    access_policy=AccessPolicy.OPEN,
                    core_project=core_project,
                    license=self.license,
                    publish_datetime=tz.make_aware(datetime(2024, 1, 1))
                )

                url = reverse('published_project_detail',
                              kwargs={'project_slug': project.slug,
                                      'version': project.version})
                response = self.client.get(url)

                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(response.json()['resource_type'], type_name)

    def test_project_without_topics(self):
        """Test that projects without topics return empty list"""
        from datetime import datetime
        from django.utils import timezone as tz
        from project.models import CoreProject

        core_project = CoreProject.objects.create(doi=None)

        project = PublishedProject.objects.create(
            slug='test-no-topics',
            version='1.0.0',
            title='Test No Topics',
            abstract='Test',
            resource_type=self.db_type,
            access_policy=AccessPolicy.OPEN,
            core_project=core_project,
            license=self.license,
            publish_datetime=tz.make_aware(datetime(2024, 1, 1))
        )

        url = reverse('published_project_detail',
                      kwargs={'project_slug': project.slug,
                              'version': project.version})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['topics'], [])

    def test_backward_compatibility(self):
        """Test that all existing fields are still present"""
        url = reverse('published_project_detail',
                      kwargs={'project_slug': 'test-api-project',
                              'version': '1.0.0'})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        # Verify all existing fields are still present
        expected_existing_fields = [
            'slug', 'title', 'version', 'abstract', 'license',
            'short_description', 'project_home_page', 'publish_datetime',
            'doi', 'main_storage_size', 'compressed_storage_size'
        ]

        for field in expected_existing_fields:
            self.assertIn(field, data, f"Field '{field}' missing from response")


class TestOAuthTokenAuthentication(TestCase):
    """Test that the metadata API accepts OAuth bearer tokens"""

    def setUp(self):
        """Set up an OAuth application, a token, and a clean throttle cache"""
        cache.clear()
        self.client = APIClient()

        self.user = User.objects.create_user(
            username='api_token_user',
            email='api_token_user@example.org',
            password='Tester11!',
        )
        self.application = Application.objects.create(
            name='Metadata API Test Application',
            redirect_uris='https://example.org/callback',
            user=self.user,
            client_type=Application.CLIENT_CONFIDENTIAL,
            authorization_grant_type=Application.GRANT_AUTHORIZATION_CODE,
        )
        self.access_token = AccessToken.objects.create(
            user=self.user,
            scope='profile:read',
            expires=timezone.now() + timedelta(seconds=300),
            token='metadata-api-test-token',
            application=self.application,
        )
        self.auth_header = {'HTTP_AUTHORIZATION': 'Bearer {}'.format(self.access_token.token)}
        self.url = reverse('published_project_detail',
                           kwargs={'project_slug': 'demopsn', 'version': '1.0'})

    def tearDown(self):
        cache.clear()

    def test_bearer_token_is_authenticated(self):
        """A bearer token identifies the caller instead of being ignored"""
        response = self.client.get(self.url, **self.auth_header)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.wsgi_request.user, self.user)

    def test_bearer_token_is_not_anonymously_throttled(self):
        """A bearer token gets the authenticated rate, not the 20/hour anonymous one"""
        for _ in range(21):
            response = self.client.get(self.url, **self.auth_header)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_anonymous_requests_are_still_throttled(self):
        """Anonymous behaviour is unchanged by accepting tokens"""
        for _ in range(20):
            self.assertEqual(self.client.get(self.url).status_code, status.HTTP_200_OK)

        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_429_TOO_MANY_REQUESTS)
