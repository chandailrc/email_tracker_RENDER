from .models import EmailInteraction, GenuineOpen

def aggregate_genuine_opens(emails):
    # print(f'email list len: {len(emails)}')
    for email in emails:
        # print(f'\n\n\n>>>>>>>>>>Processing email: {email}')
        
        # Delete existing GenuineOpen objects for this email
        GenuineOpen.objects.filter(email=email).delete()
        
        # Get all open and action events for this email, ordered by timestamp
        all_events = EmailInteraction.objects.filter(
            email=email
        ).order_by('timestamp')
        
        genuine_opens = 0
        last_open_event = None
        
        for event in all_events:
            if event.interaction_type == 'open':
                last_open_event = event
            elif event.interaction_type in ['click', 'form_submission']:
                if last_open_event:
                    # We found a genuine open
                    genuine_opens += 1
                    # print(f'Genuine open found: Open event at {last_open_event.timestamp}, Action event at {event.timestamp}')
                    GenuineOpen.objects.create(email=email, open_event=last_open_event)
                    last_open_event = None  # Reset last_open_event
        
        # print(f'Finished processing email: {email}. Found {genuine_opens} genuine opens.')