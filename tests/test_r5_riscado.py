#!/usr/bin/env python3
"""r5: preço riscado ("de R$") só quando o item NÃO vem marcado sd (sem histórico); promo maior que o normal é ignorada.
Estoque FICTÍCIO montado aqui (o estoque.json real não é usado). Uso: python3 -m http.server 8767 e python3 tests/test_r5_riscado.py"""
import json, os
from datetime import datetime
from playwright.sync_api import sync_playwright
URL = os.environ.get("URL", "http://localhost:8767/index.html"); CHROME = os.environ.get("CHROME", "/usr/bin/google-chrome")
P = {"pi": "2026-11-16", "pf": "2026-11-30"}
B = lambda i, **k: {"s": "apple", "g": "iPhone", "tipo": "iPhone", "cond": "semi", "cap": "128GB", "cor": "Preto", "bat": 85, "i": i, **k}
FX = json.dumps({"atualizado": "2026-11-16T03:00:00Z", "itens": [
    B("com", modelo="iPhone 14", preco=2499, pn=2499, pp=2349, k="0001", **P),
    B("sem", modelo="iPhone 15", preco=3290, pn=3290, pp=3090, k="0002", sd=1, **P),
    B("maior", modelo="iPhone 13", preco=1899, pn=1899, pp=1949, k="0003", **P)]})
falhas = []
def ck(n, c, i=""): print(("OK    " if c else "FALHOU"), n, "" if c else i); c or falhas.append(n)
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
    pg = b.new_context(timezone_id="America/Sao_Paulo").new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.route("**/estoque.json*", lambda r: r.fulfill(status=200, content_type="application/json", body=FX))
    pg.clock.set_fixed_time(datetime.fromisoformat("2026-11-28T15:00:00+00:00")); pg.goto(URL + "#semi"); pg.wait_for_timeout(1200)
    r = pg.evaluate("""()=>{ const g=id=>ITENS.find(i=>i.i===id); const html=document.body.innerHTML;
      return {com:precoAjustado(g('com')), sem:precoAjustado(g('sem')), maior:precoAjustado(g('maior')), maiorAtiva:promoAtiva(g('maior')),
              deCom:html.includes('de R$ 2.499'), deSem:html.includes('de R$ 3.290'), deMaior:html.includes('de R$ 1.899')}; }""")
    ck("promo com histórico: 2.349 com 'de R$ 2.499'", r["com"] == 2349 and r["deCom"], r)
    ck("promo sem histórico (sd): 3.090 sem riscado", r["sem"] == 3090 and not r["deSem"], r)
    ck("promo maior que o normal ignorada: 1.899, sem riscado", r["maior"] == 1899 and not r["maiorAtiva"] and not r["deMaior"], r)
    ck("sem erro JS", not errs, errs[:2]); b.close()
print("RESULTADO FINAL:", "tudo certo" if not falhas else f"{len(falhas)} falha(s): {falhas}")
