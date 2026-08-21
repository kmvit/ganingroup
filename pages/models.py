# -*- coding: utf-8 -*-
"""Модели переехали в отдельные приложения по смыслу.

Здесь оставлены только импорты — чтобы существующие ссылки вида
`pages.models.Lead` продолжали работать.

  core    — общие данные сайта, меню, страницы, плитки
  content — цифры, направления, объекты, люди, вакансии, документы
  calc    — марки бетона с ценами и зоны доставки
  leads   — заявки с сайта
"""
from calc.models import ConcreteGrade, DeliveryZone                       # noqa: F401
from content.models import (Department, Direction, Document, MapPoint,    # noqa: F401
                            ProjectObject, Review, Stat, TeamMember,
                            TimelineEvent, Vacancy)
from core.models import Card, MenuItem, Ordered, Page, SiteSettings       # noqa: F401
from leads.models import HaulerLead, Lead, VacancyApplication             # noqa: F401
