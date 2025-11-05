import yt_dlp
import os
from celery import shared_task
from django.conf import settings
from .models import DownloadJob 
import tempfile
import shutil
from django.core.files.storage import default_storage
from django.core.files import File


def _build_ydl_opts(download_type, quality):

    ffmpeg_path = str(settings.FFMPEG_BIN_PATH)
    
    #path_template = str(settings.MEDIA_ROOT / 'downloads' / '%(title)s.%(ext)s')

    ydl_opts_dict = {
        'format': '',
        'noplaylist': True,
        'ffmpeg_location': ffmpeg_path,
        'rm_cachedir': True,
        'extractor_args': {'youtube': {'player_client': ['android_sdkless']}},
        # 'outtmpl': path_template,
        'restrictfilenames': True
    }

    # print("!!! MODO DE TESTE FFmpeg: Forçando formato pré-mesclado !!!")
    ydl_opts_dict['format'] = 'best[ext=mp4][height<=720]/best[height<=720]'

    format_strings = {
        '1080': 'bestvideo[height=1080][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height=1080]+bestaudio',
        '720': 'bestvideo[height=720][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height=720]+bestaudio/best[height=720][ext=mp4]/best[height=720]',
        '480': 'bestvideo[height=480][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height=480]+bestaudio/best[height=480][ext=mp4]/best[height=480]',
        '360': 'bestvideo[height=360][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height=360]+bestaudio/best[height=360][ext=mp4]/best[height=360]',
    }

    match (download_type, quality):
        case ('audio', _):
            ydl_opts_dict['format'] = 'bestaudio/best'
        case ('video', '720p'):
            ydl_opts_dict['format'] = format_strings['720']
        case ('video', '1080p'):
            ydl_opts_dict['format'] = format_strings['1080']
        case ('video', '480p'):
            ydl_opts_dict['format'] = format_strings['480']
        case ('video', '360p'):
            ydl_opts_dict['format'] = format_strings['360']
        case _:

            ydl_opts_dict['format'] = format_strings['best[ext=mp4][height<=720]/best[height<=720]']

    return ydl_opts_dict


def _execute_download(video_url, ydl_opts_dict):
    
    temp_dir = tempfile.mkdtemp()
    local_filepath = None # Inicializa a variável
    
    print(f"Baixando para o diretório temporário: {temp_dir}")
    
    try:
        # Configura o yt-dlp para baixar nesse diretório
        ydl_opts_dict['outtmpl'] = os.path.join(temp_dir, '%(id)s.%(ext)s')

        with yt_dlp.YoutubeDL(ydl_opts_dict) as ydl:
            print("Iniciando ydl.extract_info com download=False...")
            info_dict = ydl.extract_info(video_url, download=False)
            print("ydl.extract_info concluído.")
            
            # Pega o caminho REAL do arquivo
            local_filepath = ydl.prepare_filename(info_dict)

            if not local_filepath:
                raise FileNotFoundError("yt-dlp não conseguiu preparar um nome de arquivo.")
            
            print(f"Caminho de arquivo preparado: {local_filepath}")

            print("Iniciando o ydl.download...")
            ydl.download([video_url])
            print("ydl.download concluído.")
            

            if not os.path.exists(local_filepath):
                print(f"!!! FALHA !!! ydl.download() terminou mas o arquivo {local_filepath} não existe.")
                raise FileNotFoundError(
                    f"yt-dlp não criou o arquivo em {local_filepath}. "
                    "Verifique se o FFmpeg está instalado (se necessário) ou se há permissão de escrita."
                )   
            
            print(f"Arquivo baixado com sucesso em: {local_filepath}")
        

        # Faz o upload do arquivo para o S3
        filename = os.path.basename(local_filepath)
        s3_path = f'downloads/{filename}' 
        
        print(f"Iniciando upload para o S3 em: {s3_path}")
        with open(local_filepath, 'rb') as file_obj:
            saved_path = default_storage.save(s3_path, File(file_obj))
        
        # Obtém a URL pública
        print("Upload concluído. Obtendo URL pública...")
        public_url = default_storage.url(saved_path)
        return public_url

    finally:
        # Limpa o diretório temporário
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print(f"Diretório temporário {temp_dir} limpo.")

@shared_task
def process_download_job(job_id):
    """
    Esta é a tarefa Celery principal que gerencia o processo.
    """
    # Obter o Job
    try:
        job = DownloadJob.objects.get(id=job_id)
        job.status = 'IN_PROGRESS'
        job.save()
    except DownloadJob.DoesNotExist:
        print(f"Job {job_id} não encontrado.")
        return

    # Executar sua lógica de negócio
    try:
        # Pega as opções salvas no Job
        download_type = job.download_type
        quality = job.quality
        video_url = job.url

        # Constrói as opções
        ydl_opts = _build_ydl_opts(download_type, quality)

        # Executa o download 
        '''
        
        ADICIONAR LOGICA DE MARCA D'ÁGUA PARA USERS FREE

        
        '''
        final_filepath = _execute_download(video_url, ydl_opts)

        # Sucesso: Atualiza o Job
        job.status = 'COMPLETED'

        # Salva o link S3 no Job
        # Por enquanto, é um caminho local
        relative_path = os.path.relpath(final_filepath, settings.MEDIA_ROOT)
        job.s3_link = os.path.join(settings.MEDIA_URL, relative_path).replace('\\', '/')
        job.save()

    except Exception as e:
        # Falha: Atualiza o Job com o erro
        job.status = 'FAILED'
        job.save()
        print(f"Erro no Job {job_id}: {str(e)}")