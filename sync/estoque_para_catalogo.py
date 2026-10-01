#!/usr/bin/env python3
"""Gera o estoque.json do catálogo a partir do estoque do Zicão Gestão.

Uso: python3 sync/estoque_para_catalogo.py <pasta_produtos> <pasta_vendas> [saida]
  - As pastas têm um .json por documento (o nome do arquivo é o id).
  - saida: caminho do estoque.json (padrão: estoque.json na raiz do repo).
    Se passar um .html, grava o estoque.json na mesma pasta dele.

Entra no catálogo tudo que está em estoque, com preço, fora do técnico e sem
a caixinha "Esconder do catálogo". Lacrados iguais viram um card só (sem
mostrar quantidade). Nunca grava custo, IMEI, série ou dados de cliente.
"""
import json, glob, os, re, sys
from collections import Counter
from datetime import datetime, timezone

prod_dir, vend_dir = sys.argv[1], sys.argv[2]
raiz = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
saida = sys.argv[3] if len(sys.argv) > 3 else os.path.join(raiz, "estoque.json")
if saida.endswith(".html"):
    saida = os.path.join(os.path.dirname(saida), "estoque.json")


def carregar(d):
    out = {}
    for f in glob.glob(os.path.join(d, "*.json")):
        out[os.path.basename(f)[:-5]] = json.load(open(f, encoding="utf-8"))
    return out


produtos, vendas = carregar(prod_dir), carregar(vend_dir)
if not produtos:
    sys.exit("ERRO: nenhum produto lido; não vou apagar o catálogo.")
vendidos = {it.get("pid") for v in vendas.values() if v.get("status") != "cancelada" for it in v.get("itens", [])}


def num(v):
    try:
        return float(str(v).replace(",", "."))
    except Exception:
        return 0.0


def limpa(s):
    return re.sub(r"\s+", " ", str(s or "")).strip()


def cap1(s):
    s = limpa(s)
    return s[:1].upper() + s[1:]


APARELHOS = {"iPhone", "Android", "iPad", "Mac"}
APPLE_ACESS = re.compile(r"\b(airpods?|apple\s*watch|apple\s*pencil|airtag|magic\s*(mouse|keyboard|trackpad))\b", re.I)
TABLET = re.compile(r"\b(pad|tab|tablet)\b", re.I)


def secao(p):
    t, nome = p.get("tipo"), p.get("modelo") or ""
    if t in ("iPhone", "iPad", "Mac"):
        return "apple", t
    if t == "Android":
        return "android", "Tablets" if TABLET.search(nome) else "Celulares"
    if APPLE_ACESS.search(nome):
        return "apple", "AirPods e Watch"
    if t == "TV Box":
        return "acessorios", "TV Box"
    cat = limpa(p.get("categoria"))
    return "acessorios", cat if cat and cat != "Outro" else "Outros"


def obs_de(p):
    obs = [limpa(p.get("obs"))] + [limpa(m.get("desc")) for m in (p.get("manut") or []) if m.get("desc")]
    return "; ".join(o for o in obs if o and not re.fullmatch(r"(tudo\s*)?ok|perfeito|sem detalhes?", o, re.I))[:90]


itens, vistos = [], set()
for pid, p in produtos.items():
    if p.get("status") != "estoque" or p.get("tecnico") or p.get("ocultarCatalogo"):
        continue
    preco = round(num(p.get("preco")))
    if preco <= 0:
        continue
    tipo = p.get("tipo") or "Outro"
    unico = tipo in APARELHOS or bool(p.get("imei"))
    if unico and pid in vendidos:
        continue
    if not unico and num(p.get("qtd")) <= 0:
        continue
    s, g = secao(p)
    it = {"s": s, "g": g, "tipo": tipo, "modelo": limpa(p.get("modelo")), "preco": preco}
    if p.get("cor"):
        it["cor"] = cap1(p["cor"])
    if tipo in APARELHOS:
        novo = p.get("condicao") == "Novo lacrado"
        it["cond"] = "novo" if novo else "semi"
        if tipo == "Android" and p.get("marca") and p["marca"] != "Outra":
            it["marca"] = p["marca"]
        if p.get("armazenamento"):
            it["cap"] = limpa(p["armazenamento"])
        if novo:  # lacrados iguais viram um card só
            k = (tipo, it.get("marca"), it["modelo"].lower(), it.get("cap"), (it.get("cor") or "").lower(), preco)
            if k in vistos:
                continue
            vistos.add(k)
        else:
            if num(p.get("bateria")) > 0:
                it["bat"] = int(num(p.get("bateria")))
            o = obs_de(p)
            if o:
                it["obs"] = o
            if p.get("condicao") == "Vitrine / Recondicionado":
                it["vitrine"] = True
    else:
        if p.get("garantiaDias") not in (None, ""):
            it["garDias"] = int(num(p.get("garantiaDias")))
        k = ("acc", it["modelo"].lower(), (it.get("cor") or "").lower(), preco)
        if k in vistos:
            continue
        vistos.add(k)
    itens.append(it)

ORD_S = {"apple": 0, "android": 1, "acessorios": 2}
itens.sort(key=lambda i: (ORD_S[i["s"]], i["g"], i.get("marca") or "", i["modelo"], i["preco"], -i.get("bat", 0), i.get("cor") or ""))

doc = {"atualizado": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "itens": itens}
with open(saida, "w", encoding="utf-8") as f:
    json.dump(doc, f, ensure_ascii=False, separators=(",", ":"))
    f.write("\n")
c = Counter(f'{i["s"]}/{i.get("cond", "-")}' for i in itens)
print(f"estoque.json: {len(itens)} itens", dict(c))
