from django.contrib import admin, messages
from .models import Pet, PetExtraPhoto


class PetExtraPhotoInline(admin.TabularInline):
    model = PetExtraPhoto
    extra = 1


@admin.register(Pet)
class PetAdmin(admin.ModelAdmin):
    list_display = ("nome", "especie", "status", "solicitante", "data_cadastro")
    list_filter = ("status", "especie", "data_cadastro")
    search_fields = ("nome", "raca", "solicitante__username")
    prepopulated_fields = {"slug": ("nome",)}
    inlines = [PetExtraPhotoInline]
    readonly_fields = ("data_cadastro", "data_atualizacao")
    list_per_page = 20
    
    # Adicionando a ação de aprovação
    actions = ["aprovar_pets"]

    @admin.action(description="Aprovar pets selecionados (mudar status para Disponível)")
    def aprovar_pets(self, request, queryset):
        # Filtra apenas os que estão pendentes para evitar mudanças indesejadas
        pets_para_aprovar = queryset.filter(status=Pet.StatusChoices.PENDENTE)
        
        updated_count = pets_para_aprovar.update(status=Pet.StatusChoices.DISPONIVEL)
        
        self.message_user(
            request,
            f"{updated_count} pets foram aprovados e estão agora disponíveis na galeria.",
            messages.SUCCESS,
        )

@admin.register(PetExtraPhoto)
class PetExtraPhotoAdmin(admin.ModelAdmin):
    list_display = ("pet", "ordem", "data_envio")
    list_filter = ("data_envio", "pet__especie")
    search_fields = ("pet__nome",)