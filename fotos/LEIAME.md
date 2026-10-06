# Fotos dos aparelhos

- `fotos/p/` — fotos tiradas na loja pelo Zicão Gestão (Estoque › produto › Foto pro catálogo).
  São geradas sozinhas toda noite pelo `sync/estoque_para_catalogo.py --fotos`: miniatura (~25 KB)
  pro card e grande (~100 KB) só quando o cliente abre o produto. Foto de produto vendido é apagada.
  Não mexa nessa pasta na mão.
- Fotos antigas por modelo (opcional, lista `FOTOS` do `index.html`): `.webp` quadrada de ~600 px,
  nome `modelo-cor.webp` (ex.: `15-pro-max-cinza.webp`) ou só `modelo.webp`. A foto da loja tem prioridade.
