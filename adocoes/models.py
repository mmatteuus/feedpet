from django.conf import settings
from django.core.validators import (
    FileExtensionValidator,
    MaxValueValidator,
    MinValueValidator,
)
from django.db import models
from django.urls import reverse
from django.utils.text import slugify

from .constants import (
    ALLOWED_IMAGE_EXTENSIONS,
    ALLOWED_VIDEO_EXTENSIONS,
    MAX_ADDITIONAL_PHOTOS,
)


class Pet(models.Model):
    """
    Modelo robusto e escalável que representa um animal para adoção,
    incluindo status, validações e URLs amigáveis.
    """

    class EspecieChoices(models.TextChoices):
        CACHORRO = "CACHORRO", "Cachorro"
        GATO = "GATO", "Gato"
        COELHO = "COELHO", "Coelho"
        PEIXE = "PEIXE", "Peixe"
        PASSARO = "PASSARO", "Pássaro"
        ROEDOR = "ROEDOR", "Roedor"
        REPTIL = "REPTIL", "Réptil"
        OUTRO = "OUTRO", "Outro"

    class StatusChoices(models.TextChoices):
        PENDENTE = "PENDENTE", "Pendente de Aprovação" # NOVO STATUS
        DISPONIVEL = "DISPONIVEL", "Disponível"
        EM_PROCESSO = "EM_PROCESSO", "Em Processo de Adoção"
        ADOTADO = "ADOTADO", "Adotado"

    # NOVO CAMPO: Rastreia o usuário que cadastrou o pet.
    solicitante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, # Se o usuário for deletado, não deleta o pet.
        null=True,
        blank=True,
        related_name="pets_cadastrados",
        verbose_name="Solicitante",
    )

    nome = models.CharField(
        max_length=100,
        verbose_name="Nome do Pet",
        help_text="Ex: Rex, Luna, etc.",
    )

    slug = models.SlugField(
        max_length=120,
        unique=True,
        blank=True,
        verbose_name="URL Amigável (Slug)",
        help_text="Deixe em branco para ser gerado automaticamente a partir do nome.",
    )

    especie = models.CharField(
        max_length=12,
        choices=EspecieChoices.choices,
        default=EspecieChoices.OUTRO,
        verbose_name="Espécie",
    )

    raca = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Raça",
        help_text="Opcional. Ex: Vira-lata, Poodle, Siamês.",
    )

    idade = models.PositiveIntegerField(
        verbose_name="Idade (anos)",
        validators=[MinValueValidator(0), MaxValueValidator(30)],
        help_text="Idade aproximada em anos.",
    )

    descricao = models.TextField(
        verbose_name="Descrição",
        help_text="Descreva a personalidade, história e necessidades do pet.",
    )

    foto_principal = models.ImageField(
        upload_to="pets/%Y/%m/%d/principal/", null=True, blank=True,
        verbose_name="Foto principal",
        validators=[FileExtensionValidator(ALLOWED_IMAGE_EXTENSIONS)],
        help_text="Envie a foto destaque do pet em JPG, JPEG, PNG ou WEBP.",
    )

    video = models.FileField(
        upload_to="pets/%Y/%m/%d/videos/",
        blank=True,
        null=True,
        verbose_name="Vídeo",
        validators=[FileExtensionValidator(ALLOWED_VIDEO_EXTENSIONS)],
        help_text="Envie um vídeo curto do pet (.mp4, .mov, .avi, .mkv ou .webm).",
    )

    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.PENDENTE, # O padrão agora é PENDENTE
        verbose_name="Status da Adoção",
    )

    data_cadastro = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data de Cadastro",
    )

    data_atualizacao = models.DateTimeField(
        auto_now=True,
        verbose_name="Última Atualização",
    )

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.nome)
            unique_slug = base_slug
            num = 1
            # Garante que o slug seja único no banco de dados
            while Pet.objects.filter(slug=unique_slug).exists():
                unique_slug = f"{base_slug}-{num}"
                num += 1
            self.slug = unique_slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("detalhe_pet", kwargs={"slug": self.slug})

    def __str__(self):
        return f"{self.nome} ({self.get_especie_display()})"

    class Meta:
        ordering = ["-data_cadastro"]
        verbose_name = "Pet para Adoção"
        verbose_name_plural = "Pets para Adoção"
        constraints = [
            models.UniqueConstraint(
                fields=["nome", "especie"], name="unique_pet_nome_especie"
            )
        ]

    @property
    def limite_fotos_extras(self):
        return MAX_ADDITIONAL_PHOTOS


class PetExtraPhoto(models.Model):
    pet = models.ForeignKey(
        Pet,
        on_delete=models.CASCADE,
        related_name="fotos_extras",
        verbose_name="Pet",
    )
    imagem = models.ImageField(
        upload_to="pets/%Y/%m/%d/galeria/",
        verbose_name="Foto adicional",
        validators=[FileExtensionValidator(ALLOWED_IMAGE_EXTENSIONS)],
    )
    ordem = models.PositiveSmallIntegerField(default=0, verbose_name="Ordem")
    data_envio = models.DateTimeField(auto_now_add=True, verbose_name="Data de envio")

    class Meta:
        ordering = ["ordem", "data_envio", "id"]
        verbose_name = "Foto adicional do pet"
        verbose_name_plural = "Fotos adicionais do pet"

    def __str__(self):
        return f"{self.pet.nome} - foto adicional #{self.pk}"