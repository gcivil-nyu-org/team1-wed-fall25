from django.urls import path
from . import views

app_name = 'locations'

urlpatterns = [
    path('', views.location_list, name='list'),
    path('new/', views.location_create, name='create'),
    path('<int:pk>/', views.location_detail, name='detail'),
    path('<int:pk>/edit/', views.location_edit, name='edit'),
    path('<int:pk>/favorite/', views.location_favorite_toggle, name='favorite_toggle'),
    path('favorites/', views.favorites_list, name='favorites'),
]

