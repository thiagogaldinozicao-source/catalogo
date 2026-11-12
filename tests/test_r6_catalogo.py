#!/usr/bin/env python3
"""r6: acabamento — foto repetida/do modelo marcada como ilustrativa, carrossel separa Pix do cartão, Natal não mostra
desconto da Black e telas pequenas sem nada vazando. Estoque FICTÍCIO de prévia. Uso: python3 -m http.server 8766 e python3 tests/test_r6_catalogo.py"""
import json, os
from datetime import datetime
from playwright.sync_api import sync_playwright
AQUI = os.path.dirname(os.path.abspath(__file__)); URL = os.environ.get("URL", "http://localhost:8766/index.html"); CHROME = os.environ.get("CHROME", "/usr/bin/google-chrome")
FX = open(os.path.join(AQUI, "estoque-previa-campanhas.json"), encoding="utf-8").read()
falhas = []
def ck(n, c, i=""): print(("OK    " if c else "FALHOU"), n, "" if c else i); c or falhas.append(n)
def abre(b, inst, w=375, h=667):
    ctx = b.new_context(timezone_id="America/Sao_Paulo", viewport={"width": w, "height": h}, is_mobile=True, has_touch=True); pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e))); pg.route("**/estoque.json*", lambda r: r.fulfill(status=200, content_type="application/json", body=FX))
    pg.clock.set_fixed_time(datetime.fromisoformat(inst)); pg.goto(URL); pg.wait_for_timeout(1300); return ctx, pg, errs
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
    ctx, pg, errs = abre(b, "2026-11-14T15:00:00+00:00")
    r = pg.evaluate("""()=>{ const c={}; ITENS.forEach(x=>{const h=fotoHash(x.f); if(h) c[h]=(c[h]||0)+1;});
      const ruim=ITENS.filter(x=>x.f).filter(x=>fotoIlustrativa(x)!==(c[fotoHash(x.f)]>1)).length;
      const rep=ITENS.find(x=>x.f&&c[fotoHash(x.f)]>1), uni=ITENS.find(x=>x.f&&c[fotoHash(x.f)]===1);
      abrirDetalhe(rep); const dr=document.querySelector('.det-in').textContent.includes('Foto ilustrativa'); fecharDetalhe();
      abrirDetalhe(uni); const du=document.querySelector('.det-in').textContent.includes('Foto ilustrativa'); fecharDetalhe();
      return {ruim, temRep:!!rep, temUni:!!uni, dr, du, nRep:ITENS.filter(x=>x.f&&c[fotoHash(x.f)]>1).length}; }""")
    ck(f"foto repetida em mais de uma unidade marcada como ilustrativa ({r['nRep']} unidades); foto única sem marca", r["ruim"] == 0 and r["temRep"] and r["temUni"] and r["dr"] and not r["du"], r)
    u = pg.evaluate("()=>ITENS.filter(x=>Number(x.q)>0&&Number(x.q)<=2&&x.cond==='novo').slice(0,4).map(x=>{const e=card(x).querySelector('.flag.ult');return (x.q===1?'1:':'2:')+(e?e.textContent.trim():'')})")
    u = [x.split(":", 1)[1] for x in u if (x.startswith("1:") and x.endswith("Última unidade")) or (x.startswith("2:") and x.endswith("Últimas unidades"))] if u and all((x.startswith("1:") and x.endswith("Última unidade")) or (x.startswith("2:") and x.endswith("Últimas unidades")) for x in u) else u and ["errado"] + u
    ck("selo de estoque baixo com concordância ('Última unidade' / 'Últimas unidades')", u and all(x in ("Última unidade", "Últimas unidades") for x in u), u)
    ck("original: sem erro JS", not errs, errs[:2]); ctx.close()
    ctx, pg, errs = abre(b, "2026-11-28T15:00:00+00:00")
    r = pg.evaluate("""()=>{ const t=[...document.querySelectorAll('.camp-i')].map(e=>e.textContent); return {n:t.length, pix:t.every(x=>x.includes('no Pix')), cartao:t.filter(x=>/12x R\\$/.test(x)).length,
      sd:t.filter(x=>x.includes('iPhone 17 Pro')).map(x=>x.includes('de R$'))}; }""")
    ck("Black: carrossel mostra 'no Pix' em todos e a parcela no cartão à parte", r["n"] > 0 and r["pix"] and r["cartao"] > 0, r)
    ck("Black: lacrado sem histórico (sd) aparece sem 'de R$'", r["sd"] == [False], r)
    ck("Black: sem erro JS", not errs, errs[:2]); ctx.close()
    ctx, pg, errs = abre(b, "2026-12-10T15:00:00+00:00")
    r = pg.evaluate("""()=>{ const sec=[...document.querySelectorAll('.camp-sec,section')].find(s=>/Ofertas de Natal/.test(s.textContent))||document.body;
      const black=ITENS.filter(x=>x.pp&&x.pf==='2026-11-30'); return {blackNoNatal:black.filter(x=>sec.textContent.includes(x.modelo)&&sec.textContent.includes(fmt(x.pp))).map(x=>x.modelo),
      blackPreco:black.every(x=>precoAjustado(x)===x.preco), presentear:/Pra presentear/.test(document.body.textContent), neutro:document.querySelectorAll('.camp-ft.neutro').length}; }""")
    ck("Natal: nenhum preço da Black aparece (fica o preço normal)", r["blackPreco"] and not r["blackNoNatal"], r)
    ck("Natal: 'Pra presentear' presente; sem foto = quadro neutro", r["presentear"] and r["neutro"] > 0, r)
    ck("Natal: sem erro JS", not errs, errs[:2]); ctx.close()
    for w in (320, 375, 390):
        for inst, nm in (("2026-11-14T15:00:00+00:00", "original"), ("2026-11-28T15:00:00+00:00", "Black"), ("2026-12-10T15:00:00+00:00", "Natal")):
            ctx, pg, errs = abre(b, inst, w, 700)
            r = pg.evaluate("""()=>({docW:document.documentElement.scrollWidth, W:innerWidth,
              cortes:[...document.querySelectorAll('.price,.det-price,.camp-ib .p,.buy,.camp-b a,.camp-b button,.sec,.grp')].filter(e=>e.offsetParent&&e.scrollWidth>e.clientWidth+1).map(e=>e.className+':'+e.textContent.trim().slice(0,30))})""")
            ck(f"{nm} {w}px: página não vaza na horizontal e preços/botões sem corte", r["docW"] <= r["W"] and not r["cortes"], r); ctx.close()
    b.close()
print("RESULTADO FINAL:", "tudo certo" if not falhas else f"{len(falhas)} falha(s): {falhas}")
