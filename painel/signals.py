import json
import logging
import threading
import urllib.request

from django.conf import settings
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from convite.models import RSVP

logger = logging.getLogger(__name__)


def _enviar(url, corpo):
    req = urllib.request.Request(url, data=corpo, method="POST", headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.PAINEL_API_TOKEN}",
    })
    try:
        urllib.request.urlopen(req, timeout=10).close()
    except Exception:
        logger.exception("Falha ao enviar aviso de confirmação para %s", url)


@receiver(post_save, sender=RSVP)
def avisar_confirmacao(sender, instance, created, **kwargs):
    """Avisa o bot externo (PAINEL_WEBHOOK_URL) sempre que alguém confirma pelo site."""
    url = settings.PAINEL_WEBHOOK_URL
    if not created or not url:
        return

    def disparar():
        from .api import linha_json, resumo, rsvp_json
        from .relatorio import montar_lista

        linhas, sem_vinculo = montar_lista()
        convite = next((l for l in linhas if instance in l["rsvps_todos"]), None)
        corpo = json.dumps({
            "evento": "confirmacao",
            "confirmacao": rsvp_json(instance),
            "convite": linha_json(convite) if convite else None,
            "resumo": resumo(linhas, sem_vinculo),
        }).encode()
        threading.Thread(target=_enviar, args=(url, corpo), daemon=True).start()

    transaction.on_commit(disparar)
