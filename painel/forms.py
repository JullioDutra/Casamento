from django import forms

from .models import ConvidadoLista


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
