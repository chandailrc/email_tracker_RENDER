from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from datetime import datetime, time, timedelta
from django.db.models import Count, Avg, Q
from tracking.models import EmailInteraction
from sending.models import SentEmail
from unsubscribers.models import UnsubscribedUser
from django.contrib.auth import get_user_model
from contacts.models import Contact, ContactList

User = get_user_model()

class AnalyticsViewSet(viewsets.ViewSet):
    
    def calculate_prospect_quality(self, contact_lists):
        contacts = Contact.objects.filter(contact_list__in=contact_lists)
        total_contacts = contacts.count()
        high_quality_contacts = contacts.filter(icp_score__gte=4).count()  # Assuming 4+ is high quality
    
        if total_contacts > 0:
            return (high_quality_contacts / total_contacts) * 100
        return 0
    
    @action(detail=False, methods=['post'])
    def metrics(self, request):
        # Get filter parameters from POST data
        data = request.data
        campaign_id = data.get('campaign_id', 'default_campaign')
        time_period = data.get('time_period', 'custom')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        team_id = data.get('team_id')
        user_id = data.get('user_id')
        lead_source = data.get('lead_source')
        recipient_domain = data.get('recipient_domain')
        subject_contains = data.get('subject_contains')
        contactList_Id = data.get('contactListId', 1)

        print(request.data)
        # Base queryset
        sent_emails = SentEmail.objects.filter(user=request.user)
        print(sent_emails.count())

        # Apply time period filter
        end_date = timezone.now()
        if time_period == 'daily':
            start_date = end_date - timedelta(days=1)
        elif time_period == 'weekly':
            start_date = end_date - timedelta(weeks=1)
        elif time_period == 'monthly':
            start_date = end_date - timedelta(days=30)  # Approximate month
        elif time_period == 'custom':
            if start_date and end_date:
                # Convert string dates to timezone-aware datetime objects
                start_date = timezone.make_aware(datetime.strptime(start_date, '%Y-%m-%d'))
                end_date = timezone.make_aware(datetime.strptime(end_date, '%Y-%m-%d'))
                # Set end_date to the end of the day
                end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
            else:
                # If custom range is not properly specified, default to last 30 days
                start_date = end_date - timedelta(days=30)
        else:
            # Default to last 30 days if an invalid time_period is provided
            start_date = end_date - timedelta(days=30)

        # Ensure start_date is at the beginning of the day and timezone-aware
        start_date = timezone.make_aware(datetime.combine(start_date.date(), time.min))
        
        print(start_date)
        print(end_date)

        # Apply date range filter
        # sent_emails = sent_emails.filter(sent_at__gte=start_date, sent_at__lte=end_date)

        

        # Apply other filters
        if campaign_id:
            sent_emails = sent_emails.filter(campaign_id=campaign_id)
        # if team_id:
        #     sent_emails = sent_emails.filter(user__team_id=team_id)
        # if user_id:
        #     sent_emails = sent_emails.filter(user_id=user_id)
        # if lead_source:
        #     sent_emails = sent_emails.filter(lead_source=lead_source)
        if recipient_domain:
            sent_emails = sent_emails.filter(recipient__iendswith=f'@{recipient_domain}')
            print(sent_emails.count())

        if subject_contains:
            sent_emails = sent_emails.filter(subject__icontains=subject_contains)
            print(sent_emails.count())


        # Calculate metrics
        total_intended = sent_emails.count()
        total_sent = sent_emails.filter(is_bounced=False).count()
        total_bounced = sent_emails.filter(is_bounced=True).count()
        total_opens = EmailInteraction.objects.filter(email__in=sent_emails, interaction_type='OPEN').count()
        total_clicks = EmailInteraction.objects.filter(email__in=sent_emails, interaction_type='CLICK').count()
        total_unsubscribes = UnsubscribedUser.objects.filter(email__in=sent_emails.values_list('recipient', flat=True)).count()
        
        contacts = ContactList.objects.filter(user=request.user, id=contactList_Id) 
        prospect_quality = self.calculate_prospect_quality(contacts)

        contacted_percentage = (total_sent / total_intended) * 100 if total_intended > 0 else 0
        read_percentage = (total_opens / total_sent) * 100 if total_sent > 0 else 0
        bounce_rate = (total_bounced / total_intended) * 100 if total_intended > 0 else 0
        click_rate = (total_clicks / total_sent) * 100 if total_sent > 0 else 0
        unsubscribe_rate = (total_unsubscribes / total_sent) * 100 if total_sent > 0 else 0

        return Response({
            'total_intended': total_intended,
            'total_sent': total_sent,
            'total_bounced': total_bounced,
            'total_opens': total_opens,
            'total_clicks': total_clicks,
            'total_unsubscribes': total_unsubscribes,
            'contacted_percentage': contacted_percentage,
            'read_percentage': read_percentage,
            'bounce_rate': bounce_rate,
            'click_rate': click_rate,
            'unsubscribe_rate': unsubscribe_rate,
            'prospect_quality': prospect_quality,
        })
    
from django.shortcuts import render
    
def analytics_form_view(request):
    return render(request, 'analytics_request.html')