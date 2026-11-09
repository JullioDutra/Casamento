# API do Painel dos Noivos

API JSON para bots e sistemas externos. Base: `https://<seu-dominio>/painel/api/`.

## Configuração (variáveis de ambiente no servidor)

| Variável | Para quê |
|---|---|
| `PAINEL_API_TOKEN` | Token secreto. Sem ele a API responde `503` (desativada). |
| `PAINEL_WEBHOOK_URL` | Opcional. URL do bot que recebe um aviso a cada nova confirmação. |

Toda requisição precisa do header `Authorization: Bearer <PAINEL_API_TOKEN>`.

## Endpoints

| Método | Rota | O que faz |
|---|---|---|
| GET | `resumo/` | Totais: convites, confirmados, pendentes, pessoas esperadas/confirmadas/faltando |
| GET | `convidados/?status=pendentes\|confirmados\|faltando` | Lista convites (sem `status` = todos). `faltando` inclui convites confirmados em parte |
| POST | `convidados/` | Adiciona convite. JSON: `{"nome": "...", "telefone": "...", "quantidade_esperada": 2, "grupo": "...", "observacoes": "..."}` (só `nome` é obrigatório) |
| GET | `convidados/<id>/` | Detalhe de um convite |
| DELETE | `convidados/<id>/` | Remove um convite |
| GET | `confirmacoes/?desde=2026-11-09T10:00:00-03:00` | Confirmações do site (opcionalmente só as novas depois de `desde`) |

Exemplo:

```bash
curl -H "Authorization: Bearer $TOKEN" https://<seu-dominio>/painel/api/resumo/
```

## Aviso de nova confirmação (webhook)

Com `PAINEL_WEBHOOK_URL` definida, cada confirmação feita pelo site gera um `POST` para essa URL,
com o mesmo header `Authorization: Bearer <PAINEL_API_TOKEN>` (para o bot conferir a origem) e o corpo:

```json
{
  "evento": "confirmacao",
  "confirmacao": {"id": 7, "nome": "Joana", "telefone": "...", "quantidade": 1, "mensagem": "...", "criado_em": "..."},
  "convite": {"id": 3, "nome": "Maria Souza", "quantidade_esperada": 5, "quantidade_confirmada": 1, "faltam": 4, "...": "..."},
  "resumo": {"pessoas_confirmadas": 42, "pessoas_faltando": 18, "...": "..."}
}
```

`convite` vem `null` quando o nome não bate com ninguém da lista (vincule no painel, aba RSVP).
Se o servidor não puder fazer chamadas externas, use `confirmacoes/?desde=` periodicamente no lugar do webhook.
