import json
from django.shortcuts import get_object_or_404, redirect, render
from django.http import JsonResponse
from .models import Thread
from .modules.aiModule import GenerateResponse  
import logging
from django.contrib.auth.decorators import login_required
import requests

from django.shortcuts import render
from django.views import View
from .modules.usage_data_processor import load_usage_data, process_usage_data
import os
import time

import logging
import json
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

logger = logging.getLogger(__name__)

isInTestMode = True
filldataAI = False


class UsageDataView(View):
    def get(self, request):
        json_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'usage_data.json')
        
        try:
            data = load_usage_data(json_file_path)
        except FileNotFoundError:
            return render(request, 'error.html', {'message': 'Usage data file not found.'})
        
        datasets = process_usage_data(data)
        
        return render(request, 'usage_data.html', {'datasets': datasets})