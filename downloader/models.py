from django.db import models
from django.conf import settings

# Create your models here.

class DownloadJob(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        null=True,  # Permite que o valor no BD seja NULO
        blank=True  # Permite que o campo no Django Admin/Forms fique em branco
    )
    url = models.URLField(max_length=800)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    s3_link = models.URLField(max_length=800, blank=True, null=True)
    download_type = models.CharField(max_length=10, default='video')
    quality = models.CharField(max_length=10, default='720p')

    def __str__(self):
        return f"(id={self.id}, {self.url}, {self.status})"
    
