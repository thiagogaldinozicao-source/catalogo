#!/usr/bin/env python3
"""Testa os temas Black/Natal do catálogo (branch temas-2026) com um estoque FICTÍCIO (tests/estoque-ficticio.json).
Não mexe no estoque.json real. Uso: python3 -m http.server 8766 (na raiz) e python3 tests/test_temas.py [--fotos]"""
import json, os, sys
from datetime import datetime
from playwright.sync_api import sync_playwright
URL = os.environ.get("URL", "http://localhost:8766/index.html"); CHROME = os.environ.get("CHROME", "/usr/bin/google-chrome")
FX = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "estoque-ficticio.json"), encoding="utf-8").read()
falhas = []
def ck(n, c, i=""): print(("OK    " if c else "FALHOU"), n, i); c or falhas.append(n)
ESTADO = "()=>({tema:document.body.className.match(/tema-\\w+/)?.[0]||'original',banner:!!document.querySelector('#camp .camp-b'),hojeBR:hojeBR(),preco:(()=>{const it=ITENS.find(i=>i.pp);return it?precoAjustado(it):null})(),cssBg:getComputedStyle(document.body).getPropertyValue('--bg').trim(),cssGold:getComputedStyle(document.body).getPropertyValue('--gold').trim()})"
def abre(b, inst, tz="America/Sao_Paulo", vw=390, vh=844, qs="", relogio="fixo"):
    ctx = b.new_context(timezone_id=tz, viewport={"width": vw, "height": vh}, device_scale_factor=2); pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.route("**/estoque.json*", lambda r: r.fulfill(status=200, content_type="application/json", body=FX))
    if relogio == "fixo": pg.clock.set_fixed_time(datetime.fromisoformat(inst))
    else: pg.clock.install(time=datetime.fromisoformat(inst))
    pg.goto(URL + qs); pg.wait_for_timeout(1200); return pg, errs
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
    orig = None
    CASOS = [("2026-11-16T02:59:59+00:00", "15/11 23:59:59", "original"), ("2026-11-16T03:00:01+00:00", "16/11 00:00:01", "tema-black"),
             ("2026-12-01T02:59:59+00:00", "30/11 23:59:59", "tema-black"), ("2026-12-01T03:00:01+00:00", "01/12 00:00:01", "tema-natal"),
             ("2026-12-26T02:59:59+00:00", "25/12 23:59:59", "tema-natal"), ("2026-12-26T03:00:01+00:00", "26/12 00:00:01", "original")]
    for tz in ("America/Sao_Paulo", "Asia/Tokyo", "UTC"):
        for inst, br, esp in CASOS:
            pg, errs = abre(b, inst, tz); e = pg.evaluate(ESTADO)
            ck(f"[{tz}] {br} Brasília → {esp}", e["tema"] == esp and e["banner"] == (esp != "original") and not errs, json.dumps(e) + (" ERR " + errs[0] if errs else ""))
            if esp == "original":
                if orig is None: orig = (e["cssBg"], e["cssGold"])
                ck(f"[{tz}] {br}: cores originais iguais (--bg {e['cssBg']}, --gold {e['cssGold']})", (e["cssBg"], e["cssGold"]) == orig)
            pg.close()
    ck("cores originais = as do arquivo (#0c0f14 / #f5b301)", orig == ("#0c0f14", "#f5b301"), str(orig))
    # preço da promo fictícia (pi=16/11, pf=25/12) é separado do tema
    for inst, br, esp in [("2026-11-16T02:59:59+00:00", "15/11 23:59", "normal"), ("2026-11-16T03:00:01+00:00", "16/11 00:00", "promo"), ("2026-12-26T03:00:01+00:00", "26/12 00:00", "normal")]:
        pg, errs = abre(b, inst); r = pg.evaluate("()=>{const it=ITENS.find(i=>i.pp);return {v:precoAjustado(it),pn:it.pn,pp:it.pp}}")
        ck(f"preço {br}: {esp}", r["v"] == (r["pp"] if esp == "promo" else r["pn"]), json.dumps(r)); pg.close()
    # catálogo ABERTO na virada da meia-noite (relógio andando): 15/11 23:59:30 → 16/11 00:00:30 e 25/12 → 26/12
    for inst, de, para in [("2026-11-16T02:59:30+00:00", "original", "tema-black"), ("2026-12-01T02:59:30+00:00", "tema-black", "tema-natal"), ("2026-12-26T02:59:30+00:00", "tema-natal", "original")]:
        pg, errs = abre(b, inst, relogio="andando"); a = pg.evaluate(ESTADO); pg.clock.run_for(65000); pg.wait_for_timeout(300); d = pg.evaluate(ESTADO)
        ck(f"página aberta na meia-noite: {de} → {para} sozinho", a["tema"] == de and d["tema"] == para and not errs, f"{a['tema']} → {d['tema']} · preço {a['preco']} → {d['preco']}"); pg.close()
    # prévia (?tema=) e "original" forçado
    pg, errs = abre(b, "2026-11-14T15:00:00+00:00", qs="?tema=natal"); e = pg.evaluate(ESTADO)
    ck("prévia ?tema=natal antes da data mostra o tema + selo PRÉVIA e NÃO muda preço", e["tema"] == "tema-natal" and pg.locator(".camp-prev").count() == 1 and e["preco"] == pg.evaluate("()=>ITENS.find(i=>i.pp).pn"), json.dumps(e)); pg.close()
    # contagem regressiva honesta = até 30/11 23:59:59 de Brasília
    pg, errs = abre(b, "2026-11-29T03:00:00+00:00"); t = pg.inner_text(".camp-cd")
    ck("contagem regressiva da Black termina 30/11 23:59:59 (faltam 1d 23h 59m em 29/11 00:00)", "1d" in t and "23h" in t and "59m" in t, t.replace("\n", " ")); pg.close()
    # campanha desativada pelo Master não aparece
    pg, errs = abre(b, "2026-11-28T15:00:00+00:00"); pg.evaluate("()=>{CAMPANHAS=CAMPANHAS.map(c=>c.id==='black'?{...c,ativo:false}:c);aplicaCampanha();}")
    ck("Black desativada → visual original", pg.evaluate(ESTADO)["tema"] == "original"); pg.close()
    # iPhone 13 (emulação: tela, toque e user-agent do Safari no Chrome; o WebKit de verdade não pôde ser baixado neste ambiente)
    dev = {k: v for k, v in p.devices["iPhone 13"].items() if k != "default_browser_type"}
    for inst, esp in [("2026-11-28T15:00:00+00:00", "tema-black"), ("2026-12-10T15:00:00+00:00", "tema-natal")]:
        ctx = b.new_context(**dev, timezone_id="America/Sao_Paulo"); pg = ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.route("**/estoque.json*", lambda r: r.fulfill(status=200, content_type="application/json", body=FX)); pg.clock.set_fixed_time(datetime.fromisoformat(inst))
        pg.goto(URL); pg.wait_for_timeout(1200)
        r = pg.evaluate("""()=>{const W=document.documentElement.clientWidth;const fora=[...document.querySelectorAll('body *')].filter(e=>{for(let a=e.parentElement;a;a=a.parentElement){const o=getComputedStyle(a).overflowX;if(o==='auto'||o==='scroll'||o==='hidden')return false;}const b=e.getBoundingClientRect();return b.width>0&&b.right>W+1}).map(e=>e.className).slice(0,3);
          const secs=document.querySelector('#secs').getBoundingClientRect().top;const l=document.querySelector('.camp-l');const x0=l?l.scrollLeft:0;return {fora,secsTop:Math.round(secs),vh:innerHeight,x0,tema:document.body.className.match(/tema-\w+/)?.[0]}}""")
        pg.click('[data-cl="camp-ofertas"][data-d="1"]'); pg.wait_for_timeout(700); x1 = pg.evaluate("()=>document.querySelector('#camp-ofertas .camp-l').scrollLeft")
        pg.click(".camp-cta"); pg.wait_for_timeout(900); topo = pg.evaluate("()=>Math.round(document.querySelector('#camp-ofertas').getBoundingClientRect().top)")
        ck(f"iPhone 13 {esp}: nada vazando da tela, categorias visíveis sem rolar (topo {r['secsTop']}px de {r['vh']}), carrossel anda ({r['x0']}→{x1}), 'Ver ofertas' leva às ofertas (topo {topo}px)",
           r["tema"] == esp and not r["fora"] and r["secsTop"] < r["vh"] * 0.6 and x1 > r["x0"] and abs(topo) < 60 and not errs, json.dumps(r))
        pg.close()
    if "--fotos" in sys.argv:
        os.makedirs("/tmp/previas", exist_ok=True)
        for nome, inst, vw, vh in [("black-celular", "2026-11-28T15:00:00+00:00", 390, 844), ("natal-celular", "2026-12-10T15:00:00+00:00", 390, 844),
                                   ("original-celular", "2026-11-14T15:00:00+00:00", 390, 844), ("black-pc", "2026-11-28T15:00:00+00:00", 1280, 860), ("natal-pc", "2026-12-10T15:00:00+00:00", 1280, 860)]:
            pg, errs = abre(b, inst, vw=vw, vh=vh); pg.wait_for_timeout(800); pg.screenshot(path=f"/tmp/previas/{nome}.png"); pg.close()
    b.close()
print("RESULTADO:", "tudo certo" if not falhas else f"{len(falhas)} falha(s): {falhas}"); sys.exit(1 if falhas else 0)
