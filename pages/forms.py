# -*- coding: utf-8 -*-
import re

from django import forms

from .models import Lead, HaulerLead, VacancyApplication

PHONE_RE = re.compile(r'^[\d\s\-\+\(\)]{10,25}$')


def _clean_phone(value: str) -> str:
    value = (value or '').strip()
    if not PHONE_RE.match(value):
        raise forms.ValidationError('Укажите телефон — например +7 928 000-00-00.')
    if len(re.sub(r'\D', '', value)) < 10:
        raise forms.ValidationError('В номере слишком мало цифр.')
    return value


class LeadForm(forms.ModelForm):
    """Форма «Запросить ТКП». Согласие на обработку ПДн — обязательное поле."""

    agree = forms.BooleanField(
        label='Согласие на обработку персональных данных',
        error_messages={'required': 'Без согласия на обработку ПДн отправить заявку нельзя.'},
    )

    class Meta:
        model = Lead
        fields = ['name', 'phone', 'company', 'details']

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        if len(name) < 2:
            raise forms.ValidationError('Как к вам обращаться?')
        return name

    def clean_phone(self):
        return _clean_phone(self.cleaned_data.get('phone'))


class HaulerLeadForm(forms.ModelForm):
    """Форма перевозчика на странице «Карьера»."""

    agree = forms.BooleanField(
        label='Согласие на обработку персональных данных',
        error_messages={'required': 'Без согласия на обработку ПДн отправить заявку нельзя.'},
    )

    class Meta:
        model = HaulerLead
        fields = ['name', 'phone', 'vehicles']

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        if len(name) < 2:
            raise forms.ValidationError('Как к вам обращаться?')
        return name

    def clean_phone(self):
        return _clean_phone(self.cleaned_data.get('phone'))


RESUME_EXT = ('.pdf', '.doc', '.docx', '.rtf', '.odt')
RESUME_MAX_MB = 10


class VacancyApplicationForm(forms.ModelForm):
    """Отклик на вакансию. Резюме — pdf/doc до 10 МБ."""

    agree = forms.BooleanField(
        label='Согласие на обработку персональных данных',
        error_messages={'required': 'Без согласия на обработку ПДн отправить отклик нельзя.'},
    )

    class Meta:
        model = VacancyApplication
        fields = ['name', 'phone', 'vacancy', 'vacancy_title', 'resume', 'comment']

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        if len(name) < 2:
            raise forms.ValidationError('Как к вам обращаться?')
        return name

    def clean_phone(self):
        return _clean_phone(self.cleaned_data.get('phone'))

    def clean_resume(self):
        f = self.cleaned_data.get('resume')
        if not f:
            return f
        name = (f.name or '').lower()
        if not name.endswith(RESUME_EXT):
            raise forms.ValidationError(
                'Резюме принимаем в PDF, DOC, DOCX, RTF или ODT.')
        if f.size > RESUME_MAX_MB * 1024 * 1024:
            raise forms.ValidationError(
                f'Файл больше {RESUME_MAX_MB} МБ — пришлите версию полегче.')
        return f
