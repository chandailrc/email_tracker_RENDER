from django.urls import path
from . import views

urlpatterns = [
    path('lists/create/', views.create_contact_list, name='create_contact_list'),
    path('lists/', views.get_contact_lists, name='get_contact_lists'),
    path('lists/<int:list_id>/contacts/create/', views.create_contact, name='create_contact'),
    path('lists/<int:list_id>/contacts/', views.get_contacts, name='get_contacts'),
    path('contacts/<int:contact_id>/update/', views.update_contact, name='update_contact'),
    path('contacts/<int:contact_id>/delete/', views.delete_contact, name='delete_contact'),
]