# API de Processamento de Mídia (Python, Celery, AWS S3 & RDS)

![Status do CI](https://github.com/SEU-USUARIO/SEU-REPOSITORIO/actions/workflows/ci.yml/badge.svg)

Uma API RESTful de back-end de alta performance, construída em Python e Django, para processamento assíncrono de mídia. O projeto é desenhado como um serviço desacoplado, capaz de receber requisições de download, processá-las em segundo plano usando Celery, e fazer o upload do resultado final diretamente para um bucket AWS S3.

Esta arquitetura garante que a API permaneça 100% responsiva, retornando uma resposta em milissegundos, mesmo ao processar arquivos pesados de vídeo que exigem mesclagem com FFmpeg.

---

## 🚀 Arquitetura e Fluxo de Dados

Este projeto foi desenhado para ser uma solução "nativa da nuvem", escalável e robusta, focada em resolver o problema de tarefas de longa duração (I/O-bound).

**O fluxo de uma requisição é o seguinte:**

1.  Um cliente (ex: um front-end JavaScript) envia um `POST` para `/api/v1/jobs/` com uma URL de vídeo e a qualidade desejada.
2.  A **API (Django Rest Framework)** valida os dados e salva um novo `Job` no banco **AWS RDS (PostgreSQL)** com o status `IN_PROGRESS`.
3.  A API publica o `job_id` na fila de mensagens **Redis**.
4.  A API retorna **imediatamente** (`HTTP 201 Created`) para o cliente com os dados do job pendente.
5.  Um **Worker (Celery)**, rodando em um processo separado, consome a tarefa da fila Redis.
6.  O Worker atualiza o `celery.py` para ler o `.env`, garantindo que ele tenha as credenciais da AWS.
7.  O Worker usa `yt-dlp` para baixar o vídeo e o áudio em um diretório temporário (`/tmp/`).
8.  O Worker usa `FFmpeg` para mesclar os arquivos de áudio e vídeo.
9.  O Worker usa **Boto3** (a SDK da AWS) para fazer o upload **explícito** do arquivo final (do `/tmp/`) para o bucket **AWS S3**.
10. Durante o upload, ele define o cabeçalho `ContentDisposition: "attachment"` para forçar o download no navegador.
11. O Worker deleta o diretório temporário local.
12. O Worker atualiza o `Job` no AWS RDS com o status `COMPLETED` e o link público do S3 (`s3_link`).
13. O cliente (front-end), que estava "pollando" (consultando) o endpoint `GET /api/v1/jobs/<id>/`, recebe o novo status e o link de download.

---

## 🛠️ Stack de Tecnologias

| Categoria | Tecnologia | Propósito |
| :--- | :--- | :--- |
| **Back-End** | Python, Django | Estrutura principal da aplicação e ORM |
| **API** | Django Rest Framework (DRF) | Criação de endpoints `POST` e `GET` para os jobs |
| **Filas & Tarefas** | Celery, Redis | Execução de downloads pesados em segundo plano (assíncrono) |
| **Cloud (Banco)** | AWS RDS (PostgreSQL) | Banco de dados relacional gerenciado e escalável |
| **Cloud (Storage)** | AWS S3, Boto3 | Armazenamento de objetos (arquivos de vídeo) na nuvem |
| **Processamento** | `yt-dlp`, `FFmpeg` | Download e mesclagem de áudio/vídeo |
| **Testes & CI/CD** | Pytest, GitHub Actions | Testes de integração da API e automação de build |
| **Segurança** | `django-environ` | Gerenciamento de segredos (`.env`) para AWS e DB |

---

## 🏁 Execução e Teste do Ambiente Local

Este guia detalha o procedimento completo para configurar, executar e testar o projeto localmente.

### Pré-requisitos

Para a execução bem-sucedida da aplicação, os seguintes componentes de software devem estar instalados e configurados:

1.  **Python:** Versão 3.10 ou superior.
2.  **Servidor de Mensagens:** Um servidor **Redis** deve estar ativo e acessível (ex: `redis-server`).
3.  **Banco de Dados:** Um servidor **PostgreSQL** (local ou remoto, como AWS RDS).
4.  **Armazenamento AWS:** Um **Bucket S3** configurado e acessível.
5.  **Credenciais AWS:** Um **Usuário IAM** com as seguintes permissões mínimas no bucket: `s3:PutObject`.
6.  **Biblioteca de Mídia:** `FFmpeg` deve estar instalado e acessível (seja no PATH do sistema ou no diretório `/bin` do projeto, conforme `FFMPEG_BIN_PATH`).

### 1. Configuração Inicial

Primeiro, clone o repositório, configure o ambiente virtual e instale as dependências:

```bash
git clone [https://github.com/SEU-USUARIO/SEU-REPOSITORIO.git](https://github.com/SEU-USUARIO/SEU-REPOSITORIO.git)
cd SEU-REPOSITORIO

# Crie e ative o ambiente virtual
python -m venv venv
source venv/bin/activate  # (Linux/Mac)
# ou .\venv\Scripts\activate (Windows)

# Instale as dependências
pip install -r requirements.txt


