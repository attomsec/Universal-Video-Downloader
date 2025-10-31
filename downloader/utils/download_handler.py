from django.http import HttpRequest, HttpResponse, JsonResponse, HttpResponseServerError
from django.shortcuts import render
import yt_dlp
from yt_dlp.utils import DownloadError
import os
from django.conf import settings


# Handle download options based on user selection
def option_handler(request: HttpRequest):

    try:
        if request.POST.get('download-type') == 'audio':
            return audio_download_handler(request)
        elif request.POST.get('download-type') == 'video':
            return video_download_handler(request)
    except Exception as error:
        context = {'error_message': f'An error occurred: {str(error)}'}
        return render(request, 'home.html', context)

# Handle audio download    
def audio_download_handler(request: HttpRequest):

    context = {}

    audio_url = request.POST.get('video_url')

    if audio_url:
                try:
                    ffmpeg_path = os.path.join(settings.BASE_DIR, 'bin', 'ffmpeg')

                    ydl_opts = {
                        'format': 'bestaudio/best',
                        'noplaylist': True,
                        'ffmpeg_location': ffmpeg_path,
                        'rm_cachedir': True,
                        'extractor_args': {'youtube': {'player_client': ['android_sdkless']}},
                    }

                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info_dict = ydl.extract_info(audio_url, download=False)
                        download_url = info_dict.get('url', None)
                        audio_title = info_dict.get('title', 'Audio')
                        context['audio_title'] = audio_title
                        context['download_url'] = download_url
                        return render(request, 'home.html', context)
                except DownloadError:
                    context['error_message'] = 'Invalid audio URL. Please try again.'

    return render(request, 'home.html', context)

# Handle video download
def video_download_handler(request: HttpRequest):

    context = {}

    video_url = request.POST.get('video_url')

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
                    
                        #Logica antiga para JsonResponse, mantida aqui apenas por referencia futura.

                        # ext = info_dict.get('ext', 'mp4')
                        # filename = f"{video_title}.{ext}"

                        # if not download_url:
                        #     raise DownloadError('Could not retrieve download URL.')
                        
                        # response_data = {
                        #     'success': True,
                        #     'download_url': download_url,
                        #     'filename': filename,
                        # }
                        
                        # return JsonResponse(response_data)
                        
                except DownloadError:
                    context['error_message'] = 'Invalid video URL. Please try again.'

    return render(request, 'home.html', context)