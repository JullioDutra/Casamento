from django import forms

from .models import FotoConvidado, RSVP


class RSVPForm(forms.ModelForm):
    class Meta:
        model = RSVP
        fields = ["nome_completo", "telefone", "quantidade_convidados", "mensagem"]
        widgets = {
            "nome_completo": forms.TextInput(attrs={
                "class": "input-lux", "placeholder": "Seu nome",
            }),
            "telefone": forms.TextInput(attrs={
                "class": "input-lux", "placeholder": "(00) 00000-0000",
            }),
            "quantidade_convidados": forms.Select(
                choices=[(i, f"{i} pessoa" + ("s" if i > 1 else "")) for i in range(1, 6)],
                attrs={"class": "input-lux"},
            ),
            "mensagem": forms.Textarea(attrs={
                "class": "input-lux", "rows": 4,
                "placeholder": "Deixe seus votos e felicitações...",
            }),
        }
        labels = {
            "nome_completo": "Nome Completo",
            "telefone": "Telefone",
            "quantidade_convidados": "Quantidade de Convidados",
            "mensagem": "Mensagem para os Noivos",
        }


class FotoConvidadoForm(forms.ModelForm):
    class Meta:
        model = FotoConvidado
        fields = ["nome_convidado", "imagem"]
        widgets = {
            "nome_convidado": forms.TextInput(attrs={
                "class": "input-lux", "placeholder": "Seu nome (opcional)",
            }),
            "imagem": forms.ClearableFileInput(attrs={
                "class": "input-lux text-xs",
            }),
        }
        labels = {
            "nome_convidado": "Seu nome (opcional)",
            "imagem": "Foto",
        }
