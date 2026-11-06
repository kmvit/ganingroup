from django.urls import path

from . import views

urlpatterns = [
    path('consent/', views.consent_text, name='assistant_consent'),
    path('chat/', views.chat, name='assistant_chat'),
    path('lead/', views.lead, name='assistant_lead'),
]
