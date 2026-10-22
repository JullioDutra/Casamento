import difflib
from io import BytesIO

from django.utils import timezone

from convite.models import RSVP

from .models import ConvidadoLista
from .utils import normalizar_nome


def nomes_similares(nome1, nome2):
    """
    Retorna True se os nomes forem pelo menos 80% parecidos ou se um contiver o outro.
    Útil para não duplicar confirmações quando há erros de digitação.
    """
    if not nome1 or not nome2:
        return False
    if nome1 in nome2 or nome2 in nome1:
        return True
    return difflib.SequenceMatcher(None, nome1, nome2).ratio() > 0.8


def montar_lista():
    """
    Cruza a lista mestre com os RSVPs do site. Cada convite recebe:
    o RSVP que bate pelo nome, mais os RSVPs vinculados manualmente.
    Retorna (linhas, rsvps_sem_vinculo).
    """
    rsvps = list(RSVP.objects.select_related("vinculo").order_by("-criado_em"))
    vinculados = {}
    livres = []
    for r in rsvps:
        vinculo = getattr(r, "vinculo", None)
        if vinculo:
            vinculados.setdefault(vinculo.convidado_id, []).append(r)
        else:
            livres.append((normalizar_nome(r.nome_completo), r))

    usados = set()
    linhas = []
    for c in ConvidadoLista.objects.all():
        nome_c = normalizar_nome(c.nome)
        auto = next((r for n, r in livres if nomes_similares(nome_c, n)), None)
        if auto:
            usados.add(auto.pk)
        extras = vinculados.get(c.pk, [])
        rsvps_c = ([auto] if auto else []) + extras

        confirmado = c.confirmado_manual or bool(rsvps_c)
        if rsvps_c:
            qtd = sum(r.quantidade_convidados for r in rsvps_c)
        else:
            qtd = c.quantidade_esperada if confirmado else 0

        linhas.append({
            "obj": c,
            "confirmado": confirmado,
            "rsvp": auto or (extras[0] if extras else None),
            "rsvps_vinculados": extras,
            "rsvps_todos": rsvps_c,
            "qtd_confirmada": qtd,
            "qtd_final": qtd if confirmado else c.quantidade_esperada,
            "faltam": max(c.quantidade_esperada - qtd, 0) if confirmado else c.quantidade_esperada,
        })

    sem_vinculo = [r for _, r in livres if r.pk not in usados]
    return linhas, sem_vinculo


def gerar_pdf(linhas, sem_vinculo):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    vinho = colors.HexColor("#8A1538")
    estilos = getSampleStyleSheet()
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=1.5 * cm, rightMargin=1.5 * cm,
                            topMargin=1.5 * cm, bottomMargin=1.5 * cm,
                            title="Relatório de confirmações")

    confirmados = [l for l in linhas if l["confirmado"]]
    pendentes = [l for l in linhas if not l["confirmado"]]
    pessoas_conf = sum(l["qtd_confirmada"] for l in confirmados)
    pessoas_esp = sum(l["obj"].quantidade_esperada for l in linhas)
    pessoas_faltam = sum(l["faltam"] for l in linhas)

    def tabela(dados, larguras):
        t = Table(dados, colWidths=larguras, repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), vinho),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 8.5),
            ("VALIGN", (0, 0), (-1, -1), 'MIDDLE'),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7F4F2")]),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#D6D3D1")),
        ]))
        return t

    def p(texto):
        return Paragraph(texto.replace("&", "&amp;").replace("<", "&lt;"), estilos["BodyText"])

    el = [
        Paragraph("Relatório de Confirmações — Casamento", estilos["Title"]),
        Paragraph(f"Gerado em {timezone.localtime().strftime('%d/%m/%Y %H:%M')}", estilos["Normal"]),
        Spacer(1, 0.4 * cm),
        tabela([
            ["Convites", "Conf.", "Pendentes",
             "Esperadas", "Confirmadas", "Faltam"],
            [len(linhas), len(confirmados), len(pendentes), pessoas_esp, pessoas_conf, pessoas_faltam],
        ], [2.9 * cm] * 6),
        Spacer(1, 0.6 * cm),
        Paragraph(f"Confirmados ({len(confirmados)} convites / {pessoas_conf} pessoas)", estilos["Heading2"]),
    ]

    dados = [["Convite", "Grupo", "Confirmadas", "Esperadas", "Faltam", "Quem confirmou"]]
    for l in sorted(confirmados, key=lambda x: x["obj"].nome):
        quem = []
        if l["obj"].confirmado_manual:
            quem.append("manual")
        quem += [f"{r.nome_completo} ({r.quantidade_convidados})" for r in l["rsvps_todos"]]
        dados.append([p(l["obj"].nome), p(l["obj"].grupo or "—"), l["qtd_confirmada"],
                      l["obj"].quantidade_esperada, l["faltam"], p(", ".join(quem))])
    if len(dados) == 1:
        dados.append(["Nenhum", "", "", "", "", ""])
    el.append(tabela(dados, [4.2 * cm, 2.8 * cm, 1.9 * cm, 1.8 * cm, 1.4 * cm, 5.9 * cm]))

    el += [Spacer(1, 0.6 * cm),
           Paragraph(f"Faltam confirmar ({len(pendentes)} convites / "
                     f"{sum(l['obj'].quantidade_esperada for l in pendentes)} pessoas)", estilos["Heading2"])]
    dados = [["Convite", "Grupo", "Telefone", "Pessoas"]]
    for l in sorted(pendentes, key=lambda x: x["obj"].nome):
        dados.append([p(l["obj"].nome), p(l["obj"].grupo or "—"), l["obj"].telefone or "—",
                      l["obj"].quantidade_esperada])
    if len(dados) == 1:
        dados.append(["Todos confirmaram", "", "", ""])
    el.append(tabela(dados, [7 * cm, 4.5 * cm, 3.5 * cm, 2 * cm]))

    if sem_vinculo:
        el += [Spacer(1, 0.6 * cm),
               Paragraph(f"Confirmações do site sem vínculo na lista ({len(sem_vinculo)})", estilos["Heading2"])]
        dados = [["Nome informado", "Telefone", "Pessoas"]]
        for r in sem_vinculo:
            dados.append([p(r.nome_completo), r.telefone or "—", r.quantidade_convidados])
        el.append(tabela(dados, [9 * cm, 5 * cm, 3 * cm]))

    doc.build(el)
    return buf.getvalue()
