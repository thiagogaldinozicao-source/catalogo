#!/usr/bin/env python3
"""Atualiza a lista SEMINOVOS do index.html com o estoque do Zicão Gestão.

Uso: python3 sync/estoque_para_catalogo.py <pasta_produtos> <pasta_vendas> [index.html]
As pastas têm um .json por documento (o nome do arquivo é o id).
Só mexe na lista SEMINOVOS. A lista NOVOS (lacrados/encomenda) continua manual.
"""
import json, glob, os, re, sys

prod_dir, vend_dir = sys.argv[1], sys.argv[2]
html_path = sys.argv[3] if len(sys.argv) > 3 else os.path.join(os.path.dirname(__file__), "..", "index.html")

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
    try: return float(str(v).replace(",", "."))
    except: return 0.0

def modelo_cat(m):
    m = re.sub(r"^\s*iphone\s*", "", str(m or ""), flags=re.I).strip()
    m = re.sub(r"^SE\s*\(.*\)$", "SE", m)
    return m

def limpa(s):
    return re.sub(r"\s+", " ", str(s or "")).strip().replace("\\", "").replace('"', "'")

itens = []
for pid, p in produtos.items():
    if p.get("tipo") != "iPhone" or p.get("condicao") != "Seminovo": continue
    if p.get("status") != "estoque" or p.get("tecnico") or pid in vendidos: continue
    preco = round(num(p.get("preco")))
    if preco <= 0: continue
    obs = [limpa(p.get("obs"))] + [limpa(m.get("desc")) for m in (p.get("manut") or []) if m.get("desc")]
    obs = "; ".join(o for o in obs if o and not re.fullmatch(r"(tudo\s*)?ok|perfeito|sem detalhes?", o, re.I))[:80]
    itens.append(dict(modelo=modelo_cat(p.get("modelo")), bat=int(num(p.get("bateria"))), cap=limpa(p.get("armazenamento")),
                      cor=(lambda c: c[:1].upper() + c[1:])(limpa(p.get("cor"))), preco=f"{preco:,}".replace(",", "."), obs=obs))

itens.sort(key=lambda i: (i["modelo"], int(i["preco"].replace(".", "")), -i["bat"], i["cor"]))
linhas = []
for i in itens:
    s = f'{{modelo:"{i["modelo"]}", bat:{i["bat"]}, cap:"{i["cap"]}", cor:"{i["cor"]}", preco:"{i["preco"]}"'
    if i["obs"]: s += f', obs:"{i["obs"]}"'
    linhas.append(s + "},")

html = open(html_path, encoding="utf-8").read()
ini = html.index("const SEMINOVOS = [")
fim = html.index("];", ini)
novo = html[:ini] + "const SEMINOVOS = [\n" + "\n".join(linhas) + "\n" + html[fim:]
open(html_path, "w", encoding="utf-8").write(novo)
print(f"SEMINOVOS atualizado: {len(itens)} aparelhos")
