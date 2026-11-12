# Temas Black / Natal 2026 — branch `temas-2026` (NÃO publicado)

- **Black Zicão Store:** 16/11/2026 00:00 → 30/11/2026 23:59:59 (Brasília). Preto, dourado e vermelho; banner, contagem regressiva até o fim real e "Ofertas da Black".
- **Natal Zicão Store:** 01/12/2026 00:00 → 25/12/2026 23:59:59. Verde-esmeralda, dourado, vermelho discreto; banner, "Ofertas de Natal" e "Pra presentear".
- Fora das datas: **visual original** (volta sozinho em 26/12), sem nenhuma classe/cor extra (o tema só existe dentro de `body.tema-black` / `body.tema-natal`; o `:root` original não foi tocado).

Como funciona
- O navegador do cliente calcula a data de Brasília (`hojeBR`, Intl `America/Sao_Paulo`) ao abrir e a cada 20 s: virou o dia com o catálogo aberto, troca/volta o tema e os preços sozinho. Não depende de ninguém abrir o Gestão nem da tarefa agendada.
- Datas padrão no código; o Gestão (Master, ⚙ › 🎨 Temas do catálogo) pode ligar/desligar e mudar datas → vai no estoque.json (`campanhas`) na atualização do catálogo.
- **Tema ≠ preço.** "Ofertas" só mostra item com promoção real (`pp` < `pn` e dentro de `pi..pf`, cadastrada na 🔥 Promoção do Gestão). Sem promo, a seção não aparece. Nada de desconto fictício.
- "Últimas unidades" só quando o estoque.json traz `q` (quantidade real) ≤ 2 em lacrado/acessório.
- Prévia: `?tema=black`, `?tema=natal`, `?tema=original` (selo PRÉVIA; não muda preço).

Testes: `python3 -m http.server 8766` e `python3 tests/test_temas.py` (estoque FICTÍCIO em tests/estoque-ficticio.json; o estoque.json real não é usado nem alterado). Prévias em `tests/previas/`.

## Acabamento (12/11)
- Integrado em cima de `preco-por-data`: uma única lógica de preço (`hojeBR/promoAtiva/precoAjustado`). O tema só cuida do visual; na virada do dia o módulo de preço redesenha a lista e refaz a campanha.
- Banner compacto (não ocupa a primeira tela): Black com faixas douradas sutis e vermelho; Natal esmeralda com pontos de neve discretos. Botão **Ver ofertas** (ou **Ver presentes** / **Ver catálogo** se não houver promoção real) rola até a seção.
- Ofertas e "Pra presentear" ficam **depois** das seções Apple/Android/Acessórios, então categorias e busca continuam no topo.
- Carrossel com o próximo card aparecendo, "arraste" e botões ‹ ›; nada vaza da tela no iPhone.
- Foto **real** do catálogo (da loja ou do modelo). Sem foto: quadro neutro com o logo e a categoria, nunca imagem inventada. Hoje os acessórios não têm foto no catálogo, então "Pra presentear" aparece com o quadro neutro até alguém fotografar esses produtos no Gestão.
- Testes: `tests/test_temas.py` (inclui iPhone 13 emulado no Chrome) e `tests/test_preco_data.py`. O WebKit (motor do Safari) não pôde ser baixado neste ambiente (bloqueado), então falta conferir num iPhone de verdade.

## Acabamento final (12/11, r6) — não publicado
- **Fontes:** Sora/Inter agora têm fonte reserva do sistema (no iPhone, a do próprio iOS). Antes, se a fonte da web não carregasse (rede lenta), títulos e botões caíam pra uma fonte serifada (tipo Times).
- **Foto ilustrativa:** a mesma foto usada em mais de uma unidade (hoje: 9 iPhone 13 pretos com a mesma foto, 5 iPhone 14 pretos etc. — 38 unidades com foto, só 14 fotos diferentes) ou foto do modelo aparece com "📷 Foto ilustrativa do modelo" no card, no detalhe e no carrossel. Foto exclusiva da unidade continua sem aviso.
- **Pix × cartão:** o carrossel das campanhas agora mostra "no Pix" e, à parte, "ou 12x R$ … no cartão" (antes mostrava só "R$ …"). O detalhe mostra o "de R$" com a mesma regra do card (só com desconto real e histórico, sem `sd`).
- **Texto:** selo "Última unidade" / "Últimas unidades" (antes "Últimas unidade").
- Natal não mostra preço da Black (promo de 16–30/11 volta ao normal em 01/12), "Pra presentear" com foto real ou quadro neutro.
- Testes: `tests/test_r6_catalogo.py` (foto ilustrativa, Pix/cartão, Natal sem Black, 320/375/390 px sem vazamento e sem preço/botão cortado), com o estoque FICTÍCIO `tests/estoque-previa-campanhas.json` (promos inventadas só pra prévia: Black 16–30/11, Natal 01–25/12). Prévias: `python3 tests/previas_campanhas.py` → `tests/previas/`.
- O R$ 1.099 das prévias antigas era do estoque fictício de teste (`tests/estoque-ficticio.json`, promo inventada nos iPhone 11). O index.html não tem preço nenhum embutido: só lê o estoque.json; os arquivos de teste nunca são carregados pelo site.

## Testar no Safari do iPhone sem publicar
1. No iPhone, abra no Safari (aba normal): `https://raw.githack.com/thiagogaldinozicao-source/catalogo/temas-2026/index.html?tema=black`
   — é a cópia da branch de teste servida direto do GitHub; o site oficial (GitHub Pages, branch main) não muda.
2. Troque o fim do endereço pra `?tema=natal` e `?tema=original`. Aparece o selo PRÉVIA; os preços são os reais de hoje (o `?tema=` só muda o visual, nunca o preço).
3. Confira: banner, botão "Ver ofertas", categorias, carrossel (arrastar e ‹ ›), abrir um aparelho, botão do WhatsApp (abre o WhatsApp — não precisa enviar), girar o celular, zoom do texto (Ajustes › Tela › Tamanho do Texto maior).
4. Sem promoção cadastrada, "Ofertas" não aparece e não tem preço riscado — é o esperado. As ofertas só aparecem quando a promoção real for cadastrada no Gestão e o catálogo atualizado (depois do seu OK).
5. Se o githack mostrar versão antiga, acrescente `&v=2` no fim (cache).
