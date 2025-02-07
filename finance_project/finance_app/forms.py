from django import forms
from .models import Transaction

class TransactionForm(forms.ModelForm):
    """
    Форма для добавления / редактирования транзакции.
    """
    class Meta:
        model = Transaction
        fields = ['category', 'amount', 'date', 'description']
        labels = {
            'category': 'Категория',
            'amount': 'Сумма',
            'date': 'Дата',
            'description': 'Описание',
        }
        widgets = {
            'date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'description': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
        }

class CSVImportForm(forms.Form):
    """
    Форма для импорта данных из CSV-файла.
    """
    csv_file = forms.FileField(label='CSV-файл')