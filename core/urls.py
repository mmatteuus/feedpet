# core/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Rota principal do projeto, que inclui TODAS as outras URLs.
    # A landing page, login, logout, etc., serão gerenciadas aqui.
    path('', include('adocoes.urls')),
]

# Configuração para servir arquivos de mídia em desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)