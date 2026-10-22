from django.contrib.auth import get_user_model
from django.test import TestCase
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
