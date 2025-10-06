from django.urls import path
from . import views

app_name = 'itineraries'

urlpatterns = [
    path('', views.itinerary_list, name='list'),
    path('new/', views.itinerary_create, name='create'),
    path('<int:pk>/', views.itinerary_detail, name='detail'),
    path('<int:pk>/edit/', views.itinerary_edit, name='edit'),
    path('<int:pk>/delete/', views.itinerary_delete, name='delete'),
    path('<int:pk>/items/add/', views.itinerary_item_add, name='item_add'),
    path('<int:pk>/items/reorder/', views.itinerary_item_reorder, name='item_reorder'),
    path('<int:itinerary_pk>/items/<int:item_pk>/delete/', views.itinerary_item_delete, name='item_delete'),
]

