# -*- coding: utf-8 -*-
from django.urls import path

from . import views

urlpatterns = [
    path(p, views.make_page_view(tpl, active, name), name=name)
    for p, name, tpl, active in views.PAGES
] + [
    path('sitemap.xml', views.sitemap_xml, name='sitemap'),
    path('robots.txt', views.robots_txt, name='robots'),
    path('zayavka/tkp/', views.lead_create, name='lead_create'),
    path('zayavka/perevozchik/', views.hauler_create, name='hauler_create'),
    path('zayavka/vakansiya/', views.application_create, name='application_create'),
]
