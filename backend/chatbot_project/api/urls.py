from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload_manual),
    path('ask/', views.ask_question),
    path('health/', views.health_check),
]