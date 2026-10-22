
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