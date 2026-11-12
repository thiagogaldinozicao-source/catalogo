#!/usr/bin/env python3
"""Gera prévias (PNG) do catálogo original / Black / Natal com estoque FICTÍCIO de prévia e audita cortes/vazamentos
em telas pequenas. Não usa nem altera o estoque.json real. Uso: python3 -m http.server 8766 e python3 tests/previas_campanhas.py [saida]"""
import json, os, sys
from datetime import datetime
from playwright.sync_api import sync_playwright
AQUI = os.path.dirname(os.path.abspath(__file__)); OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(AQUI, "previas")
URL = os.environ.get("URL", "http://localhost:8766/index.html"); CHROME = os.environ.get("CHROME", "/usr/bin/google-chrome")
FX = open(os.path.join(AQUI, "estoque-previa-campanhas.json"), encoding="utf-8").read()
AUDIT = """()=>{ const W=innerWidth, ruins=[];
  document.querySelectorAll('body *').forEach(e=>{ const cs=getComputedStyle(e); if(cs.display==='none'||cs.visibility==='hidden') return;
    const r=e.getBoundingClientRect(); if(!r.width||!r.height) return;
    let a=e.parentElement, rola=false; while(a){ const ox=getComputedStyle(a).overflowX; if(ox==='auto'||ox==='scroll'||ox==='hidden'){rola=true;break;} a=a.parentElement; }
    if(rola && !(r.right>W+1 && e.matches('.camp-b,.camp-b *,header *,nav *'))) { /* dentro de faixa que rola/recorta de propósito */ }
    else
    if(r.right>W+1||r.left<-1) ruins.push('vaza: '+(e.className||e.tagName)+' '+Math.round(r.left)+'..'+Math.round(r.right));
    const t=(e.matches('.price,.p,.n,.t,button,a,.camp-b *,.camp-cd,h1,h2,h3')); if(t && e.scrollWidth>e.clientWidth+1 && cs.overflow!=='visible')
      ruins.push('cortado: '+(e.className||e.tagName)+' "'+e.textContent.trim().slice(0,40)+'"'); });
  return {ruins:[...new Set(ruins)].slice(0,25), docW:document.documentElement.scrollWidth, W}; }"""
CASOS = [("original", "2026-11-14T15:00:00+00:00"), ("black", "2026-11-28T15:00:00+00:00"), ("natal", "2026-12-10T15:00:00+00:00")]
TELAS = [("se", 375, 667), ("iphone", 390, 844), ("mini", 320, 640)]
os.makedirs(OUT, exist_ok=True); res = {}
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
    for nome, inst in CASOS:
        for tn, w, h in TELAS:
            ctx = b.new_context(timezone_id="America/Sao_Paulo", viewport={"width": w, "height": h}, device_scale_factor=2, is_mobile=True, has_touch=True)
            pg = ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.route("**/estoque.json*", lambda r: r.fulfill(status=200, content_type="application/json", body=FX))
            pg.clock.set_fixed_time(datetime.fromisoformat(inst)); pg.goto(URL); pg.wait_for_timeout(1500)
            a = pg.evaluate(AUDIT); a["errs"] = errs; res[f"{nome}-{tn}"] = a
            if tn == "iphone":
                pg.screenshot(path=os.path.join(OUT, f"{nome}-topo.png"))
                pg.screenshot(path=os.path.join(OUT, f"{nome}-pagina.png"), full_page=True)
            ctx.close()
    b.close()
print(json.dumps(res, ensure_ascii=False, indent=1))
