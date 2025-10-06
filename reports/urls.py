from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('new/', views.report_create, name='create'),
]

