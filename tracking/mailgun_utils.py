#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jul 13 14:23:48 2024

@author: rahul
"""

# mailgun_utils.py
import requests
from django.conf import settings

def send_email(subject, message, from_email, recipient_list, html_text):
    # Join the recipient_list into a single string separated by commas
    # recipient_list = ', '.join(recipient_list)
    return requests.post(
        f"https://api.mailgun.net/v3/{settings.MAILGUN_DOMAIN}/messages",
        auth=("api", settings.MAILGUN_API_KEY),
        data={
            "from": from_email,
            "to": recipient_list,
            "subject": subject,
            "text": message,
            "html": html_text,
            "o:tracking-opens": "yes"
        }
    )

def send_simple_message(subject, message, from_email, recipient_list):
	return requests.post(
		"https://api.mailgun.net/v3/razor-arts.com/messages",
		auth=("api", settings.MAILGUN_API_KEY),
		data={"from": from_email,
			"to": recipient_list,
			"subject": subject,
			"template": "Test Template",
			"h:X-Mailgun-Variables": "{'test': 'test'}"})