from django.http import HttpRequest #HttpResponse, JsonResponse, HttpResponseServerError
from django.shortcuts import render
import yt_dlp
from yt_dlp.utils import DownloadError
import os
from django.conf import settings

# Handle download options based on user selection
def option_handler(request: HttpRequest):

    try:

        quallity = request.POST.get('quality-options')
        download_type = request.POST.get('download-type')
        ffmpeg_path = str(settings.FFMPEG_BIN_PATH)
        path_template = str(settings.MEDIA_ROOT / 'downloads' / '%(title)s.%(ext)s')

        ydl_opts_dict = {
            'format': '',
            'noplaylist': True,
            'ffmpeg_location': ffmpeg_path,
            'rm_cachedir': True,
            'extractor_args': {'youtube': {'player_client': ['android_sdkless']}},
            'outtmpl': path_template,
            'restrictfilenames': True
        }

        format_strings = {
        '1080': 'bestvideo[height=1080][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height=1080]+bestaudio',
        '720': 'bestvideo[height=720][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height=720]+bestaudio/best[height=720][ext=mp4]/best[height=720]',
        '480': 'bestvideo[height=480][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height=480]+bestaudio/best[height=480][ext=mp4]/best[height=480]',
        '360': 'bestvideo[height=360][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height=360]+bestaudio/best[height=360][ext=mp4]/best[height=360]',
    }

        match (download_type, quallity):
             
            case ('audio', _):
                ydl_opts_dict['format'] = 'bestaudio/best'
                return media_download_handler(request, ydl_opts_dict)
            
            case ('video', '720p'):
                ydl_opts_dict['format'] = format_strings['720']
                return media_download_handler(request, ydl_opts_dict)

            case ('video', '1080p'):
                # Implementar verificcação de usuario premium aqui futuramente
                ydl_opts_dict['format'] = format_strings['1080']
                return media_download_handler(request, ydl_opts_dict)
            
            case ('video', '480p'):
                ydl_opts_dict['format'] = format_strings['480']
                return media_download_handler(request, ydl_opts_dict)
            
            case ('video', '360p'):
                ydl_opts_dict['format'] = format_strings['360']
                return media_download_handler(request, ydl_opts_dict)
            
    except Exception as error:
        context = {'error_message': f'An error occurred: {str(error)}'}
        return render(request, 'home.html', context)

# Handle media download
def media_download_handler(request: HttpRequest, ydl_opts_dict):

#####################################################################

# IMPLEMENTAR ASSINCRONISMO PARA MELHORAR A PERFORMANCE DOS DOWNLOADS (E.G USAR CELERY OU OUTRA FERRAMENTA PARA GERENCIAR TAREFAS ASSINCRONAS)

# IMPLEMENTAR LOGICA DE VERIFICAÇÃO DE USUARIO PREMIUM AQUI FUTURAMENTE

# IMPLEMENTAR LOGICA DE LIMITE DE TEMPO MAXIMO DO VIDEO (E.G 10 MINUTOS FREE USERS | PREMIUM USERS UNLIMITED)

#IMPLEMENTAR LOGICA DE LIMITE DE DOWNLOADS POR DIA (E.G 5 DOWNLOADS FREE USERS | PREMIUM USERS UNLIMITED)

# IMPLEMENTAR LOGICA DE FILTRO DE SITES RESTRITOS (E.G SITES ADULTOS, ETC) PARA FREE USERS

# IMPLEMENTAR LOGICA DE NOTIFICAÇÃO POR EMAIL APOS DOWNLOAD PARA USUARIOS PREMIUM

# IMPLEMENTAR LOGICA DE ARMAZENAMENTO TEMPORARIO DOS ARQUIVOS NO SERVIDOR (E.G ARQUIVOS EXCLUÍDOS APOS 24 HORAS)

# IMPLEMENTAR LOGICA DE CACHE PARA DOWNLOADS FREQUENTES (E.G SE O MESMO VIDEO FOR BAIXADO NOVAMENTE, USAR O ARQUIVO JA EXISTENTE NO SERVIDOR)

#####################################################################
    context = {}

    video_url = request.POST.get('video_url')

    if video_url:
                
                try:

                    format = ydl_opts_dict['format']
                    
                    if format == 'bestaudio/best':
                         ydl_opts_dict[format] = 'bestaudio/best'

                    with yt_dlp.YoutubeDL(ydl_opts_dict) as ydl:
                        info_dict = ydl.extract_info(video_url, download=False)
                        # download_url = info_dict.get('url', None)
                        video_title = info_dict.get('title', 'Video')

                        # Generate the download URL for the media file
                        filepath_on_server = ydl.prepare_filename(info_dict)
                        ydl.download([video_url])

                        relative_path = os.path.relpath(filepath_on_server, settings.MEDIA_ROOT)
                        download_url = os.path.join(settings.MEDIA_URL, relative_path).replace('\\', '/')

                        context['video_title'] = video_title
                        context['download_url'] = download_url

                        return render(request, 'home.html', context)
                        
                except DownloadError:
                    context['error_message'] = 'Invalid video URL. Please try again.'

    return render(request, 'home.html', context)