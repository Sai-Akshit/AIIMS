from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .algorithm import export_data

app_name = 'main'
urlpatterns = [
    path('', views.selectTable, name='select_table'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('dataentry/', views.dataEntry, name='dataentry'),
    path('update/<int:serial_number>', views.update_data, name='update_data'),
    path('delete/<int:serial_number>', views.delete_data, name='delete_data'),
    path('delete_table/<str:table_name>', views.delete_table, name='delete_table'),
]