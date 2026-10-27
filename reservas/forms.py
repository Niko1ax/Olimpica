from .models import Cancha, Complejo, PerfilUsuario
from .models import Cancha

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class RegistroForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        label="Correo electrónico",
        widget=forms.EmailInput(attrs={
            "placeholder": "ejemplo@correo.com",
            "autocomplete": "email",
        }),
    )

    telefono = forms.CharField(
        required=True,
        max_length=25,
        label="Número de teléfono",
        widget=forms.TextInput(attrs={
            "placeholder": "Ej.: 11 1234-5678",
            "autocomplete": "tel",
        }),
    )

    class Meta:
        model = User
        fields = ["username", "email"]

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()

        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "Ya existe una cuenta registrada con ese correo electrónico."
            )

        return email

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.email = self.cleaned_data["email"].strip().lower()

        if commit:
            usuario.save()

        return usuario

from django import forms
from .models import Complejo


class ComplejoForm(forms.ModelForm):
    class Meta:
        model = Complejo
        fields = ["nombre", "direccion", "telefono", "descripcion"]

        labels = {
            "nombre": "Nombre del complejo",
            "direccion": "Dirección",
            "telefono": "Teléfono de contacto",
            "descripcion": "Descripción",
        }

        widgets = {
            "nombre": forms.TextInput(attrs={
                "placeholder": "Ej.: Complejo Deportivo Olimpica",
            }),
            "direccion": forms.TextInput(attrs={
                "placeholder": "Calle y número, localidad",
            }),
            "telefono": forms.TextInput(attrs={
                "placeholder": "Ej.: 11 1234-5678",
            }),
            "descripcion": forms.Textarea(attrs={
                "rows": 4,
                "placeholder": "Contá qué ofrece el complejo...",
            }),
        }

        

class CanchaForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        if user is not None and not user.is_staff:
            perfil = PerfilUsuario.objects.filter(
                usuario=user,
                rol="DUENIO",
            ).first()

            if perfil is not None:
                self.fields["complejo"].queryset = Complejo.objects.filter(
                    dueno=perfil
                )
            else:
                self.fields["complejo"].queryset = Complejo.objects.none()

    class Meta:
        model = Cancha
        fields = [
            "complejo",
            "nombre",
            "superficie",
            "precio_por_hora",
            "activa",
        ]
        labels = {
            "complejo": "Complejo deportivo",
            "nombre": "Nombre de la cancha",
            "superficie": "Tipo de superficie",
            "precio_por_hora": "Precio por hora",
            "activa": "Cancha activa",
        }
        widgets = {
            "complejo": forms.Select(),
            "nombre": forms.TextInput(
                attrs={"placeholder": "Ej.: Cancha 1"}
            ),
            "superficie": forms.Select(),
            "precio_por_hora": forms.NumberInput(
                attrs={
                    "min": "0.01",
                    "step": "0.01",
                    "placeholder": "Ej.: 25000",
                }
            ),
        }

    def clean_precio_por_hora(self):
        precio = self.cleaned_data["precio_por_hora"]

        if precio <= 0:
            raise forms.ValidationError(
                "El precio por hora debe ser mayor que cero."
            )

        return precio
