from django.urls import path
from . import views

app_name = 'events'

urlpatterns = [
    # CREATE
    path('create/', views.create, name='create'),
    
    # DETAIL (stub for Phase 1, full in Phase 3)
    path('<slug:slug>/', views.detail, name='detail'),
    
    # HELPER APIs (autocomplete for create form)
    path('api/locations/search/', views.api_locations_search, name='api_locations_search'),
    path('api/users/search/', views.api_users_search, name='api_users_search'),
    path('api/pins/', views.api_event_pins, name='api_event_pins'),
]

