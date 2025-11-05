from rest_framework import serializers
from .models import DownloadJob

class DownloadJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = DownloadJob
        
        fields = ['id', 'url', 'status', 'created_at', 's3_link', 'download_type', 'quality']

        read_only_fields = ['id', 'status', 'created_at', 's3_link']