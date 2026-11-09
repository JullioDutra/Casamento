import json
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from convite.models import RSVP

from .models import ConvidadoLista, VinculoRSVP


class VinculoERelatorioTests(TestCase):
    def setUp(self):
        self.client.force_login(get_user_model().objects.create(username="admin"))
        self.mae = ConvidadoLista.objects.create(nome="Maria Souza", quantidade_esperada=5)
        ConvidadoLista.objects.create(nome="Pedro Pendente", quantidade_esperada=2)
        RSVP.objects.create(nome_completo="Maria Souza", telefone="1", quantidade_convidados=2)
        self.filha = RSVP.objects.create(nome_completo="Joana Filha", telefone="2", quantidade_convidados=1)

    def test_rsvp_sem_vinculo_e_vinculo_conta_no_convite(self):
        r = self.client.get(reverse("painel:dashboard"))
        self.assertEqual(r.status_code, 200)
        self.assertEqual([x.pk for x in r.context["rsvps_sem_vinculo"]], [self.filha.pk])
        self.assertEqual(r.context["total_pessoas_confirmadas"], 2)

        self.client.post(reverse("painel:vincular_rsvp", args=[self.filha.pk]), {"convidado": self.mae.pk})
        r = self.client.get(reverse("painel:dashboard"))
        self.assertEqual(r.context["total_pessoas_confirmadas"], 3)
        self.assertEqual(r.context["total_pessoas_faltando"], 2 + 2)  # 5-3 da Maria + 2 do Pedro
        self.assertEqual(list(r.context["rsvps_sem_vinculo"]), [])

        self.client.post(reverse("painel:desvincular_rsvp", args=[self.filha.pk]))
        self.assertFalse(VinculoRSVP.objects.exists())

    def test_pdf(self):
        VinculoRSVP.objects.create(rsvp=self.filha, convidado=self.mae)
        r = self.client.get(reverse("painel:relatorio_pdf"))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r["Content-Type"], "application/pdf")
        self.assertTrue(r.content.startswith(b"%PDF"))

    def test_confirmar_restante_e_desfazer(self):
        VinculoRSVP.objects.create(rsvp=self.filha, convidado=self.mae)  # Maria: 2 + 1 de 5
        self.client.post(reverse("painel:confirmar_restante", args=[self.mae.pk]))
        self.mae.refresh_from_db()
        self.assertEqual(self.mae.confirmados_extra, 2)
        r = self.client.get(reverse("painel:dashboard"))
        self.assertEqual(r.context["total_pessoas_confirmadas"], 5)
        self.assertEqual(r.context["total_pessoas_faltando"], 2)  # só o Pedro

        self.client.post(reverse("painel:desfazer_restante", args=[self.mae.pk]))
        self.mae.refresh_from_db()
        self.assertEqual(self.mae.confirmados_extra, 0)


@override_settings(PAINEL_API_TOKEN="segredo", PAINEL_WEBHOOK_URL="")
class ApiTests(TestCase):
    auth = {"HTTP_AUTHORIZATION": "Bearer segredo"}

    def setUp(self):
        self.mae = ConvidadoLista.objects.create(nome="Maria Souza", quantidade_esperada=5)
        RSVP.objects.create(nome_completo="Maria Souza", telefone="1", quantidade_convidados=2)

    def test_token_obrigatorio(self):
        self.assertEqual(self.client.get(reverse("painel:api_resumo")).status_code, 401)
        r = self.client.get(reverse("painel:api_resumo"), HTTP_AUTHORIZATION="Bearer errado")
        self.assertEqual(r.status_code, 401)

    @override_settings(PAINEL_API_TOKEN="")
    def test_api_desativada_sem_token(self):
        self.assertEqual(self.client.get(reverse("painel:api_resumo"), **self.auth).status_code, 503)

    def test_resumo(self):
        r = self.client.get(reverse("painel:api_resumo"), **self.auth).json()
        self.assertEqual(r["pessoas_confirmadas"], 2)
        self.assertEqual(r["pessoas_faltando"], 3)

    def test_adicionar_listar_remover(self):
        r = self.client.post(reverse("painel:api_convidados"), {"nome": "Novo", "quantidade_esperada": 3},
                             content_type="application/json", **self.auth)
        self.assertEqual(r.status_code, 201)
        novo = r.json()["id"]
        pend = self.client.get(reverse("painel:api_convidados") + "?status=pendentes", **self.auth).json()
        self.assertEqual([c["nome"] for c in pend["convidados"]], ["Novo"])
        self.assertEqual(self.client.delete(reverse("painel:api_convidado", args=[novo]), **self.auth).status_code, 200)
        self.assertFalse(ConvidadoLista.objects.filter(pk=novo).exists())

    def test_nome_obrigatorio(self):
        r = self.client.post(reverse("painel:api_convidados"), {}, content_type="application/json", **self.auth)
        self.assertEqual(r.status_code, 400)

    def test_webhook_ao_confirmar(self):
        with override_settings(PAINEL_WEBHOOK_URL="https://bot.exemplo/aviso"), \
                mock.patch("painel.signals._enviar") as enviar, \
                mock.patch("painel.signals.threading.Thread", side_effect=lambda target, args, daemon: mock.Mock(start=lambda: target(*args))), \
                self.captureOnCommitCallbacks(execute=True):
            ConvidadoLista.objects.create(nome="Pedro Lima", quantidade_esperada=3)
            RSVP.objects.create(nome_completo="Pedro Lima", telefone="2", quantidade_convidados=1)
        url, corpo = enviar.call_args.args
        dados = json.loads(corpo)
        self.assertEqual(url, "https://bot.exemplo/aviso")
        self.assertEqual(dados["evento"], "confirmacao")
        self.assertEqual(dados["confirmacao"]["nome"], "Pedro Lima")
        self.assertEqual(dados["convite"]["faltam"], 2)
        self.assertEqual(dados["resumo"]["pessoas_confirmadas"], 3)
