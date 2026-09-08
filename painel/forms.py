from django import forms

from .models import ConvidadoLista
from convite.models import Presente

class PresenteForm(forms.ModelForm):
    class Meta:
        model = Presente
        fields = ["titulo", "valor", "chave_pix", "imagem", "icone", "disponivel"]
        widgets = {
            "titulo": forms.TextInput(attrs={"class": "border border-stone-200 rounded px-3 py-2 text-sm w-full", "placeholder": "Ex: Geladeira"}),
            "chave_pix": forms.TextInput(attrs={"class": "border border-stone-200 rounded px-3 py-2 text-sm w-full", "placeholder": "Sua chave PIX"}),
            "valor": forms.NumberInput(attrs={"class": "border border-stone-200 rounded px-3 py-2 text-sm w-full", "placeholder": "Valor R$ (Opcional)"}),
            "icone": forms.TextInput(attrs={"class": "border border-stone-200 rounded px-3 py-2 text-sm w-full", "placeholder": "Ícone lucide (Opcional)"}),
            "imagem": forms.FileInput(attrs={
                "class": "block w-full text-sm text-stone-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-stone-100 file:text-[#8A1538] hover:file:bg-stone-200 cursor-pointer"
            }),
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
