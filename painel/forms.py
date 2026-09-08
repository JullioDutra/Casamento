from django import forms

from .models import ConvidadoLista
from convite.models import Presente

class PresenteForm(forms.ModelForm):
    class Meta:
        model = Presente
        fields = ["titulo", "descricao", "valor", "chave_pix", "disponivel", "icone"]
        widgets = {
            "titulo": forms.TextInput(attrs={"class": "border border-stone-200 rounded px-3 py-2 text-sm w-full"}),
            "chave_pix": forms.TextInput(attrs={"class": "border border-stone-200 rounded px-3 py-2 text-sm w-full", "placeholder": "Sua chave PIX"}),
            "valor": forms.NumberInput(attrs={"class": "border border-stone-200 rounded px-3 py-2 text-sm w-full"}),
        }


class UploadPlanilhaForm(forms.Form):
    arquivo = forms.FileField(
        label="Planilha (.xlsx ou .csv)",
        widget=forms.ClearableFileInput(attrs={"accept": ".xlsx,.csv"}),
    )


class ConvidadoManualForm(forms.ModelForm):
    class Meta:
        model = ConvidadoLista
        fields = ["nome", "telefone", "quantidade_esperada", "grupo", "observacoes"]
        widgets = {
            "nome": forms.TextInput(attrs={"placeholder": "Nome completo"}),
            "telefone": forms.TextInput(attrs={"placeholder": "(00) 00000-0000"}),
            "grupo": forms.TextInput(attrs={"placeholder": "Ex: Família da noiva"}),
            "observacoes": forms.TextInput(attrs={"placeholder": "Opcional"}),
        }
