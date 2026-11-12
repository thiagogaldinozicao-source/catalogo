#!/usr/bin/env python3
"""Catálogo: preço da promoção pela data de Brasília no navegador, ao abrir e com a aba aberta na virada.
Estoque FICTÍCIO (tests/estoque-ficticio.json: 4 itens com pp = preço − 200 de 16/11 a 25/12). O estoque.json real não é usado.
Uso: python3 -m http.server 8767 e python3 tests/test_preco_data.py"""
import json, os, sys
from datetime import datetime
from playwright.sync_api import sync_playwright
URL = os.environ.get("URL", "http://localhost:8767/index.html"); CHROME = os.environ.get("CHROME", "/usr/bin/google-chrome")
FX = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "estoque-ficticio.json"), encoding="utf-8").read()
falhas = []
def ck(n, c, i=""): print(("OK    " if c else "FALHOU"), n, i); c or falhas.append(n)
LE = "()=>{const it=ITENS.find(i=>i.pp);const card=[...document.querySelectorAll('.card')].find(c=>c.querySelector('.de'));return {dia:hojeBR(),preco:precoAjustado(it),pn:it.pn,pp:it.pp,redesenhos:window._nd||0}}"
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
    def abre(inst, tz, andando=False):
        pg = b.new_context(timezone_id=tz).new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.route("**/estoque.json*", lambda r: r.fulfill(status=200, content_type="application/json", body=FX))
        pg.clock.install(time=datetime.fromisoformat(inst)) if andando else pg.clock.set_fixed_time(datetime.fromisoformat(inst))
        pg.goto(URL + "#semi"); pg.wait_for_timeout(1000)
        if andando: pg.clock.run_for(1500)
        pg.evaluate("()=>{window._nd=0;const o=desenha;desenha=function(){window._nd++;return o.apply(this,arguments)}}")
        return pg, errs
    for tz in ("America/Sao_Paulo", "Asia/Tokyo", "UTC"):
        for inst, br, promo in [("2026-11-16T02:59:59+00:00", "15/11 23:59:59", False), ("2026-11-16T03:00:01+00:00", "16/11 00:00:01", True),
                                ("2026-12-26T02:59:59+00:00", "25/12 23:59:59", True), ("2026-12-26T03:00:01+00:00", "26/12 00:00:01", False)]:
            pg, errs = abre(inst, tz); e = pg.evaluate(LE)
            ck(f"[{tz}] abrir em {br} Brasília → {'promo' if promo else 'normal'}", e["preco"] == (e["pp"] if promo else e["pn"]) and not errs, json.dumps(e)); pg.close()
    for inst, br, de, para in [("2026-11-16T02:59:30+00:00", "15/11→16/11", "normal", "promo"), ("2026-12-26T02:59:30+00:00", "25/12→26/12", "promo", "normal")]:
        pg, errs = abre(inst, "Asia/Tokyo", andando=True); a = pg.evaluate(LE); pg.clock.run_for(65000); pg.wait_for_timeout(300); d = pg.evaluate(LE)
        okA = a["preco"] == (a["pp"] if de == "promo" else a["pn"]); okD = d["preco"] == (d["pp"] if para == "promo" else d["pn"])
        ck(f"aba aberta na virada {br}: {de} → {para} sem recarregar (lista redesenhada {d['redesenhos']}x)", okA and okD and d['redesenhos'] >= 1 and not errs, f"{a['preco']} → {d['preco']}"); pg.close()
    b.close()
print("RESULTADO:", "tudo certo" if not falhas else f"{len(falhas)} falha(s): {falhas}"); sys.exit(1 if falhas else 0)
