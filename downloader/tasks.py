import yt_dlp
import os
from celery import shared_task
from django.conf import settings
# from .models import DownloadJob 
from . import models
import tempfile
import shutil
from django.core.files.storage import default_storage
from django.core.files import File
import boto3
from botocore.exceptions import NoCredentialsError, ClientError

def _build_ydl_opts(download_type, quality, video_url):

    ffmpeg_path = str(settings.FFMPEG_BIN_PATH)

    # Adicionar aqui argumentos para outras plataformas
    EXTRACTOR_ARGS = {
        'youtube': {
            'player_client': ['android_sdkless']
        },
        'facebook':{}
        # 'vimeo': {},
        # 'twitter': {}
        # Adicione outros conforme necessário
    }

    ydl_opts_dict = {
            'format': 'best[ext=mp4][height<=720]/best[height<=720]',
            'noplaylist': True,
            'ffmpeg_location': ffmpeg_path,
            'rm_cachedir': True,
            'extractor_args': EXTRACTOR_ARGS,
            'restrictfilenames': True
        }
    

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

            ydl_opts_dict['format'] = 'best[ext=mp4][height<=720]/best[height<=720]'

    return ydl_opts_dict


def _execute_download(video_url, ydl_opts_dict):

    # Cria uma pasta temporária no servidor
    temp_dir = tempfile.mkdtemp()
    local_filepath = None

    print(f"[DEBUG] Baixando para o diretório temporário: {temp_dir}") 
    
    try:
        # Download do arquivo em uma pasta temporária no servidor
        ydl_opts_dict['outtmpl'] = os.path.join(temp_dir, '%(id)s.%(ext)s')
        with yt_dlp.YoutubeDL(ydl_opts_dict) as ydl:

            # Extrai as informações do video sem fazer download
            info_dict = ydl.extract_info(video_url, download=False)
            
            # Extrai o diretório do arquivo na pasta temporária e cria um nome
            local_filepath = ydl.prepare_filename(info_dict)
            if not local_filepath:
                raise FileNotFoundError("yt-dlp não preparou um nome de arquivo.")
            
            print(f"[DEBUG] Caminho preparado: {local_filepath}")
            
            # Faz o download do video
            ydl.download([video_url])
            
            if not os.path.exists(local_filepath):
                raise FileNotFoundError(f"yt-dlp não criou o arquivo em {local_filepath}.")
            
            print(f"[DEBUG] Download local concluído: {local_filepath}")

        # UPLOAD 
        filename = os.path.basename(local_filepath)
        s3_path = f'downloads/{filename}' 
        public_url = None
        
        try:
            print(f"[DEBUG] Iniciando upload Boto3 para S3 em: {s3_path}...")
            
            # Pega as configurações do settings.py (que o Celery leu do .env)
            bucket_name = settings.AWS_STORAGE_BUCKET_NAME
            region_name = settings.AWS_S3_REGION_NAME
            
            if not bucket_name or not region_name:
                raise ValueError("AWS_STORAGE_BUCKET_NAME ou AWS_S3_REGION_NAME não estão no .env!")

            # Conecta ao S3
            s3_client = boto3.client(
                's3',
                region_name=region_name
                # As chaves (KEY e SECRET) serão lidas do .env automaticamente!
            )

            # Define as permissões de leitura pública
            # Isso é necessário (ACLs desabilitadas)
            # extra_args = {
            #     'ACL': 'public-read' 
            # }

            # Faz o upload para o bucket
            s3_client.upload_file(
                local_filepath, # O arquivo no /tmp/
                bucket_name,    # O nome do bucket
                s3_path,        # O caminho do arquivo no bucket
                ExtraArgs={
                # Esta linha força o download
                'ContentDisposition': f'attachment; filename="{filename}"'
                }
            )
            
            print("[DEBUG] Upload Boto3 CONCLUÍDO.")
            
            # Gera a URL pública do s3 para download do arquivo
            public_url = f"https://{bucket_name}.s3.{region_name}.amazonaws.com/{s3_path}"
            print(f"[DEBUG] URL Pública gerada: {public_url}")
        
        except NoCredentialsError as e:
            print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            print("[ERROR] FALHA NO UPLOAD: SEM CREDENCIAIS! O Celery não leu o .env!")
            print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            raise e
        except ClientError as e:
            # Erro de AccessDenied (IAM) ou outro erro do S3
            print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            print(f"[ERROR] FALHA NO UPLOAD (ClientError): {str(e)}")
            print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            raise e
        except Exception as e:
            print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            print(f"[ERROR] FALHA NO UPLOAD (Erro Genérico): {str(e)}")
            print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            raise e 

        return public_url

    finally:
        # Limpa o arquivo do servidor
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print(f"[DEBUG] Diretório temporário {temp_dir} limpo.")

@shared_task
def process_download_job(job_id):

    job = None # Inicializa para o 'except' funcionar
    try:
        # Obter o Job e marcar como em progresso
        job = models.DownloadJob.objects.get(id=job_id)
        # (IN_PROGRESS, COMPLETED, FAILED)
        job.status = 'IN_PROGRESS' 
        job.save()
    except models.DownloadJob.DoesNotExist:
        print(f"Job {job_id} não encontrado.")
        return
    
    try:
        download_type = job.download_type
        quality = job.quality
        video_url = job.url

        # Constrói as opções 
        ydl_opts = _build_ydl_opts(download_type, quality, video_url)

        # Executa o download E o upload para o S3
        final_s3_url = _execute_download(video_url, ydl_opts) 

        # Veriffica se a URL do s é válida
        if not final_s3_url or 'https://' not in final_s3_url:
            print(f"!!! FALHA CRÍTICA no Job {job_id}: _execute_download não retornou uma URL S3 válida.")

            raise ValueError("Falha no upload para o S3, URL não retornada.")

        # Atualiza o status do Job no banco
        job.status = 'COMPLETED'
     
        # Atribui o link do arquivo no s3 para o banco
        job.s3_link = final_s3_url

        # Salva o Job atualizado no banco
        job.save()
        print(f"Job {job_id} concluído. Salvo em {final_s3_url}")

    except Exception as e:

        print(f"Erro CRÍTICO no Job {job_id}: {str(e)}")
        if job: 
            job.status = 'FAILED' 
            job.save()