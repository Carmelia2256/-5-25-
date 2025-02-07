from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Sum
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib import messages
import csv
import io

from .models import Transaction, Category
from .forms import TransactionForm, CSVImportForm

def index_view(request):
    """
    Авторизация.
    """
    if request.user.is_authenticated:
        return redirect('profile')
    return render(request, 'index.html')

@login_required
def profile_view(request):
    """
    Личный кабинет.
    """
    # 1. Считаем общий доход
    incomes_sum = Transaction.objects.filter(
        user=request.user,
        category__category_type='income'
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    # 2. Считаем общий расход
    expenses_sum = Transaction.objects.filter(
        user=request.user,
        category__category_type='expense'
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    # 3. Итоговый баланс
    balance = incomes_sum - expenses_sum

    # 4. Данные для пироговой диаграммы (распределение расходов по категориям)
    expense_categories = Category.objects.filter(category_type='expense')
    expense_stats_labels = []
    expense_stats_values = []
    for cat in expense_categories:
        total = Transaction.objects.filter(user=request.user, category=cat)\
                                   .aggregate(Sum('amount'))['amount__sum'] or 0
        if total > 0:
            expense_stats_labels.append(cat.name)
            expense_stats_values.append(float(total))

    # 5. Данные для ЛИНЕЙНОГО графика «Баланс по датам»
    # Получим все транзакции по пользователю, отсортированные по дате
    transactions = Transaction.objects.filter(user=request.user).order_by('date')

    running_balance = 0
    date_balance_map = {}
    # Проходимся по всем транзакциям в порядке возрастания даты
    for tx in transactions:
        if tx.category.category_type == 'income':
            running_balance += tx.amount
        else:
            running_balance -= tx.amount
        # На каждую дату у нас «текущий баланс»
        date_balance_map[tx.date] = running_balance

    # Преобразуем в два списка: labels (строки дат), data (значения баланса)
    balance_labels = sorted(date_balance_map.keys())
    # Превращаем date в строку вида 'YYYY-MM-DD'
    balance_labels_str = [d.strftime('%Y-%m-%d') for d in balance_labels]
    balance_values = [float(date_balance_map[d]) for d in balance_labels]

    context = {
        'balance': balance,
        'incomes_sum': incomes_sum,
        'expenses_sum': expenses_sum,

        # Пироговая диаграмма
        'expense_stats_labels': expense_stats_labels,
        'expense_stats_values': expense_stats_values,

        # Линейный график
        'balance_labels': balance_labels_str,
        'balance_values': balance_values,
    }
    return render(request, 'profile.html', context)

@login_required
def transaction_list_view(request):
    """
    Если запрос POST — пытаемся сохранить новую транзакцию.
    Если GET — показываем список транзакций и форму на одной странице.
    """
    transactions = Transaction.objects.filter(user=request.user).order_by('-date')

    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            new_tx = form.save(commit=False)
            new_tx.user = request.user
            new_tx.save()
            messages.success(request, "Транзакция успешно добавлена.")
            return redirect('transaction_list')  # после добавления обновим страницу
    else:
        form = TransactionForm()

    context = {
        'transactions': transactions,
        'form': form
    }
    return render(request, 'transaction_list.html', context)

@login_required
def import_export_view(request):
    """ Одна страница для загрузки CSV и показа формы. """
    if request.method == 'POST':
        form = CSVImportForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            # Обрабатываем CSV
            decoded_file = csv_file.read().decode('utf-8')
            io_string = io.StringIO(decoded_file)
            reader = csv.reader(io_string, delimiter=',')

            # Ожидаем формат: date,category_id,amount,description
            for row in reader:
                if len(row) < 4:
                    continue
                date_str, category_id_str, amount_str, desc = row

                try:
                    category_id = int(category_id_str)
                    category = Category.objects.get(id=category_id)
                    amount = float(amount_str)
                except (ValueError, Category.DoesNotExist):
                    # пропускаем некорректные строки
                    continue

                Transaction.objects.create(
                    user=request.user,
                    category=category,
                    amount=amount,
                    date=date_str,
                    description=desc
                )
            messages.success(request, "Данные успешно импортированы.")
            return redirect('import_export')
    else:
        form = CSVImportForm()

    return render(request, 'import_export.html', {'form': form})

@login_required
def export_csv_view(request):
    """ Генерируем CSV-файл с текущими транзакциями пользователя """
    transactions = Transaction.objects.filter(user=request.user)

    # Создаём объект HttpResponse c заголовками для скачивания CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="transactions_export.csv"'

    writer = csv.writer(response)
    # Шапка CSV (например: date, category_id, amount, description)
    writer.writerow(['date', 'category_id', 'amount', 'description'])

    for tx in transactions:
        writer.writerow([tx.date, tx.category.id, tx.amount, tx.description or ''])

    return response