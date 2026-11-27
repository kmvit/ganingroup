from decimal import Decimal
from uuid import uuid4

from django import forms
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from calc.models import ConcreteGrade, ConstructionType
from leads.models import Lead
from .notify import notify_lead


class DeliveryForm(forms.Form):
    grade = forms.ChoiceField(label='Марка бетона')
    volume = forms.DecimalField(label='Объём, м³', required=False, min_value=Decimal('0.01'), max_digits=10, decimal_places=2,
                                widget=forms.NumberInput(attrs={'step': '0.01', 'inputmode': 'decimal'}))
    needs_volume_help = forms.BooleanField(label='Нужна помощь с объёмом', required=False)
    address = forms.CharField(label='Населённый пункт или адрес объекта', max_length=250)
    pump = forms.ChoiceField(label='Бетононасос', choices=[('', 'Выберите вариант')] + [
        (item, item) for item in ('Нужен', 'Не нужен', 'Нужна консультация')])
    phone = forms.CharField(label='Телефон', max_length=25,
                            widget=forms.TextInput(attrs={'type': 'tel', 'autocomplete': 'tel'}))
    date = forms.DateField(label='Дата заливки (если известна)', required=False,
                           widget=forms.DateInput(attrs={'type': 'date'}))
    agree = forms.BooleanField()
    calculation = forms.CharField(required=False, max_length=600, widget=forms.HiddenInput)
    submission_id = forms.UUIDField(widget=forms.HiddenInput)
    origin = forms.ChoiceField(widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        titles = ConcreteGrade.objects.filter(published=True).values_list('title', flat=True)
        self.fields['grade'].choices = [(v, v) for v in dict.fromkeys(['Нужна помощь', *titles])]
        self.fields['origin'].choices = [(reverse(n), n) for n in ('home', 'kalkulyator', 'reshenie_chastnaya_zastroyka')]
        for field in self.visible_fields():
            if field.name not in ('agree', 'needs_volume_help'):
                field.field.widget.attrs['class'] = 'f-input'

    def clean(self):
        data = super().clean()
        if data.get('needs_volume_help'):
            data['volume'] = None
            data['calculation'] = ''
        elif 'volume' in data and data['volume'] is None:
            self.add_error('volume', 'Введите объём больше нуля или выберите помощь с расчётом.')
        return data

    def clean_phone(self):
        value = self.cleaned_data['phone']
        if sum(c.isdigit() for c in value) < 10 or any(c not in '+()- 0123456789' for c in value):
            raise forms.ValidationError('Проверьте номер телефона.')
        return value


@never_cache
@require_http_methods(['GET', 'POST'])
def delivery_quote(request):
    initial = {'submission_id': uuid4(), 'origin': request.GET.get('origin', '/'),
               'calculation': request.GET.get('calculation', '')[:600],
               'grade': request.GET.get('grade'), 'volume': request.GET.get('volume')}
    form = DeliveryForm(request.POST if request.method == 'POST' else None, initial=initial)
    wants_json = request.headers.get('Accept') == 'application/json'
    if request.method == 'POST' and form.is_valid():
        data = form.cleaned_data
        date = data['date'].strftime('%d.%m.%Y') if data['date'] else 'уточнить'
        volume = 'Требуется расчёт' if data['needs_volume_help'] else f"{data['volume']} м³"
        details = '\n'.join([
            'Сайт: ganin-group.ru', f"Марка: {data['grade']}", f"Объём: {volume}",
            f"Место доставки: {data['address']}", f"Бетононасос: {data['pump']}", f"Дата заливки: {date}",
        ])
        if data['calculation']:
            details += f"\nИсходный расчёт: {data['calculation']}"
        lead, created = Lead.objects.get_or_create(submission_id=data['submission_id'], defaults={
            'name': 'Бетон с доставкой', 'phone': data['phone'], 'page': data['origin'],
            'details': details,
        })
        if created:
            notify_lead(lead)
        if wants_json:
            return JsonResponse({'accepted': True})
        return render(request, 'pages/delivery_quote.html', {'accepted': True})
    if wants_json and form.is_bound:
        return JsonResponse({'errors': [str(e) for errors in form.errors.values() for e in errors]}, status=400)
    return render(request, 'pages/delivery_quote.html', {
        'form': form,
        'ctypes': ConstructionType.objects.filter(published=True),
        'grades': ConcreteGrade.objects.filter(published=True),
    })
