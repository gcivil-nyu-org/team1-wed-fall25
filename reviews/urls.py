from django.urls import path
from . import views

app_name = 'reviews'

urlpatterns = [
    path('<int:pk>/edit/', views.review_edit, name='edit'),
    path('<int:pk>/delete/', views.review_delete, name='delete'),
]

