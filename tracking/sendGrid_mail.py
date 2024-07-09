#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul  1 11:28:50 2024

@author: rahul
"""

from django.core.mail import send_mail

def sendGridmail():
    send_mail(
        'Subject here',
        'Here is the message.',
        '1chandailrc1@example.com',  # This should be your verified sender email
        ['chandailrc@hotmail.com'],
        fail_silently=False,
    )