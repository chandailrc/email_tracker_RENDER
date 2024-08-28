from django.test import TestCase
from rest_framework.test import APIClient
from django.urls import reverse
from django.utils import timezone
from datetime import datetime, timedelta
from django.contrib.auth import get_user_model


from sending.models import SentEmail
from tracking.models import EmailInteraction
from contacts.models import ContactList, Contact
from unsubscribers.models import UnsubscribedUser

User = get_user_model()

class AnalyticsViewSetTestCase(TestCase):

    def setUp(self):
        # Set up initial data
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        # Create some contacts and contact lists
        self.contact_list = ContactList.objects.create(user=self.user, name="Test Contact List")
        self.contact = Contact.objects.create(contact_list=self.contact_list, email="test@example.com", icp_score=5)

        # Create some sent emails
        self.sent_email = SentEmail.objects.create(
            user=self.user,
            recipient="test@example.com",
            subject="Test Email",
            sent_at=timezone.now() - timedelta(days=1),
            is_bounced=False,
            campaign_id=1,
            # lead_source="LinkedIn"
        )

        # Create email interactions
        EmailInteraction.objects.create(email=self.sent_email, interaction_type='OPEN')
        EmailInteraction.objects.create(email=self.sent_email, interaction_type='CLICK')

        # Create unsubscribed user
        UnsubscribedUser.objects.create(email="test@example.com", unsubscribed_from=self.user)

    def test_metrics_view(self):
        # Prepare the data for the POST request
        data = {
            "campaign_id": 1,
            "time_period": "custom",
            "start_date": (timezone.now() - timedelta(days=2)).strftime('%Y-%m-%d'),
            "end_date": timezone.now().strftime('%Y-%m-%d'),
            "team_id": None,
            "user_id": self.user.id,
            "lead_source": "LinkedIn",
            "recipient_domain": "example.com",
            "subject_contains": "Test",
            "contactListId": self.contact_list.id,
        }

        # Make the POST request to the metrics view
        url = reverse('analytics-metrics')
        response = self.client.post(url, data, format='json')

        # Check that the response status is 200 OK
        self.assertEqual(response.status_code, 200)

        # Check the response data
        self.assertEqual(response.data['total_intended'], 1)
        self.assertEqual(response.data['total_sent'], 1)
        self.assertEqual(response.data['total_bounced'], 0)
        self.assertEqual(response.data['total_opens'], 1)
        self.assertEqual(response.data['total_clicks'], 1)
        self.assertEqual(response.data['total_unsubscribes'], 1)
        self.assertAlmostEqual(response.data['prospect_quality'], 100.0)  # 100% high quality

