from django.db import models


class ConvidadoLista(models.Model):
    """
    Lista mestre de convidados dos noivos — importada da planilha deles ou
    cadastrada manualmente. É comparada com os RSVPs recebidos pelo site
    para indicar quem já confirmou e quem ainda falta confirmar.
    """
    nome = models.CharField("Nome do convidado", max_length=150)
    telefone = models.CharField("Telefone", max_length=30, blank=True)
    quantidade_esperada = models.PositiveSmallIntegerField(
        "Quantidade esperada", default=1,
        help_text="Quantas pessoas esse convidado deve trazer (incluindo ele mesmo).",
    )
    grupo = models.CharField(
        "Grupo", max_length=100, blank=True,
        help_text="Ex: Família da noiva, Família do noivo, Amigos, Trabalho.",
    )
    observacoes = models.TextField("Observações", blank=True)
    confirmado_manual = models.BooleanField(
        "Confirmado manualmente pelos noivos", default=False,
        help_text="Marque se o convidado confirmou por fora do site (WhatsApp, telefone etc).",
    )
    criado_em = models.DateTimeField("Adicionado em", auto_now_add=True)

    class Meta:
        ordering = ["nome"]
        verbose_name = "Convidado da lista"
        verbose_name_plural = "Lista de convidados"

    def __str__(self):
        return self.nome
