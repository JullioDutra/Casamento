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


class VinculoRSVP(models.Model):
    """
    Vincula uma confirmação do site (RSVP) a um convite da lista mestre.
    Útil quando quem confirmou não está na lista com o próprio nome (ex: o
    convite está no nome da mãe e o filho confirmou) — a confirmação passa a
    contar dentro daquele convite.
    """
    rsvp = models.OneToOneField(
        "convite.RSVP", on_delete=models.CASCADE, related_name="vinculo",
        verbose_name="Confirmação do site",
    )
    convidado = models.ForeignKey(
        ConvidadoLista, on_delete=models.CASCADE, related_name="vinculos",
        verbose_name="Convite da lista",
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Vínculo de confirmação"
        verbose_name_plural = "Vínculos de confirmações"

    def __str__(self):
        return f"{self.rsvp.nome_completo} → {self.convidado.nome}"
