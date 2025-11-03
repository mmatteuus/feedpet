# adocoes/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from .constants import (
    ALLOWED_IMAGE_EXTENSIONS,
    ALLOWED_VIDEO_EXTENSIONS,
    MAX_ADDITIONAL_PHOTOS,
    MAX_ADDITIONAL_IMAGE_SIZE_MB,
    MAX_VIDEO_SIZE_MB,
)
from .models import Pet, PetExtraPhoto

# --- NOVO FORMULÁRIO DE CADASTRO ---
class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=True, help_text="O e-mail é necessário para contato."
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ("email",)


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class PetForm(forms.ModelForm):
    fotos_adicionais = forms.FileField(
        required=False,
        widget=MultipleFileInput(
            attrs={"class": "form-control", "multiple": True, "accept": "image/*"}
        ),
        label="Galeria de fotos (extras)",
        help_text=f"Envie até {MAX_ADDITIONAL_PHOTOS} fotos, cada uma com até {MAX_ADDITIONAL_IMAGE_SIZE_MB}MB.",
    )

    video = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(
            attrs={"class": "form-control", "accept": "video/*"}
        ),
        label="Vídeo do pet",
        help_text=f"Envie um vídeo curto até {MAX_VIDEO_SIZE_MB}MB.",
    )

    def __init__(self, *args, **kwargs):
        # Captura o usuário passado pela view
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        placeholders = {
            "nome": "Ex: Rex, Luna...",
            "raca": "Ex: Vira-lata, Siamês, Poodle...",
            "idade": "Idade aproximada em anos (0 a 30)",
            "descricao": "Descreva a personalidade, história e necessidades...",
        }

        # Se o usuário não for da equipe, o status não pode ser alterado.
        if self.user and not self.user.is_staff:
            self.fields.pop("status", None)

        for field_name, field in self.fields.items():
            css_class = "form-control"
            if isinstance(field.widget, forms.Select):
                css_class = "form-select"
            field.widget.attrs.setdefault("class", css_class)

            if field_name in placeholders:
                field.widget.attrs["placeholder"] = placeholders[field_name]

            if field_name == "descricao":
                field.widget.attrs["rows"] = 5

        self._existing_extra_photos = self.instance.fotos_extras.count() if self.instance.pk else 0

        if self.instance.pk and self.instance.fotos_extras.exists():
            self.fields["fotos_extras_remover"] = forms.ModelMultipleChoiceField(
                required=False,
                queryset=self.instance.fotos_extras.order_by("ordem", "id"),
                widget=forms.CheckboxSelectMultiple(attrs={"class": "form-check-input"}),
                label="Remover fotos existentes",
            )
            self.fields.move_to_end("fotos_extras_remover")

    # MÉTODOS DE VALIDAÇÃO (sem alterações) ...
    def _validate_file_extension(self, filename, allowed_extensions):
        extension = filename.split(".")[-1].lower()
        if extension not in allowed_extensions:
            raise ValidationError(
                f"Formato não permitido: .{extension}. Use: {', '.join(allowed_extensions)}."
            )

    def _validate_file_size(self, file_obj, max_size_mb):
        max_bytes = max_size_mb * 1024 * 1024
        if file_obj.size > max_bytes:
            raise ValidationError(
                f"O arquivo {file_obj.name} excede o limite de {max_size_mb}MB."
            )

    def clean_nome(self):
        nome = self.cleaned_data.get("nome")
        nomes_proibidos = ["cachorro", "gato", "pet", "animal", "outro"]
        if nome and nome.lower() in nomes_proibidos:
            raise ValidationError(
                "Por favor, forneça um nome específico para o pet."
            )
        return nome

    def clean(self):
        cleaned_data = super().clean()
        extra_files = self.files.getlist("fotos_adicionais")

        if extra_files:
            total = len(extra_files) + self._existing_extra_photos
            if total > MAX_ADDITIONAL_PHOTOS:
                raise ValidationError(f"Você pode ter no máximo {MAX_ADDITIONAL_PHOTOS} fotos extras.")
            for file_obj in extra_files:
                self._validate_file_extension(file_obj.name, ALLOWED_IMAGE_EXTENSIONS)
                self._validate_file_size(file_obj, MAX_ADDITIONAL_IMAGE_SIZE_MB)
        cleaned_data["fotos_adicionais"] = extra_files

        video_file = cleaned_data.get("video")
        if video_file:
            self._validate_file_extension(video_file.name, ALLOWED_VIDEO_EXTENSIONS)
            self._validate_file_size(video_file, MAX_VIDEO_SIZE_MB)
        
        especie = cleaned_data.get("especie")
        raca = cleaned_data.get("raca")
        if especie == Pet.EspecieChoices.OUTRO and not raca:
            self.add_error("raca", "Se a espécie é 'Outro', especifique o tipo no campo 'Raça'.")

        return cleaned_data

    def save(self, commit=True):
        pet = super().save(commit=False)
        
        # Atribui o solicitante, se for um novo pet
        if not pet.pk and self.user:
            pet.solicitante = self.user

        # Se o usuário não for staff, força o status para PENDENTE em novos cadastros
        if not self.user.is_staff and not pet.pk:
            pet.status = Pet.StatusChoices.PENDENTE

        if commit:
            pet.save()
            self._save_m2m_data(pet)

        return pet
    
    def _save_m2m_data(self, pet_instance):
        extra_files = self.cleaned_data.get("fotos_adicionais", [])
        to_remove = self.cleaned_data.get("fotos_extras_remover")

        if to_remove:
            to_remove.delete()
        
        if extra_files:
            existing_count = pet_instance.fotos_extras.count()
            for index, file_obj in enumerate(extra_files, start=existing_count + 1):
                PetExtraPhoto.objects.create(
                    pet=pet_instance,
                    imagem=file_obj,
                    ordem=index,
                )

    class Meta:
        model = Pet
        fields = [
            "nome", "especie", "status", "raca", "idade", "descricao",
            "foto_principal", "video"
        ]
        labels = {"raca": "Raça (ou Tipo)", "idade": "Idade (anos)"}
        # O campo 'solicitante' não deve ser preenchido manualmente
        exclude = ["slug", "solicitante"]