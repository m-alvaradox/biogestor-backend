"""Test helpers shared by the API test suites."""

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase


class AuthenticatedAPITestCase(APITestCase):
    """API test case whose client is already logged in.

    Endpoints are protected by default (S2-07); suites that test business rules
    rather than authentication start from an authenticated client.
    """

    def setUp(self):
        super().setUp()
        self.account = get_user_model().objects.create_user(username="api-tester")
        self.client.force_authenticate(user=self.account)
