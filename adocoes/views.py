# adocoes/views.py
import os
from django.urls import reverse_lazy
from django.contrib.auth import views as auth_views
from django.contrib.auth.mixins import AccessMixin, UserPassesTestMixin, LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, RedirectView
from django.shortcuts import redirect
from django.contrib import messages
from .models import Pet
from .forms import PetForm, CustomUserCreationForm

# --- MIXINS DE PERMISSÃO ATUALIZADOS ---

class VisitorOrUserRequiredMixin(AccessMixin):
    """
    Mixin customizado que verifica se o usuário está autenticado OU
    se identificou como 'visitante' na sessão.
    """
    def dispatch(self, request, *args, **kwargs):
        is_visitor = request.session.get('is_visitor', False)
        if not request.user.is_authenticated and not is_visitor:
            # Redireciona para a landing page se não for nem usuário nem visitante
            messages.info(request, "Por favor, faça login ou entre como visitante para continuar.")
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)
    
    def get_login_url(self):
        return reverse_lazy('landing')

class StaffRequiredMixin(UserPassesTestMixin):
    """ Exige que o usuário seja da equipe (staff). """
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_staff
    
    def get_login_url(self):
        return reverse_lazy('landing')

class PetOwnerOrStaffRequiredMixin(UserPassesTestMixin):
    """ Exige que o usuário seja o dono do pet ou da equipe. """
    def test_func(self):
        pet = self.get_object()
        user = self.request.user
        return user.is_authenticated and (user.is_staff or pet.solicitante == user)

# --- VIEWS DE ENTRADA E AUTENTICAÇÃO ---

class LandingPageView(auth_views.LoginView):
    """
    Esta é a nova porta de entrada. Ela herda da LoginView do Django
    para processar o formulário de login, mas usa nosso template customizado.
    """
    template_name = 'adocoes/landing.html'
    redirect_authenticated_user = True # Se o usuário já estiver logado, redireciona

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = "Bem-vindo ao FeedPet"
        return context

class VisitorRedirectView(RedirectView):
    """
    View simples para marcar a sessão do usuário como 'visitante'
    e redirecioná-lo para a galeria.
    """
    pattern_name = 'galeria_pets'

    def get(self, request, *args, **kwargs):
        request.session['is_visitor'] = True
        # Limpa a sessão de visitante ao fazer logout
        request.session.set_expiry(0) 
        return super().get(request, *args, **kwargs)

class SignUpView(SuccessMessageMixin, CreateView):
    """ View de cadastro de usuário. """
    form_class = CustomUserCreationForm
    template_name = 'registration/signup.html'
    success_url = reverse_lazy('landing') # Após cadastro, volta para a landing para fazer login
    success_message = "✅ Conta criada com sucesso! Faça o login para começar."
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = "Crie sua Conta"
        return context

# --- VIEWS DO APLICATIVO (PROTEGIDAS) ---

class PetListView(VisitorOrUserRequiredMixin, ListView):
    model = Pet
    template_name = 'adocoes/pet_list.html'
    context_object_name = 'pets'
    paginate_by = 8

    def get_paginate_by(self, queryset):
        # Disable pagination when building the static preview for Netlify.
        if os.getenv("STATIC_BUILD"):
            return None
        return super().get_paginate_by(queryset)

    def get_queryset(self):
        # AQUI ESTÁ A NOVA LÓGICA INTELIGENTE
        filter_type = self.request.GET.get('filtro')

        # Se o filtro for 'meus' e o usuário estiver logado...
        if filter_type == 'meus' and self.request.user.is_authenticated:
            # ...mostra todos os pets daquele usuário, em qualquer status.
            queryset = Pet.objects.filter(solicitante=self.request.user)
        else:
            # Senão, continua com o comportamento padrão: mostra pets disponíveis.
            queryset = Pet.objects.filter(status=Pet.StatusChoices.DISPONIVEL)

        # A lógica de busca continua funcionando em ambos os modos
        nome = self.request.GET.get('nome')
        especie = self.request.GET.get('especie')
        if nome:
            queryset = queryset.filter(nome__icontains=nome)
        if especie:
            queryset = queryset.filter(especie=especie)
        
        return queryset.order_by('-data_cadastro')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        filter_type = self.request.GET.get('filtro')

        # Passa o modo de filtro para o template, para que ele possa mudar o título
        context['filter_mode'] = filter_type if filter_type == 'meus' else 'public'
        
        context['is_visitor'] = self.request.session.get('is_visitor', False)
        context['especies'] = Pet.EspecieChoices.choices
        
        # O título da página agora é dinâmico
        if context['filter_mode'] == 'meus':
            context['page_title'] = "Meus Pets Cadastrados"
        else:
            context['page_title'] = 'Galeria de Pets'
        
        return context

class PetDetailView(VisitorOrUserRequiredMixin, DetailView):
    model = Pet
    template_name = 'adocoes/pet_detail.html'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_visitor'] = self.request.session.get('is_visitor', False)
        context['page_title'] = self.object.nome
        return context

class PetCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Pet
    form_class = PetForm
    template_name = 'adocoes/pet_form.html'
    success_url = reverse_lazy('galeria_pets')
    
    def get_success_message(self, cleaned_data):
        return "🐾 Seu pet foi cadastrado e enviado para análise. Obrigado!" if not self.request.user.is_staff else "🐾 O pet foi cadastrado com sucesso!"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        self.object = form.save()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Cadastrar Novo Pet'
        return context

class PetUpdateView(PetOwnerOrStaffRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Pet
    form_class = PetForm
    template_name = 'adocoes/pet_form.html'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    success_message = "✅ O cadastro do pet foi atualizado com sucesso!"

    def get_success_url(self):
        return self.object.get_absolute_url()
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Editando: {self.object.nome}'
        return context

class PetDeleteView(PetOwnerOrStaffRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Pet
    template_name = 'adocoes/pet_confirm_delete.html'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    success_url = reverse_lazy('galeria_pets')
    success_message = "🗑️ Pet removido com sucesso."

class RelatorioPetView(StaffRequiredMixin, ListView):
    model = Pet
    template_name = 'adocoes/relatorio_pets.html'
    context_object_name = 'pets'

    def get_queryset(self):
        status_filter = self.request.GET.get('status', Pet.StatusChoices.PENDENTE).upper()
        valid_statuses = [choice[0] for choice in Pet.StatusChoices.choices]
        if status_filter not in valid_statuses:
            status_filter = Pet.StatusChoices.PENDENTE
        return Pet.objects.filter(status=status_filter).order_by('-data_atualizacao')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_status = self.request.GET.get('status', Pet.StatusChoices.PENDENTE).upper()
        context['status_choices'] = Pet.StatusChoices.choices
        context['current_status'] = current_status
        context['page_title'] = f"Relatório: Pets {Pet.StatusChoices(current_status).label}"
        context['counts'] = {
            s[0].lower(): Pet.objects.filter(status=s[0]).count() for s in Pet.StatusChoices.choices
        }
        return context
    

    
