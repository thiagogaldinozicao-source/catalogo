# Preço pela data de Brasília no próprio catálogo — branch `preco-por-data` (NÃO publicado)
Só preço. Os temas Black/Natal são outro trabalho (branch `temas-2026`).

- O navegador do cliente calcula `hojeBR()` (Intl, `America/Sao_Paulo`) e usa `pp` (promoção) quando `pi <= hoje <= pf`, senão `pn`/`preco`. Ao abrir já mostra o preço certo, sem esperar a tarefa das 00h22.
- Aba aberta: confere a cada 20 s; virou o dia, redesenha a lista (e a ficha aberta, sem mexer no histórico).
- Card mostra "de R$ X" riscado só quando a promoção é real e está valendo.
- Compatível com o estoque.json de hoje (sem `pp` = preço de sempre). Pra valer, a tarefa do catálogo precisa mandar `pn/pp/pi/pf` (proposta no Gestão, branch `revisao-promo`, pasta tarefas-catalogo; só manda promo que vale hoje ou começa amanhã).
- Teste: `python3 -m http.server 8767` e `python3 tests/test_preco_data.py` (estoque fictício; aparelho em Brasília, Tóquio e UTC; viradas 15→16/11 e 25→26/12 com a aba aberta).
