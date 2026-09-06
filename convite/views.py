from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST

from .forms import FotoConvidadoForm, RSVPForm
from .models import Evento, FotoGaleria, Local, Presente, Presenteador
from .pix import gerar_payload_pix, gerar_qrcode_base64


def home(request):
    evento = Evento.objects.prefetch_related("locais").first()
    locais = Local.objects.filter(evento=evento).order_by("ordem") if evento else []
    presentes = Presente.objects.filter(disponivel=True).order_by("ordem", "titulo")
    fotos = FotoGaleria.objects.all().order_by("ordem")
    form = RSVPForm()
    foto_form = FotoConvidadoForm()

    context = {
        "evento": evento,
        "locais": locais,
        "presentes": presentes,
        "fotos": fotos,
        "form": form,
        "foto_form": foto_form,
    }
    return render(request, "convite/home.html", context)


@require_POST
def rsvp_submit(request):
    """
    Recebe o envio do formulário de RSVP via fetch/AJAX e responde em JSON,
    para o front trocar o formulário pela mensagem de sucesso sem recarregar
    a página (mesmo comportamento do site original).
    """
    form = RSVPForm(request.POST)
    if form.is_valid():
        form.save()
        return JsonResponse({"ok": True})
    return JsonResponse({"ok": False, "errors": form.errors}, status=400)


@require_POST
def presente_pix(request, pk):
    """
    Registra o nome de quem está presenteando e gera, na hora, o QR Code
    PIX real (payload EMV/BR Code) para aquele presente específico.
    """
    presente = get_object_or_404(Presente, pk=pk, disponivel=True)
    nome = request.POST.get("nome_presenteador", "").strip()
    if not nome:
        return JsonResponse(
            {"ok": False, "erro": "Informe seu nome para gerar o QR Code."}, status=400
        )

    Presenteador.objects.create(presente=presente, nome=nome)

    evento = Evento.objects.first()
    nome_recebedor = evento.nome_recebedor_pix if evento else "NOIVOS"
    cidade = evento.cidade_pix if evento else "BRASIL"

    payload = gerar_payload_pix(
        chave=presente.chave_pix,
        nome_recebedor=nome_recebedor,
        cidade=cidade,
        valor=presente.valor,
        descricao=presente.titulo,
    )
    qrcode_base64 = gerar_qrcode_base64(payload)

    return JsonResponse({
        "ok": True,
        "titulo": presente.titulo,
        "chave_pix": presente.chave_pix,
        "qrcode_base64": qrcode_base64,
    })


@require_POST
def foto_convidado_upload(request):
    """
    Recebe uma foto enviada por um convidado. Só aceita o envio se o
    campo `permitir_fotos_convidados` do Evento estiver ativado no admin.
    As fotos ficam pendentes de aprovação (campo `aprovada`) antes de
    aparecerem publicamente.
    """
    evento = Evento.objects.first()
    if not evento or not evento.permitir_fotos_convidados:
        return JsonResponse(
            {"ok": False, "erro": "O envio de fotos não está disponível no momento."},
            status=403,
        )

    form = FotoConvidadoForm(request.POST, request.FILES)
    if form.is_valid():
        form.save()
        return JsonResponse({"ok": True})
    return JsonResponse({"ok": False, "errors": form.errors}, status=400)
