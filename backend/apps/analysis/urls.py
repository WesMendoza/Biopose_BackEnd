from django.urls import path, include

app_name = 'analysis'

urlpatterns = [
    path('', include('apps.analysis.api.router')),
]
