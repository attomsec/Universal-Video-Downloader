# em downloader/test_api.py (NOVO ARQUIVO)
import pytest
from rest_framework.test import APIClient
from .models import DownloadJob

# A marcação 'django_db' garante que o teste tenha acesso a um 
# banco de dados limpo e separado (não o RDS!)
@pytest.mark.django_db
def test_create_job_api():
    # 1. Preparação (Setup)
    client = APIClient()  # Cria um cliente de API falso
    url_api = '/api/v1/jobs/' # O endpoint que queremos testar
    dados_do_post = {
        'url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
    }

    # 2. Execução (Action)
    # Simula um POST para a nossa API com os dados
    response = client.post(url_api, dados_do_post, format='json')

    # 3. Verificação (Assertion)

    # O POST foi bem-sucedido? (Status 201 CREATED)
    assert response.status_code == 201

    # O job foi realmente criado no banco de dados?
    assert DownloadJob.objects.count() == 1

    # O job criado tem os dados corretos?
    job_criado = DownloadJob.objects.first()
    assert job_criado.url == 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
    assert job_criado.status == 'PENDING' # Verifica se o status default está correto

    # A resposta da API contém o status correto?
    assert response.data['status'] == 'PENDING'
    assert response.data['url'] == 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'