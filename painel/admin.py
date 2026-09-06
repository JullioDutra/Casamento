from django.contrib import admin

from .models import ConvidadoLista


@admin.register(ConvidadoLista)
class ConvidadoListaAdmin(admin.ModelAdmin):
    list_display = ("nome", "telefone", "quantidade_esperada", "grupo", "confirmado_manual")
    list_editable = ("confirmado_manual",)
    list_filter = ("grupo", "confirmado_manual")
    search_fields = ("nome", "telefone")
