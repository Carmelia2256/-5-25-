from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from .views import (
    index_view, profile_view, transaction_list_view, 
    import_export_view, export_csv_view, 
)

urlpatterns = [
    path('', index_view, name='index'),

    # Авторизация
    path('login/', LoginView.as_view(template_name='index.html'), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),

    # Профиль
    path('profile/', profile_view, name='profile'),

    # Транзакции
    path('transactions/', transaction_list_view, name='transaction_list'),

    # Импорт / экспорт
    path('import-export/', import_export_view, name='import_export'),
    path('export-csv/', export_csv_view, name='export_csv'),
]