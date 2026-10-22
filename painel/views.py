import csv
import io
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from convite.models import Presente, Presenteador, RSVP

from .forms import ConvidadoManualForm, PresenteForm, UploadPlanilhaForm
from .models import ConvidadoLista, VinculoRSVP
from .relatorio import gerar_pdf, montar_lista
from .utils import normalizar_nome

try:
    import openpyxl
except ImportError:  # pragma: no cover
    openpyxl = None


@login_required
def dashboard(request):
    busca = request.GET.get("busca", "").strip()
    status_filtro = request.GET.get("status", "todos")
    page_number = request.GET.get("page", 1)

    rsvps = RSVP.objects.select_related("vinculo__convidado").order_by("-criado_em")
    linhas, rsvps_sem_vinculo = montar_lista()

    total_pessoas_confirmadas = sum(l["qtd_confirmada"] for l in linhas if l["confirmado"])
    total_lista = len(linhas)
    total_confirmados_familias = sum(1 for l in linhas if l["confirmado"])
    total_pendentes = total_lista - total_confirmados_familias
    total_pessoas_esperadas = sum(l["obj"].quantidade_esperada for l in linhas)
    total_pessoas_faltando = sum(l["faltam"] for l in linhas)
    percentual = round((total_confirmados_familias / total_lista) * 100) if total_lista else 0

    exibir = linhas
    if status_filtro == "confirmados":
        exibir = [l for l in exibir if l["confirmado"]]
    elif status_filtro == "pendentes":
        exibir = [l for l in exibir if not l["confirmado"]]
    if busca:
        busca_norm = normalizar_nome(busca)
        exibir = [
            l for l in exibir
            if busca_norm in normalizar_nome(l["obj"].nome)
            or busca_norm in normalizar_nome(getattr(l["obj"], "grupo", "") or "")
            or busca_norm in normalizar_nome(getattr(l["obj"], "observacoes", "") or "")
        ]

    exibir.sort(key=lambda l: l["obj"].nome)

    # Paginação de 30 itens por página
    paginator = Paginator(exibir, 30)
    page_obj = paginator.get_page(page_number)

    # --- DADOS DE PRESENTES RECEBIDOS E CATÁLOGO ---
    presentes_recebidos = Presenteador.objects.select_related("presente").all()
    catalogo_presentes = Presente.objects.prefetch_related("presenteadores").all()

    total_valor_presentes = sum(
        (p.presente.valor or Decimal("0.00")) for p in presentes_recebidos
    )

    # Sugere automaticamente o próximo número na sequência de exibição
    ultima_ordem = (
        Presente.objects.order_by("-ordem").values_list("ordem", flat=True).first()
    )
    proxima_ordem = (ultima_ordem + 1) if ultima_ordem is not None else 1

    context = {
        "linhas": page_obj,  # Enviado para não quebrar templates antigos (se houver)
        "page_obj": page_obj,
        "rsvps": rsvps,
        "total_lista": total_lista,
        "total_confirmados_familias": total_confirmados_familias,
        "total_pessoas_confirmadas": total_pessoas_confirmadas,
        "total_pendentes": total_pendentes,
        "total_pessoas_esperadas": total_pessoas_esperadas,
        "total_pessoas_faltando": total_pessoas_faltando,
        "rsvps_sem_vinculo": rsvps_sem_vinculo,
        "convites_lista": ConvidadoLista.objects.all(),
        "percentual": percentual,
        "upload_form": UploadPlanilhaForm(),
        "manual_form": ConvidadoManualForm(),
        "presente_form": PresenteForm(initial={"disponivel": True, "ordem": proxima_ordem}),
        "presentes_recebidos": presentes_recebidos,
        "catalogo_presentes": catalogo_presentes,
        "total_valor_presentes": total_valor_presentes,
        "busca": busca,
        "status_filtro": status_filtro,
    }
    return render(request, "painel/dashboard.html", context)


@login_required
@require_POST
def upload_planilha(request):
    form = UploadPlanilhaForm(request.POST, request.FILES)
    if not form.is_valid():
        messages.error(request, "Selecione um arquivo válido (.xlsx ou .csv).")
        return redirect("painel:dashboard")

    arquivo = form.cleaned_data["arquivo"]
    nome_arquivo = arquivo.name.lower()

    try:
        if nome_arquivo.endswith(".csv"):
            conteudo = arquivo.read().decode("utf-8-sig")
            linhas_raw = list(csv.reader(io.StringIO(conteudo)))
        elif nome_arquivo.endswith(".xlsx"):
            if openpyxl is None:
                messages.error(request, "Suporte a .xlsx não está instalado no servidor.")
                return redirect("painel:dashboard")
            planilha = openpyxl.load_workbook(arquivo, data_only=True)
            aba = planilha.active
            linhas_raw = [list(linha) for linha in aba.iter_rows(values_only=True)]
        else:
            messages.error(request, "Formato não suportado. Envie um arquivo .xlsx ou .csv.")
            return redirect("painel:dashboard")
    except Exception:
        messages.error(request, "Não foi possível ler o arquivo. Confira se o formato está correto.")
        return redirect("painel:dashboard")

    if not linhas_raw:
        messages.warning(request, "A planilha está vazia.")
        return redirect("painel:dashboard")

    cabecalho = [str(c).strip().lower() if c else "" for c in linhas_raw[0]]

    def indice(*nomes_possiveis):
        for nome in nomes_possiveis:
            if nome in cabecalho:
                return cabecalho.index(nome)
        return None

    idx_nome = indice("nome", "convidado", "nome completo")
    idx_telefone = indice("telefone", "celular", "contato")
    idx_qtd = indice("quantidade", "qtd", "acompanhantes", "pessoas", "quantidade_esperada")
    idx_grupo = indice("grupo", "categoria")

    if idx_nome is None:
        messages.error(
            request,
            "A planilha precisa ter uma coluna chamada 'Nome' na primeira linha.",
        )
        return redirect("painel:dashboard")

    nomes_existentes = {normalizar_nome(c.nome) for c in ConvidadoLista.objects.all()}
    novos = []
    importados = 0
    ignorados = 0

    for linha in linhas_raw[1:]:
        if idx_nome >= len(linha):
            continue
        nome = str(linha[idx_nome] or "").strip()
        if not nome:
            continue
        if normalizar_nome(nome) in nomes_existentes:
            ignorados += 1
            continue

        telefone = ""
        if idx_telefone is not None and idx_telefone < len(linha) and linha[idx_telefone]:
            telefone = str(linha[idx_telefone]).strip()

        quantidade = 1
        if idx_qtd is not None and idx_qtd < len(linha) and linha[idx_qtd]:
            try:
                quantidade = int(float(linha[idx_qtd]))
            except (ValueError, TypeError):
                quantidade = 1

        grupo = ""
        if idx_grupo is not None and idx_grupo < len(linha) and linha[idx_grupo]:
            grupo = str(linha[idx_grupo]).strip()

        novos.append(
            ConvidadoLista(
                nome=nome,
                telefone=telefone,
                quantidade_esperada=quantidade or 1,
                grupo=grupo,
            )
        )
        nomes_existentes.add(normalizar_nome(nome))
        importados += 1

    ConvidadoLista.objects.bulk_create(novos)

    if importados:
        messages.success(request, f"{importados} convidado(s) importado(s) com sucesso.")
    if ignorados:
        messages.info(request, f"{ignorados} nome(s) já estavam na lista e foram ignorados.")
    if not importados and not ignorados:
        messages.warning(request, "Nenhum convidado válido foi encontrado na planilha.")

    return redirect("painel:dashboard")


@login_required
def baixar_modelo_planilha(request):
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="modelo_lista_convidados.csv"'
    writer = csv.writer(response)
    writer.writerow(["nome", "telefone", "quantidade", "grupo"])
    writer.writerow(["Maria Silva", "(62) 99999-0000", "2", "Família da noiva"])
    writer.writerow(["João Souza", "", "1", "Amigos"])
    return response


@login_required
@require_POST
def adicionar_convidado(request):
    form = ConvidadoManualForm(request.POST)
    if form.is_valid():
        convidado = form.save()
        messages.success(request, f"Convidado '{convidado.nome}' adicionado à lista.")
    else:
        messages.error(request, "Verifique os campos e tente novamente.")
    return redirect("painel:dashboard")


@login_required
@require_POST
def alternar_confirmado(request, pk):
    convidado = get_object_or_404(ConvidadoLista, pk=pk)
    convidado.confirmado_manual = not convidado.confirmado_manual
    convidado.save(update_fields=["confirmado_manual"])
    estado = "confirmado" if convidado.confirmado_manual else "pendente"
    messages.success(request, f"Status de '{convidado.nome}' alterado para {estado}.")
    return redirect("painel:dashboard")


@login_required
@require_POST
def excluir_convidado(request, pk):
    convidado = get_object_or_404(ConvidadoLista, pk=pk)
    nome = convidado.nome
    convidado.delete()
    messages.success(request, f"Convidado '{nome}' removido da lista.")
    return redirect("painel:dashboard")


@login_required
@require_POST
def adicionar_presente(request):
    # Aceita request.FILES para fazer o upload correto da imagem
    form = PresenteForm(request.POST, request.FILES)
    if form.is_valid():
        presente = form.save()
        status_txt = "ativo" if presente.disponivel else "oculto"
        messages.success(
            request,
            f"Presente '{presente.titulo}' adicionado na posição #{presente.ordem} ({status_txt}).",
        )
    else:
        messages.error(request, "Não foi possível adicionar o presente. Verifique os campos.")
    return redirect("painel:dashboard")


@login_required
@require_POST
def alternar_presente(request, pk):
    presente = get_object_or_404(Presente, pk=pk)
    presente.disponivel = not presente.disponivel
    presente.save(update_fields=["disponivel"])
    estado = "ativado no site" if presente.disponivel else "ocultado do site"
    messages.info(request, f"Presente '{presente.titulo}' foi {estado}.")
    return redirect("painel:dashboard")


@login_required
@require_POST
def excluir_presente(request, pk):
    presente = get_object_or_404(Presente, pk=pk)
    titulo = presente.titulo
    presente.delete()
    messages.success(request, f"Presente '{titulo}' removido da lista.")
    return redirect("painel:dashboard")


@login_required
@require_POST
def vincular_rsvp(request, pk):
    rsvp = get_object_or_404(RSVP, pk=pk)
    convidado = ConvidadoLista.objects.filter(pk=request.POST.get("convidado")).first()
    if not convidado:
        messages.error(request, "Escolha o convite da lista para vincular.")
        return redirect("painel:dashboard")
    VinculoRSVP.objects.update_or_create(rsvp=rsvp, defaults={"convidado": convidado})
    messages.success(
        request,
        f"'{rsvp.nome_completo}' ({rsvp.quantidade_convidados}) vinculado ao convite de '{convidado.nome}'.",
    )
    return redirect("painel:dashboard")


@login_required
@require_POST
def desvincular_rsvp(request, pk):
    vinculo = get_object_or_404(VinculoRSVP, rsvp_id=pk)
    nome = vinculo.rsvp.nome_completo
    vinculo.delete()
    messages.info(request, f"Vínculo de '{nome}' removido.")
    return redirect("painel:dashboard")


@login_required
def relatorio_pdf(request):
    linhas, sem_vinculo = montar_lista()
    response = HttpResponse(gerar_pdf(linhas, sem_vinculo), content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="relatorio_confirmacoes.pdf"'
    return response
