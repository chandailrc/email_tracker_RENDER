from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from datetime import datetime, time, timedelta
from django.db.models import Count, Q, Case, When, IntegerField
from tracking.models import EmailInteraction
from sending.models import SentEmail
from unsubscribers.models import UnsubscribedUser
from django.contrib.auth import get_user_model
from contacts.models import Contact, ContactList
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth

import logging

logger = logging.getLogger(__name__)

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
        time_period = data.get('time_period', '24hrs')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        team_id = data.get('team_id')
        user_id = data.get('user_id')
        lead_source = data.get('lead_source')
        recipient_domain = data.get('recipient_domain')
        subject_contains = data.get('subject_contains')
        contactList_Id = data.get('contactListId', 1)
        segmentation = data.get('segmentation', None)  # 'daily', 'weekly', 'monthly', or None

        print(request.data)

        # Base queryset
        sent_emails = SentEmail.objects.filter(user=request.user)
        print(sent_emails.count())

        # Apply time period filter
        end_date = timezone.now()
        if time_period == '24hrs':
            start_date = end_date - timedelta(days=1)
        elif time_period == '7days':
            start_date = end_date - timedelta(weeks=1)
        elif time_period == '1month':
            start_date = end_date - timedelta(days=30)  # Approximate month
        elif time_period == 'custom':
            if start_date and end_date:
                if isinstance(start_date, str):
                    start_date = datetime.strptime(start_date, '%Y-%m-%d')
                if isinstance(end_date, str):
                    end_date = datetime.strptime(end_date, '%Y-%m-%d')
                
                if start_date and start_date.tzinfo is None:
                    start_date = timezone.make_aware(start_date)
                if end_date and end_date.tzinfo is None:
                    end_date = timezone.make_aware(end_date)
                
                end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
            else:
                start_date = end_date - timedelta(days=30)
        else:
            start_date = end_date - timedelta(days=30)

        # Ensure start_date is at the beginning of the day and timezone-aware
        start_date = timezone.make_aware(datetime.combine(start_date.date(), time.min))

        # print(start_date)
        # print(end_date)

        # Apply date range filter
        sent_emails = sent_emails.filter(sent_at__gte=start_date, sent_at__lte=end_date)
        # print(sent_emails.count())
        
        
        # Apply other filters
        if campaign_id:
            sent_emails = sent_emails.filter(campaign_id=campaign_id)
        if recipient_domain:
            sent_emails = sent_emails.filter(recipient__iendswith=f'@{recipient_domain}')
        if subject_contains:
            sent_emails = sent_emails.filter(subject__icontains=subject_contains)

        contacts = ContactList.objects.filter(user=request.user, id=contactList_Id)
        prospect_quality = self.calculate_prospect_quality(contacts)
        
        # for email in sent_emails:
        #     print(email.recipient)
        #     print(email.subject)
        #     print(email.sent_at)
            
        # print(sent_emails.count())

        if segmentation:
            if segmentation == 'daily':
                trunc_func = TruncDate('sent_at')
            elif segmentation == 'weekly':
                trunc_func = TruncWeek('sent_at')
            elif segmentation == 'monthly':
                trunc_func = TruncMonth('sent_at')
            else:
                return Response({"error": "Invalid segmentation parameter"}, status=400)

            # First, get the basic email metrics
            base_metrics = sent_emails.annotate(
                period=trunc_func
            ).values('period').annotate(
                total_intended=Count('id'),
                total_sent=Count('id', filter=Q(is_bounced=False)),
                total_bounced=Count('id', filter=Q(is_bounced=True))
            ).order_by('period')

            # Now, let's add the interaction-related metrics
            for metric in base_metrics:
                period_start = metric['period']
                period_end = period_start + timedelta(days=1) if segmentation == 'daily' else (
                    period_start + timedelta(weeks=1) if segmentation == 'weekly' else (
                        (period_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                    )
                )

                period_emails = sent_emails.filter(sent_at__gte=period_start, sent_at__lt=period_end)

                metric['total_opens'] = EmailInteraction.objects.filter(
                    email__in=period_emails, 
                    interaction_type='OPEN'
                ).count()
                
                metric['unique_opens'] = EmailInteraction.objects.filter(
                    email__in=period_emails, 
                    interaction_type='OPEN'
                ).values('email').distinct().count()

                metric['total_clicks'] = EmailInteraction.objects.filter(
                    email__in=period_emails, 
                    interaction_type='CLICK'
                ).count()

                metric['unique_clicks'] = EmailInteraction.objects.filter(
                    email__in=period_emails, 
                    interaction_type='CLICK'
                ).values('email').distinct().count()

                metric['total_unsubscribes'] = UnsubscribedUser.objects.filter(
                    email__in=period_emails.values_list('recipient', flat=True)
                ).count()

                metric['unique_links_clicked'] = EmailInteraction.objects.filter(
                    email__in=period_emails, 
                    interaction_type='CLICK'
                ).values('email', 'tracking_item__url').distinct().count()

                # Calculate percentages and rates
                metric['contacted_percentage'] = (metric['total_sent'] / metric['total_intended'] * 100) if metric['total_intended'] > 0 else 0
                metric['read_percentage'] = (metric['unique_opens'] / metric['total_sent'] * 100) if metric['total_sent'] > 0 else 0
                metric['bounce_rate'] = (metric['total_bounced'] / metric['total_intended'] * 100) if metric['total_intended'] > 0 else 0
                metric['click_rate'] = (metric['unique_clicks'] / metric['total_sent'] * 100) if metric['total_sent'] > 0 else 0
                metric['unsubscribe_rate'] = (metric['total_unsubscribes'] / metric['total_sent'] * 100) if metric['total_sent'] > 0 else 0
                metric['avg_clicks_per_email'] = metric['total_clicks'] / metric['total_sent'] if metric['total_sent']> 0 else 0
                metric['avg_unique_links_per_email']= metric['unique_links_clicked'] / metric['total_sent'] if metric['total_sent'] > 0 else 0
                metric['prospect_quality'] = prospect_quality
                
                '''click_rate : The click rate typically represents the percentage of emails that received at least one click on any 
                                link within the email. It's not about the total number of clicks or the number of unique links clicked 
                                within each email.
                '''

            # Calculate overall totals
            overall_totals = {
                'total_intended': sum(m['total_intended'] for m in base_metrics),
                'total_sent': sum(m['total_sent'] for m in base_metrics),
                'total_bounced': sum(m['total_bounced'] for m in base_metrics),
                'total_opens': sum(m['total_opens'] for m in base_metrics),
                'total_unique_opens': sum(m['unique_opens'] for m in base_metrics),
                'total_clicks': sum(m['total_clicks'] for m in base_metrics),
                'total_unique_clicks': sum(m['unique_clicks'] for m in base_metrics),
                'total_unique_links_clicked': sum(m['unique_links_clicked'] for m in base_metrics),
                'avg_clicks_per_email': sum(m['avg_clicks_per_email'] for m in base_metrics),
                'total_unsubscribes': sum(m['total_unsubscribes'] for m in base_metrics),
                'avg_unique_links_per_email': sum(m['avg_unique_links_per_email'] for m in base_metrics)
            }

            # Calculate overall percentages and rates
            overall_totals['contacted_percentage'] = (overall_totals['total_sent'] / overall_totals['total_intended'] * 100) if overall_totals['total_intended'] > 0 else 0
            overall_totals['read_percentage'] = (overall_totals['total_unique_opens'] / overall_totals['total_sent'] * 100) if overall_totals['total_sent'] > 0 else 0
            overall_totals['bounce_rate'] = (overall_totals['total_bounced'] / overall_totals['total_intended'] * 100) if overall_totals['total_intended'] > 0 else 0
            overall_totals['click_rate'] = (overall_totals['total_unique_clicks'] / overall_totals['total_sent'] * 100) if overall_totals['total_sent'] > 0 else 0
            overall_totals['avg_clicks_per_email'] = (overall_totals['total_clicks'] / overall_totals['total_sent']) if overall_totals['total_sent'] > 0 else 0
            overall_totals['avg_unique_links_per_email'] = (overall_totals['total_unique_links_clicked'] / overall_totals['total_sent']) if overall_totals['total_sent'] > 0 else 0
            overall_totals['unsubscribe_rate'] = (overall_totals['total_unsubscribes'] / overall_totals['total_sent'] * 100) if overall_totals['total_sent'] > 0 else 0
            overall_totals['prospect_quality'] = prospect_quality

            metrics_list = list(base_metrics)
            metrics_list.append({'period': 'Total', **overall_totals})
            
            print(f"Segmentation: {segmentation}")
            for metric in metrics_list:
                print(metric)
            print('\n')
            print(len(metrics_list))

            return Response(metrics_list)
        else:
            # Calculate non-segmented metrics (your existing logic)
            total_intended = sent_emails.count()
            total_sent = sent_emails.filter(is_bounced=False).count()
            total_bounced = sent_emails.filter(is_bounced=True).count()
            total_unsubscribes = UnsubscribedUser.objects.filter(email__in=sent_emails.values_list('recipient', flat=True)).count()
            
            total_opens = EmailInteraction.objects.filter(
                email__in=sent_emails, 
                interaction_type='OPEN'
            ).count()
            
            unique_opens = EmailInteraction.objects.filter(
                email__in=sent_emails, 
                interaction_type='OPEN'
            ).values('email').distinct().count()
            
            unique_clicks = EmailInteraction.objects.filter(
                email__in=sent_emails, 
                interaction_type='CLICK'
            ).values('email').distinct().count()
            
            total_clicks = EmailInteraction.objects.filter(
                email__in=sent_emails, 
                interaction_type='CLICK'
            ).count()
            
            unique_links_clicked = EmailInteraction.objects.filter(
                email__in=sent_emails,
                interaction_type='CLICK',
                tracking_item__item_type='LINK'
            ).values('email', 'tracking_item__url').distinct().count()
            
            contacted_percentage = (total_sent / total_intended) * 100 if total_intended > 0 else 0
            read_percentage = (unique_opens / total_sent) * 100 if total_sent > 0 else 0
            bounce_rate = (total_bounced / total_intended) * 100 if total_intended > 0 else 0
            click_rate = (unique_clicks / total_sent) * 100 if total_sent > 0 else 0
            unsubscribe_rate = (total_unsubscribes / total_sent) * 100 if total_sent > 0 else 0
            avg_clicks_per_email = total_clicks / total_sent if total_sent > 0 else 0
            avg_unique_links_per_email = unique_links_clicked / total_sent if total_sent > 0 else 0
            
            metrics = {
                'total_intended': total_intended,
                'total_sent': total_sent,
                'total_bounced': total_bounced,
                'total_opens': total_opens,
                'unique_opens': unique_opens,
                'total_clicks': total_clicks,
                'unique_clicks': unique_clicks,
                'unique_links_clicked': unique_links_clicked,
                'total_unsubscribes': total_unsubscribes,
                'contacted_percentage': contacted_percentage,
                'read_percentage': read_percentage,
                'bounce_rate': bounce_rate,
                'click_rate': click_rate,
                'unsubscribe_rate': unsubscribe_rate,
                'prospect_quality': prospect_quality,
                'avg_clicks_per_email': avg_clicks_per_email,
                'avg_unique_links_per_email': avg_unique_links_per_email,
            }
            
            print("Segmentation: None")
            print(metrics)

            return Response(metrics)
    
from django.shortcuts import render
    
def analytics_form_view(request):
    return render(request, 'analytics_request.html')