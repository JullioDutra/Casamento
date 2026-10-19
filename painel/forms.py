from django import forms
from .models import ConvidadoLista
from convite.models import Presente



class UploadPlanilhaForm(forms.Form):
    arquivo = forms.FileField(
        label="Planilha (.xlsx ou .csv)",
        help_text="Colunas aceitas: nome, telefone, quantidade_esperada, grupo, confirmado, observacoes.",
        widget=forms.FileInput(attrs={
            "accept": ".xlsx,.csv",
            "class": "block w-full text-xs text-stone-600 file:mr-3 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-xs file:font-medium file:bg-[#8A1538] file:text-white hover:file:bg-[#71102d] cursor-pointer",
        }),
    )


class PresenteForm(forms.ModelForm):
    # Definimos initial=True para o checkbox já vir marcado como Ativo ao abrir o painel
    disponivel = forms.BooleanField(
        label="Ativo no site (Disponível para presentear)",
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            "class": "w-4 h-4 rounded text-[#8A1538] focus:ring-[#8A1538] border-stone-300 cursor-pointer"
        }),
    )

    class Meta:
        model = Presente
        fields = ["titulo", "valor", "icone", "chave_pix", "imagem", "ordem", "disponivel"]
        widgets = {
            "titulo": forms.TextInput(attrs={
                "placeholder": "Título (ex: Jantar Romântico)",
                "class": "border border-stone-200 rounded-lg px-3 py-2 text-sm w-full focus:border-[#8A1538] outline-none",
            }),
            "valor": forms.NumberInput(attrs={
                "placeholder": "Valor R$ (vazio = Valor Livre)",
                "step": "0.01",
                "class": "border border-stone-200 rounded-lg px-3 py-2 text-sm w-full focus:border-[#8A1538] outline-none",
            }),
            "icone": forms.TextInput(attrs={
                "placeholder": "Ícone (ex: gift, plane, utensils-crossed)",
                "class": "border border-stone-200 rounded-lg px-3 py-2 text-sm w-full focus:border-[#8A1538] outline-none",
            }),
            "chave_pix": forms.TextInput(attrs={
                "placeholder": "Chave PIX (CPF, e-mail, telefone ou aleatória)",
                "class": "border border-stone-200 rounded-lg px-3 py-2 text-sm w-full focus:border-[#8A1538] outline-none",
            }),
            "ordem": forms.NumberInput(attrs={
                "placeholder": "Sequência (ex: 1, 2, 3...)",
                "min": "0",
                "class": "border border-stone-200 rounded-lg px-3 py-2 text-sm w-full focus:border-[#8A1538] outline-none",
                "title": "Ordem em que o presente aparece no site (menor aparece primeiro)",
            }),
            "imagem": forms.FileInput(attrs={
                "accept": "image/*",
                "class": "block w-full text-xs text-stone-600 file:mr-3 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-xs file:bg-stone-200 file:text-stone-700 hover:file:bg-stone-300 cursor-pointer",
            }),
        }


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
