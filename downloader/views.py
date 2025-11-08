from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from yt_dlp.utils import DownloadError
from django.conf import settings
from .utils import download_handler
from .tasks import process_download_job

from rest_framework import viewsets, mixins, permissions
from .models import DownloadJob
from .serializers import DownloadJobSerializer

class DownloadJobViewSet(viewsets.ModelViewSet, 
                        mixins.RetrieveModelMixin,
                        mixins.ListModelMixin,
                        viewsets.GenericViewSet):

    # queryset = DownloadJob.objects.all().order_by('-created_at')
    serializer_class = DownloadJobSerializer

    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return DownloadJob.objects.filter(user=user).order_by('-created_at')

    def perform_create(self, serializer):
        # 1. Salva o Job com url, quality, e type no banco
        job = serializer.save(user=self.request.user)

        # 2. Enfileira a tarefa no Celery
        process_download_job.delay(job.id) 

        print(f"Job {job.id} enfileirado para o usuário: {self.request.user.username}")






# @login_required
def home(request: HttpRequest):

    #Implementar logica se 1080p estiver selecionado, necessario estar logado.
    # context = {}

    if request.method == 'POST':
        
        return download_handler.option_handler(request)

        #Implementar logica de carregar a preview do video antes do download.
        
        


    return render(request, 'home.html')
