from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
import yt_dlp
from yt_dlp.utils import DownloadError
import os
from django.conf import settings


# @login_required
def home(request: HttpRequest):

    #Implementar logica se 1080p estiver selecionado, necessario estar logado.
    context = {}

    if request.method == 'POST':
        
        video_url = request.POST.get('video_url')

        #Implementar logica de carregar a preview do video antes do download.
        
        if video_url:
            try:
                ffmpeg_path = os.path.join(settings.BASE_DIR, 'bin', 'ffmpeg')

                ydl_opts = {
                    'format': 'best[height=720][ext=mp4]/best[height<=?720][ext=mp4]/best[ext=mp4]',
                    'noplaylist': True,
                    'ffmpeg_location': ffmpeg_path,
                    'rm_cachedir': True,
                    'extractor_args': {'youtube': {'player_client': ['android_sdkless']}},
                }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info_dict = ydl.extract_info(video_url, download=False)
                    download_url = info_dict.get('url', None)
                    video_title = info_dict.get('title', 'Video')
                    context['video_title'] = video_title
                    context['download_url'] = download_url
                    return render(request, 'home.html', context)
            except DownloadError:
                context['error_message'] = 'Invalid video URL. Please try again.'
        else:
            context['error_message'] = 'Please enter a video URL.'


    return render(request, 'home.html', context)
