from django.urls import path
from .views import UsageDataView

from .Api import api

urlpatterns = [
    path('usage-data/', UsageDataView.as_view(), name='usage_data'),
    path('api/', api.urls)
]