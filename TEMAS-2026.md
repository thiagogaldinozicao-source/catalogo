# Temas Black / Natal 2026 — branch `temas-2026` (NÃO publicado)

- **Black Zicão Store:** 27/11/2026 00:00 → 30/11/2026 23:59:59 (Brasília). Preto, dourado e vermelho; banner, contagem regressiva até o fim real e "Ofertas da Black".
- **Natal Zicão Store:** 01/12/2026 00:00 → 25/12/2026 23:59:59. Verde-esmeralda, dourado, vermelho discreto; banner, "Ofertas de Natal" e "Pra presentear".
- Fora das datas: **visual original**, sem nenhuma classe/cor extra (o tema só existe dentro de `body.tema-black` / `body.tema-natal`; o `:root` original não foi tocado).

Como funciona
- O navegador do cliente calcula a data de Brasília (`hojeBR`, Intl `America/Sao_Paulo`) ao abrir e a cada 20 s: virou o dia com o catálogo aberto, troca/volta o tema e os preços sozinho. Não depende de ninguém abrir o Gestão nem da tarefa agendada.
- Datas padrão no código; o Gestão (Master, ⚙ › 🎨 Temas do catálogo) pode ligar/desligar e mudar datas → vai no estoque.json (`campanhas`) na atualização do catálogo.
- **Tema ≠ preço.** "Ofertas" só mostra item com promoção real (`pp` < `pn` e dentro de `pi..pf`, cadastrada na 🔥 Promoção do Gestão). Sem promo, a seção não aparece. Nada de desconto fictício.
- "Últimas unidades" só quando o estoque.json traz `q` (quantidade real) ≤ 2 em lacrado/acessório.
- Prévia: `?tema=black`, `?tema=natal`, `?tema=original` (selo PRÉVIA; não muda preço).

Testes: `python3 -m http.server 8766` e `python3 tests/test_temas.py` (estoque FICTÍCIO em tests/estoque-ficticio.json; o estoque.json real não é usado nem alterado). Prévias em `tests/previas/`.
