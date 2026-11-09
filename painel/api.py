"""
API JSON do painel para integrar com bots/sistemas externos.

Autenticação: header "Authorization: Bearer <PAINEL_API_TOKEN>".
Avisos de nova confirmação: se PAINEL_WEBHOOK_URL estiver configurada, cada
RSVP novo é enviado por POST para ela (ver painel/signals.py).
"""
import hmac
import json
from functools import wraps

from django.conf import settings
from django.http import JsonResponse
from django.utils.dateparse import parse_datetime
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from convite.models import RSVP

from .models import ConvidadoLista
from .relatorio import montar_lista


def requer_token(view):
    @csrf_exempt
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        token = settings.PAINEL_API_TOKEN
        if not token:
            return JsonResponse({"erro": "API desativada: defina PAINEL_API_TOKEN no servidor."}, status=503)
        enviado = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
        if not hmac.compare_digest(enviado.encode(), token.encode()):
            return JsonResponse({"erro": "Token inválido."}, status=401)
        return view(request, *args, **kwargs)
    return wrapper


def rsvp_json(r):
    return {
        "id": r.pk,
        "nome": r.nome_completo,
        "telefone": r.telefone,
        "quantidade": r.quantidade_convidados,
        "mensagem": r.mensagem,
        "criado_em": r.criado_em.isoformat(),
    }


def linha_json(l):
    c = l["obj"]
    return {
        "id": c.pk,
        "nome": c.nome,
        "telefone": c.telefone,
        "grupo": c.grupo,
        "observacoes": c.observacoes,
        "quantidade_esperada": c.quantidade_esperada,
        "quantidade_confirmada": l["qtd_confirmada"],
        "faltam": l["faltam"],
        "confirmado": l["confirmado"],
        "confirmacoes_site": [rsvp_json(r) for r in l["rsvps_todos"]],
    }


def resumo(linhas, sem_vinculo):
    confirmados = [l for l in linhas if l["confirmado"]]
    return {
        "convites": len(linhas),
        "convites_confirmados": len(confirmados),
        "convites_pendentes": len(linhas) - len(confirmados),
        "pessoas_esperadas": sum(l["obj"].quantidade_esperada for l in linhas),
        "pessoas_confirmadas": sum(l["qtd_confirmada"] for l in confirmados),
        "pessoas_faltando": sum(l["faltam"] for l in linhas),
        "confirmacoes_sem_vinculo": len(sem_vinculo),
    }


@requer_token
@require_http_methods(["GET"])
def api_resumo(request):
    return JsonResponse(resumo(*montar_lista()))


@requer_token
@require_http_methods(["GET", "POST"])
def api_convidados(request):
    if request.method == "POST":
        try:
            dados = json.loads(request.body or b"{}")
        except ValueError:
            return JsonResponse({"erro": "JSON inválido."}, status=400)
        nome = str(dados.get("nome") or "").strip()
        if not nome:
            return JsonResponse({"erro": "Campo 'nome' é obrigatório."}, status=400)
        try:
            quantidade = max(int(dados.get("quantidade_esperada") or 1), 1)
        except (TypeError, ValueError):
            return JsonResponse({"erro": "'quantidade_esperada' deve ser um número."}, status=400)
        c = ConvidadoLista.objects.create(
            nome=nome[:150],
            telefone=str(dados.get("telefone") or "")[:30],
            quantidade_esperada=quantidade,
            grupo=str(dados.get("grupo") or "")[:100],
            observacoes=str(dados.get("observacoes") or ""),
        )
        linha = next(l for l in montar_lista()[0] if l["obj"].pk == c.pk)
        return JsonResponse(linha_json(linha), status=201)

    linhas, _ = montar_lista()
    status = request.GET.get("status")
    if status == "confirmados":
        linhas = [l for l in linhas if l["confirmado"]]
    elif status == "pendentes":
        linhas = [l for l in linhas if not l["confirmado"]]
    elif status == "faltando":
        linhas = [l for l in linhas if l["faltam"]]
    return JsonResponse({"convidados": [linha_json(l) for l in linhas]})


@requer_token
@require_http_methods(["GET", "DELETE"])
def api_convidado(request, pk):
    c = ConvidadoLista.objects.filter(pk=pk).first()
    if not c:
        return JsonResponse({"erro": "Convidado não encontrado."}, status=404)
    if request.method == "DELETE":
        c.delete()
        return JsonResponse({"removido": pk})
    linha = next(l for l in montar_lista()[0] if l["obj"].pk == pk)
    return JsonResponse(linha_json(linha))


@requer_token
@require_http_methods(["GET"])
def api_confirmacoes(request):
    rsvps = RSVP.objects.order_by("-criado_em")
    desde = request.GET.get("desde")
    if desde:
        dt = parse_datetime(desde)
        if dt is None:
            return JsonResponse({"erro": "'desde' deve estar em ISO 8601, ex: 2026-11-09T10:00:00-03:00."}, status=400)
        rsvps = rsvps.filter(criado_em__gt=dt)
    return JsonResponse({"confirmacoes": [rsvp_json(r) for r in rsvps]})
