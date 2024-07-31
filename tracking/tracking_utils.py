from .models import EmailInteraction, GenuineOpen
from django.utils import timezone

def aggregate_genuine_opens(emails):
    for email in emails:
        # Delete existing GenuineOpen objects for this email
        GenuineOpen.objects.filter(email=email).delete()
        
        # Get all open and click/form_submission events for this email, ordered by timestamp
        all_events = EmailInteraction.objects.filter(
            email=email
        ).order_by('timestamp')
        
        open_events = all_events.filter(interaction_type='open')
        action_events = all_events.filter(interaction_type__in=['click', 'form_submission'])
        
        i, j = 0, 0  # Indices for open_events and action_events
        while i < len(open_events) and j < len(action_events):
            current_open = open_events[i]
            current_action = action_events[j]
            
            if current_action.timestamp <= current_open.timestamp:
                j += 1
                continue
            
            # Find the latest open event that precedes the current action
            while i < len(open_events) - 1 and open_events[i+1].timestamp < current_action.timestamp:
                i += 1
            
            current_open = open_events[i]
            
            # Check if the action is within 10 minutes of the open
            if (current_action.timestamp - current_open.timestamp) <= timezone.timedelta(minutes=10):
                # Find the latest action that's still within 10 minutes of the open
                while (j < len(action_events) - 1 and 
                       action_events[j+1].timestamp - current_open.timestamp <= timezone.timedelta(minutes=10)):
                    j += 1
                
                # Create a GenuineOpen object
                GenuineOpen.objects.create(email=email, open_event=current_open)
                
                # Move to the next open event
                i += 1
            else:
                # If the action is more than 10 minutes after the open, move to the next open
                i += 1


