# adocoes/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # --- ROTAS DE ENTRADA E AUTENTICAÇÃO ---
    path('', views.LandingPageView.as_view(), name='landing'),
    path('entrar-visitante/', views.VisitorRedirectView.as_view(), name='entrar_visitante'),
    path('cadastro/', views.SignUpView.as_view(), name='signup'),
    
    # Usamos a view de Logout nativa do Django.
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # --- ROTAS DO APLICATIVO (PROTEGIDAS) ---
    path('galeria/', views.PetListView.as_view(), name='galeria_pets'),
    path('pet/adicionar/', views.PetCreateView.as_view(), name='adicionar_pet'),
    path('pet/<slug:slug>/', views.PetDetailView.as_view(), name='detalhe_pet'),
    path('pet/<slug:slug>/editar/', views.PetUpdateView.as_view(), name='editar_pet'),
    path('pet/<slug:slug>/deletar/', views.PetDeleteView.as_view(), name='deletar_pet'),
    
    # Relatórios continuam exclusivos para staff
    path('relatorios/', views.RelatorioPetView.as_view(), name='relatorio_pets'),
]