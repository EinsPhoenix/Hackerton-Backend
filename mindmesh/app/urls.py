from django.urls import path
from .views import UsageDataView

from .Api import api

urlpatterns = [
    # #alt
    # path('usage-data/', UsageDataView.as_view(), name='usage_data'),
   
    
    #neu
    path('api/', api.urls)
]