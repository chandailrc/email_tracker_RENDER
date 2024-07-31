# -*- coding: utf-8 -*-

from django.urls import path
from . import views

urlpatterns = [
    path('compose/', views.compose_email_view, name='compose_email'),
    path('send-tracked-email/', views.send_tracked_email_view, name='send_tracked_email_view'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('email/<int:email_id>/', views.email_detail, name='email_detail'),
    path('unsubscribe/', views.unsubscribe, name='unsubscribe'),
    path('unsubscribed-users/', views.unsubscribed_users_list, name='unsubscribed_users_list'),
    path('delete-unsubscribed-user/<str:user_email>/', views.delete_unsubscribed_user, name='delete_unsubscribed_user'),
    path('email-management/', views.email_management, name='email_management'),
    path('fetch-emails/', views.fetch_emails, name='fetch_emails'),
    path('conversations/', views.conversation_list, name='conversation_list'),
    path('conversations/<int:conversation_id>/', views.conversation_detail, name='conversation_detail'),
    path('register/', views.register_page, name='register_page'),
    path('login/', views.login_page, name='login_page'),
    path('profile/', views.profile_page, name='profile_page'),
    path('update-profile/', views.update_profile_page, name='update_profile_page'),
    path('handle-register/', views.handle_register, name='handle_register'),
    path('handle-login/', views.handle_login, name='handle_login'),
    path('handle-logout/', views.handle_logout, name='handle_logout'),
    path('handle-update-profile/', views.handle_update_profile, name='handle_update_profile'),
    path('contact-lists/', views.contact_lists_page, name='contact_lists_page'),
    path('contact-lists/create/', views.create_contact_list_page, name='create_contact_list_page'),
    path('contact-lists/<int:list_id>/contacts/', views.contacts_in_list_page, name='contacts_in_list_page'),
    path('contact-lists/<int:list_id>/contacts/create/', views.create_contact_page, name='create_contact_page'),
    path('contacts/<int:contact_id>/update/', views.update_contact_page, name='update_contact_page'),
    path('contacts/<int:contact_id>/delete/', views.delete_contact, name='delete_contact'),
]