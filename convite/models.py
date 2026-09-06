from django.core.exceptions import ValidationError
from django.db import models


class Evento(models.Model):
    """
    Dados gerais do casamento. Pensado como singleton: deve existir
    apenas um registro (ver admin.py, que bloqueia criação de um segundo).
    """
    nome_noivo = models.CharField("Nome do noivo", max_length=100, default="Jullio Cesar")
    nome_noiva = models.CharField("Nome da noiva", max_length=100, default="Gabriella")
    iniciais = models.CharField("Iniciais (monograma)", max_length=5, default="JG")

    data_hora = models.DateTimeField("Data e hora da cerimônia")
    traje = models.CharField("Traje", max_length=100, default="Esporte Fino")

    versiculo_texto = models.TextField(
        "Texto do versículo",
        default="Assim, eles já não são dois, mas sim uma só carne. "
                "Portanto, o que Deus uniu ninguém separe.",
    )
    versiculo_referencia = models.CharField(
        "Referência do versículo", max_length=50, default="Mateus 19:6"
    )

    mensagem_convite = models.TextField(
        "Texto de abertura do convite",
        default="Temos a alegria de convidar você para celebrar conosco o dia em que "
                "uniremos nossas vidas diante do altar do Senhor, recebendo o "
                "Sacramento do Matrimônio.",
    )
    mensagem_final = models.TextField(
        "Mensagem final dos noivos",
        default="Mais do que celebrar um casamento, queremos celebrar a fidelidade de "
                "Deus em nossas vidas. A presença de cada pessoa torna este momento "
                "ainda mais especial. Obrigado por fazer parte da nossa história.",
    )

    nome_recebedor_pix = models.CharField(
        "Nome do recebedor (para o PIX)", max_length=25, default="NOIVOS",
        help_text="Máximo 25 caracteres. É o nome que aparece no app do banco de quem for pagar.",
    )
    cidade_pix = models.CharField(
        "Cidade (para o PIX)", max_length=15, default="BRASIL",
        help_text="Máximo 15 caracteres. Prefira sem acentos, ex: ANAPOLIS.",
    )

    permitir_fotos_convidados = models.BooleanField(
        "Permitir que convidados enviem fotos da cerimônia", default=False,
        help_text="Quando ativado, exibe um botão na seção da cerimônia para os "
                  "convidados subirem suas próprias fotos do evento.",
    )

    def clean(self):
        if not self.pk and Evento.objects.exists():
            raise ValidationError(
                "Já existe um evento cadastrado. Edite o registro existente "
                "em vez de criar um novo."
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nome_noivo} & {self.nome_noiva} — {self.data_hora:%d/%m/%Y}"

    class Meta:
        verbose_name = "Evento"
        verbose_name_plural = "Evento"


class Local(models.Model):
    TIPO_CHOICES = [
        ("data", "Data"),
        ("horario", "Horário"),
        ("local", "Local / Endereço"),
        ("traje", "Traje"),
        ("outro", "Outro"),
    ]
    SUBTIPO_LOCAL_CHOICES = [
        ("", "—"),
        ("cerimonia", "Cerimônia"),
        ("recepcao", "Recepção"),
    ]

    evento = models.ForeignKey(Evento, on_delete=models.CASCADE, related_name="locais")
    tipo = models.CharField("Tipo", max_length=20, choices=TIPO_CHOICES, default="local")
    subtipo_local = models.CharField(
        "Subtipo (apenas quando Tipo = Local)", max_length=20,
        choices=SUBTIPO_LOCAL_CHOICES, blank=True, default="",
        help_text="Preencha só quando Tipo = 'Local / Endereço' e houver mais de um "
                  "endereço (cerimônia e recepção), para diferenciar os botões "
                  "'Ver Localização'.",
    )
    icone = models.CharField(
        "Ícone (nome do lucide-icons)", max_length=50, default="map-pin",
        help_text="Nome de um ícone válido em lucide.dev (ex: calendar-days, clock, map-pin, user)",
    )
    titulo = models.CharField("Título do card", max_length=100, help_text="Ex: Local, Data, Horário")
    descricao = models.CharField("Descrição / valor", max_length=200, help_text="Ex: Paróquia São José Operário")
    link_maps = models.URLField("Link do Google Maps", blank=True)
    ordem = models.PositiveIntegerField("Ordem", default=0)

    class Meta:
        ordering = ["ordem"]
        verbose_name = "Local / Informação da cerimônia"
        verbose_name_plural = "Locais / Informações da cerimônia"

    def __str__(self):
        return f"{self.titulo}: {self.descricao}"


class Presente(models.Model):
    titulo = models.CharField("Título", max_length=100)
    descricao = models.TextField("Descrição", blank=True)
    valor = models.DecimalField(
        "Valor (R$)", max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="Deixe em branco para exibir 'Valor Livre'.",
    )
    icone = models.CharField(
        "Ícone (lucide-icons)", max_length=50, default="gift",
        help_text="Ex: utensils-crossed, plane, refrigerator, table-2, armchair, luggage",
    )
    imagem = models.ImageField("Foto do presente", upload_to="presentes/", blank=True, null=True)
    chave_pix = models.CharField("Chave PIX", max_length=140)
    disponivel = models.BooleanField("Disponível para presentear", default=True)
    ordem = models.PositiveIntegerField("Ordem de exibição", default=0)

    class Meta:
        ordering = ["ordem", "titulo"]
        verbose_name = "Presente"
        verbose_name_plural = "Lista de presentes"

    def __str__(self):
        return self.titulo

    @property
    def valor_exibicao(self):
        if self.valor is None:
            return "Valor Livre"
        return f"R$ {self.valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


class Presenteador(models.Model):
    """Registro de quem confirmou intenção de presentear (nome informado no modal do PIX)."""
    presente = models.ForeignKey(Presente, on_delete=models.CASCADE, related_name="presenteadores")
    nome = models.CharField("Nome de quem presenteou", max_length=150)
    criado_em = models.DateTimeField("Registrado em", auto_now_add=True)

    class Meta:
        ordering = ["-criado_em"]
        verbose_name = "Registro de presente"
        verbose_name_plural = "Registros de quem presenteou"

    def __str__(self):
        return f"{self.nome} → {self.presente.titulo}"


class FotoGaleria(models.Model):
    imagem = models.ImageField("Foto", upload_to="galeria/")
    legenda = models.CharField("Legenda", max_length=100, blank=True)
    ordem = models.PositiveIntegerField("Ordem", default=0)

    class Meta:
        ordering = ["ordem"]
        verbose_name = "Foto da galeria"
        verbose_name_plural = "Fotos da galeria"

    def __str__(self):
        return self.legenda or f"Foto {self.pk}"


class FotoConvidado(models.Model):
    """Fotos enviadas pelos próprios convidados (visível na área do admin para moderação)."""
    nome_convidado = models.CharField("Nome do convidado", max_length=150, blank=True)
    imagem = models.ImageField("Foto", upload_to="fotos_convidados/")
    criado_em = models.DateTimeField("Enviada em", auto_now_add=True)
    aprovada = models.BooleanField(
        "Aprovada para exibir na galeria pública", default=False,
        help_text="Marque para essa foto passar a aparecer na galeria do site.",
    )

    class Meta:
        ordering = ["-criado_em"]
        verbose_name = "Foto enviada por convidado"
        verbose_name_plural = "Fotos enviadas por convidados"

    def __str__(self):
        return self.nome_convidado or f"Foto convidado {self.pk}"


class RSVP(models.Model):
    nome_completo = models.CharField("Nome completo", max_length=150)
    telefone = models.CharField("Telefone", max_length=30)
    quantidade_convidados = models.PositiveSmallIntegerField("Quantidade de convidados", default=1)
    mensagem = models.TextField("Mensagem para os noivos", blank=True)
    criado_em = models.DateTimeField("Enviado em", auto_now_add=True)

    class Meta:
        ordering = ["-criado_em"]
        verbose_name = "Confirmação de presença"
        verbose_name_plural = "Confirmações de presença (RSVP)"

    def __str__(self):
        return f"{self.nome_completo} ({self.quantidade_convidados} pessoa(s))"
