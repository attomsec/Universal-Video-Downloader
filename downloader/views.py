from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
import yt_dlp
from yt_dlp.utils import DownloadError
import os
from django.conf import settings
from .utils import download_handler


# @login_required
def home(request: HttpRequest):

    #Implementar logica se 1080p estiver selecionado, necessario estar logado.
    # context = {}

    if request.method == 'POST':
        
        return download_handler.option_handler(request)

        #Implementar logica de carregar a preview do video antes do download.
        
        


    return render(request, 'home.html')
