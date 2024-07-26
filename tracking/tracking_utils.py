from .models import EmailInteraction, GenuineOpen
from datetime import timedelta

def determine_genuine_open(open_event):
    interactions = EmailInteraction.objects.filter(email=open_event.email)
    open_time = open_event.timestamp
    
    # Define time windows
    extended_window = timedelta(minutes=10)
    
    # Check for related interactions within the extended window
    related_clicks = interactions.filter(
        interaction_type='click', 
        timestamp__gte=open_time, 
        timestamp__lte=open_time + extended_window
    )
    related_forms = interactions.filter(
        interaction_type='form_submission', 
        timestamp__gte=open_time, 
        timestamp__lte=open_time + extended_window
    )
    
    # Logic to determine a genuine open
    return related_clicks.exists() or related_forms.exists()

def aggregate_genuine_opens(emails):
    for email in emails:
        interactions = EmailInteraction.objects.filter(email=email)
        open_events = interactions.filter(interaction_type='open')
        
        for open_event in open_events:
            if determine_genuine_open(open_event):
                GenuineOpen.objects.create(email=email)
