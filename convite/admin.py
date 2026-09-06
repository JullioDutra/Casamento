from django.contrib import admin

from .models import (
    Evento,
    FotoConvidado,
    FotoGaleria,
    Local,
    Presente,
    Presenteador,
    RSVP,
)


class LocalInline(admin.TabularInline):
    model = Local
    extra = 1
    fields = ("tipo", "subtipo_local", "icone", "titulo", "descricao", "link_maps", "ordem")


@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    inlines = [LocalInline]
    fieldsets = (
        ("Nomes e data", {
            "fields": ("nome_noivo", "nome_noiva", "iniciais", "data_hora", "traje"),
        }),
        ("Versículo", {
            "fields": ("versiculo_texto", "versiculo_referencia"),
        }),
        ("Textos do convite", {
            "fields": ("mensagem_convite", "mensagem_final"),
        }),
        ("Dados para o PIX (QR Code)", {
            "fields": ("nome_recebedor_pix", "cidade_pix"),
            "description": "Usados para montar o QR Code PIX de cada presente.",
        }),
        ("Fotos enviadas por convidados", {
            "fields": ("permitir_fotos_convidados",),
        }),
    )

    def has_add_permission(self, request):
        # Só permite criar o Evento se ainda não existir nenhum (singleton)
        return not Evento.objects.exists()


@admin.register(Local)
class LocalAdmin(admin.ModelAdmin):
    list_display = ("titulo", "descricao", "tipo", "subtipo_local", "ordem")
    list_editable = ("ordem",)
    list_filter = ("tipo", "subtipo_local")
    ordering = ("ordem",)


class PresenteadorInline(admin.TabularInline):
    model = Presenteador
    extra = 0
    fields = ("nome", "criado_em")
    readonly_fields = ("nome", "criado_em")
    can_delete = False
    verbose_name_plural = "Quem já presenteou (registrado automaticamente)"

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Presente)
class PresenteAdmin(admin.ModelAdmin):
    list_display = ("titulo", "valor", "chave_pix", "disponivel", "ordem", "total_presenteadores")
    list_editable = ("disponivel", "ordem")
    list_filter = ("disponivel",)
    search_fields = ("titulo", "chave_pix")
    ordering = ("ordem",)
    inlines = [PresenteadorInline]

    @admin.display(description="Presenteadores")
    def total_presenteadores(self, obj):
        return obj.presenteadores.count()


@admin.register(Presenteador)
class PresenteadorAdmin(admin.ModelAdmin):
    list_display = ("nome", "presente", "criado_em")
    list_filter = ("presente",)
    search_fields = ("nome",)
    readonly_fields = ("presente", "nome", "criado_em")

    def has_add_permission(self, request):
        return False


@admin.register(FotoGaleria)
class FotoGaleriaAdmin(admin.ModelAdmin):
    list_display = ("legenda", "ordem")
    list_editable = ("ordem",)
    ordering = ("ordem",)


@admin.register(FotoConvidado)
class FotoConvidadoAdmin(admin.ModelAdmin):
    list_display = ("nome_convidado", "criado_em", "aprovada")
    list_editable = ("aprovada",)
    list_filter = ("aprovada",)
    search_fields = ("nome_convidado",)


@admin.register(RSVP)
class RSVPAdmin(admin.ModelAdmin):
    list_display = ("nome_completo", "telefone", "quantidade_convidados", "criado_em")
    readonly_fields = ("criado_em",)
    search_fields = ("nome_completo", "telefone")
    list_filter = ("criado_em",)
