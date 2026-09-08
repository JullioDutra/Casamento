import csv
import difflib
import io

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from convite.models import RSVP

from .forms import ConvidadoManualForm, UploadPlanilhaForm, PresenteForm
from .models import ConvidadoLista
from .utils import normalizar_nome

try:
    import openpyxl
except ImportError:  # pragma: no cover
    openpyxl = None


def nomes_similares(nome1, nome2):
    """
    Retorna True se os nomes forem pelo menos 80% parecidos ou se um contiver o outro.
    Útil para não duplicar confirmações quando há erros de digitação (ex: Ana Maria x Ana Mria).
    """
    if not nome1 or not nome2:
        return False
    if nome1 in nome2 or nome2 in nome1:
        return True
    return difflib.SequenceMatcher(None, nome1, nome2).ratio() > 0.8


@login_required
def dashboard(request):
    busca = request.GET.get("busca", "").strip()
    status_filtro = request.GET.get("status", "todos")
    page_number = request.GET.get("page", 1)

    rsvps = RSVP.objects.all().order_by("-criado_em")
    total_pessoas_confirmadas_site = sum(r.quantidade_convidados for rsvps)

    # Pré-computar nomes normalizados dos RSVPs para otimizar o laço
    rsvps_normalizados = [(normalizar_nome(r.nome_completo), r) for r in rsvps]

    linhas = []
    for c in ConvidadoLista.objects.all():
        nome_c_norm = normalizar_nome(c.nome)
        
        # Encontra o primeiro RSVP que dê 'match' usando a função flexível
        rsvp_correspondente = next(
            (r for r_nome_norm, r in rsvps_normalizados if nomes_similares(nome_c_norm, r_nome_norm)), 
            None
        )
        
        confirmado = c.confirmado_manual or rsvp_correspondente is not None
        linhas.append({"obj": c, "confirmado": confirmado, "rsvp": rsvp_correspondente})

    total_lista = len(linhas)
    total_confirmados = sum(1 for l in linhas if l["confirmado"])
    total_pendentes = total_lista - total_confirmados
    total_pessoas_esperadas = sum(l["obj"].quantidade_esperada for l in linhas)
    percentual = round((total_confirmados / total_lista) * 100) if total_lista else 0

    exibir = linhas
    if status_filtro == "confirmados":
        exibir = [l for l in exibir if l["confirmado"]]
    elif status_filtro == "pendentes":
        exibir = [l for l in exibir if not l["confirmado"]]
    if busca:
        busca_norm = normalizar_nome(busca)
        exibir = [l for l in exibir if busca_norm in normalizar_nome(l["obj"].nome)]
    
    exibir.sort(key=lambda l: l["obj"].nome)

    # Paginação de 30 itens por página
    paginator = Paginator(exibir, 30)
    page_obj = paginator.get_page(page_number)

    context = {
        "linhas": page_obj,  # Substituímos a lista completa pela página atual (HTML continua funcionando)
        "page_obj": page_obj, # Enviado para renderizar os botões Anterior/Próxima
        "rsvps": rsvps,
        "total_lista": total_lista,
        "total_confirmados": total_confirmados,
        "total_pendentes": total_pendentes,
        "total_pessoas_esperadas": total_pessoas_esperadas,
        "total_pessoas_confirmadas_site": total_pessoas_confirmadas_site,
        "percentual": percentual,
        "upload_form": UploadPlanilhaForm(),
        "manual_form": ConvidadoManualForm(),
        "presente_form": PresenteForm(), # Form que será renderizado no seu modal/card
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
    idx_qtd = indice("quantidade", "qtd", "acompanhantes", "pessoas")
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

        novos.append(ConvidadoLista(
            nome=nome, telefone=telefone,
            quantidade_esperada=quantidade or 1, grupo=grupo,
        ))
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
        form.save()
        messages.success(request, "Convidado adicionado à lista.")
    else:
        messages.error(request, "Verifique os campos e tente novamente.")
    return redirect("painel:dashboard")


@login_required
@require_POST
def alternar_confirmado(request, pk):
    convidado = get_object_or_404(ConvidadoLista, pk=pk)
    convidado.confirmado_manual = not convidado.confirmado_manual
    convidado.save()
    return redirect("painel:dashboard")


@login_required
@require_POST
def excluir_convidado(request, pk):
    convidado = get_object_or_404(ConvidadoLista, pk=pk)
    convidado.delete()
    messages.success(request, "Convidado removido da lista.")
    return redirect("painel:dashboard")


@login_required
@require_POST
def adicionar_presente(request):
    form = PresenteForm(request.POST, request.FILES)
    if form.is_valid():
        form.save()
        messages.success(request, "Presente adicionado com sucesso à lista de presentes.")
    else:
        messages.error(request, "Não foi possível adicionar o presente. Verifique os campos.")
    return redirect("painel:dashboard")
