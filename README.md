# Plataforma de API de Download de Mídia (Assíncrona com Celery e AWS)

![Status do CI](https://github.com/attomsec/Universal-Video-Downloader//actions/workflows/ci.yml/badge.svg)

Este projeto implementa uma API RESTful de back-end para enfileirar e processar downloads de mídia (como vídeos do YouTube) de forma assíncrona, utilizando uma arquitetura escalável e nativa da nuvem AWS.

O usuário pode submeter uma URL para download e receber imediatamente um ID de tarefa. Um worker Celery processa o download em segundo plano, mescla áudio e vídeo com FFmpeg, faz o upload do arquivo final para o **AWS S3** e atualiza o status no banco de dados **AWS RDS**.

---

## 🚀 Principais Features e Arquitetura

Este projeto foi desenhado para ir "além do CRUD", focando em uma arquitetura de microsserviço robusta, escalável e pronta para produção.

* **API RESTful:** Construída com **Django Rest Framework (DRF)** para submissão e consulta de tarefas.
* **Processamento Assíncrono:** A API responde em milissegundos. O trabalho pesado (download) é gerenciado por workers **Celery** e uma fila **Redis**, garantindo que a aplicação nunca trave.
* **Integração Nativa da Nuvem (AWS):**
    * **Banco de Dados:** Utiliza **PostgreSQL** gerenciado no **AWS RDS**, garantindo performance e confiabilidade.
    * **Armazenamento de Arquivos:** Os arquivos finais são enviados diretamente para o **AWS S3**, permitindo escalabilidade infinita de armazenamento e servindo os arquivos de forma eficiente.
* **Testes Automatizados:** Cobertura de testes de integração para a API usando **Pytest**, garantindo que novos commits não quebrem a funcionalidade.
* **CI/CD (Integração Contínua):** Um pipeline com **GitHub Actions** é executado a cada `push`, instalando dependências e rodando o `pytest` automaticamente.
* **Configuração Segura:** Todas as chaves secretas (AWS, DB, Django) são gerenciadas fora do código usando `django-environ` e um arquivo `.env`.

## ⚙️ Fluxo da Arquitetura

1.  Um cliente faz um `POST /api/v1/jobs/` com a `url` e `quality`.
2.  A **API (Django)** valida os dados, cria um `Job` no **AWS RDS** com status `PENDENTE`.
3.  A API envia o `job_id` para a fila **Redis** e responde imediatamente `201 Created` para o cliente.
4.  Um **Worker (Celery)**, que está monitorando a fila, pega a tarefa.
5.  O Worker atualiza o status do Job no RDS para `PROCESSANDO`.
6.  O Worker usa `yt-dlp` e `FFmpeg` para baixar e mesclar o vídeo em um diretório temporário.
7.  O Worker faz o upload do arquivo final do `/tmp` diretamente para o **AWS S3**.
8.  O Worker atualiza o Job no RDS para `CONCLUIDO` e salva a URL pública do S3.
9.  O cliente pode fazer um `GET /api/v1/jobs/<id>/` para ver o status e obter o link de download do S3.

## 🛠️ Stack de Tecnologias

* **Back-end:** Python, Django, Django Rest Framework
* **Fila de Tarefas:** Celery, Redis
* **Banco de Dados:** PostgreSQL (AWS RDS)
* **Cloud & Storage:** AWS S3, Boto3, `django-storages`
* **Download:** `yt-dlp`, `ffmpeg`
* **Testes & CI/CD:** Pytest, GitHub Actions
* **Ambiente:** `django-environ`

---

## 🏁 Como Rodar Localmente

#### Pré-requisitos

1.  Python 3.10+
2.  Um servidor **Redis** rodando (ex: `redis-server`)
3.  Um servidor **PostgreSQL** (local ou na nuvem, como o AWS RDS)
4.  Um **Bucket AWS S3**
5.  Credenciais da **AWS IAM** com permissão de escrita no seu bucket.
6.  `ffmpeg` instalado e acessível no `PATH` ou na pasta `/bin` do projeto.

#### 1. Clonar o Repositório

```bash
git clone [https://github.com/SEU-USUARIO/SEU-REPOSITORIO.git](https://github.com/SEU-USUARIO/SEU-REPOSITORIO.git)
cd SEU-REPOSITORIO
