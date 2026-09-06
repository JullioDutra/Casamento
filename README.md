# Site de Casamento — Django

Versão dinâmica do convite de casamento: tudo o que antes estava fixo no HTML
(data, local, presentes, chave PIX, fotos da galeria) agora é editável pelo
**admin do Django**, sem precisar mexer em código.

## O que ficou dinâmico

| Model           | O que controla                                                          |
|------------------|--------------------------------------------------------------------------|
| `Evento`         | Nomes dos noivos, data/hora, versículo, textos do convite, dados do PIX (nome do recebedor e cidade) e o toggle de fotos dos convidados |
| `Local`          | Cards de "Data", "Horário", "Local", "Traje". Ao usar Tipo = "Local", o campo "Subtipo" (Cerimônia/Recepção) diferencia os botões "Ver Localização" quando há mais de um endereço |
| `Presente`       | Cards da lista de presentes, valor e chave PIX                          |
| `Presenteador`   | Registro automático de quem confirmou presentear cada item (nome + data), visível no admin dentro de cada Presente |
| `FotoGaleria`    | Fotos da galeria (cadastradas por você)                                 |
| `FotoConvidado`  | Fotos enviadas pelos próprios convidados (fica pendente de aprovação — campo `aprovada`) |
| `RSVP`           | Respostas do formulário de confirmação de presença                      |

## QR Code PIX automático

Cada presente gera, na hora, um QR Code PIX real (payload EMV/BR Code, o
mesmo padrão "Copia e Cola" usado por qualquer app de banco) — não é mais
um desenho estático. Antes de mostrar o QR Code, o convidado precisa
informar o nome de quem está presenteando; esse nome fica registrado no
admin, dentro da própria página de cada Presente.

Para o QR Code funcionar corretamente, preencha em **Evento → Dados para o
PIX**:
- **Nome do recebedor**: até 25 caracteres, aparece no app de quem for pagar.
- **Cidade**: até 15 caracteres, sem acento é mais seguro (ex: `ANAPOLIS`).

## Fotos enviadas pelos convidados

Em **Evento**, marque **"Permitir que convidados enviem fotos da
cerimônia"** para exibir o botão de upload na seção da cerimônia do site.
Desmarcado, o botão simplesmente não aparece. As fotos enviadas chegam em
**FotoConvidado** no admin, com o campo `aprovada` desmarcado por padrão —
é uma etapa de moderação antes de decidir se elas vão para a galeria
pública (adicione-as manualmente em `FotoGaleria` se aprovar).

## Painel dos Noivos (acesso restrito)

Em `/painel/` fica uma tela completa, separada do site público, só para os
noivos controlarem a lista de convidados. **Não existe cadastro público** —
o acesso é feito com login e senha criados por vocês via
`python manage.py createsuperuser` (ou qualquer usuário criado no
`/admin/`). Sem login, `/painel/` redireciona direto para a tela de entrada.

O que o painel mostra:
- **Cards com estatísticas**: quantos estão na lista, quantos confirmaram,
  quantos ainda faltam, % de confirmação, total de pessoas esperadas e
  quantas pessoas já confirmaram pelo formulário do site.
- **Importar planilha**: suba um `.xlsx` ou `.csv` com colunas `Nome`
  (obrigatória), `Telefone`, `Quantidade` e `Grupo` — nessa ordem ou não,
  o sistema identifica pelo nome da coluna. Tem um botão para baixar um
  modelo de planilha pronto. Nomes repetidos são ignorados automaticamente.
- **Adicionar convidado manualmente**, sem precisar de planilha.
- **Lista de convidados** com status "Confirmado" (calculado automaticamente
  ao bater o nome com algum RSVP recebido pelo site, ou marcado manualmente
  pelos noivos) ou "Falta confirmar", com filtro por status, busca por nome,
  botão para alternar o status na marra e excluir.
- **Tabela separada com todas as confirmações recebidas pelo site**, mesmo
  que a pessoa ainda não esteja na planilha importada.

Link discreto para o painel no rodapé do site ("Painel dos Noivos"); como
o acesso exige login, convidados comuns não conseguem entrar mesmo vendo o link.

## Como rodar localmente

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Depois acesse:
- `http://127.0.0.1:8000/` → site do convite
- `http://127.0.0.1:8000/admin/` → painel para cadastrar o Evento, Locais, Presentes e Fotos

## Primeiro cadastro (obrigatório)

O site não vai exibir nada até você cadastrar um **Evento** no admin
(é tratado como singleton — só pode existir um). No mesmo formulário do
Evento, dá pra adicionar os **Locais** (inline), e depois em telas separadas
você cadastra os **Presentes** e as **Fotos** da galeria.

## Próximos passos sugeridos

- Trocar `SECRET_KEY` e `DEBUG=False` antes de publicar
- Configurar um banco Postgres em produção (hoje está em SQLite)
- Gerar QR Code real do PIX a partir da chave (lib `qrcode`), em vez do
  desenho estático que hoje é só ilustrativo
- Adicionar proteção anti-spam no formulário de RSVP (ex: honeypot ou captcha)
