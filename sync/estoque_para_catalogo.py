#!/usr/bin/env python3
"""Gera o estoque.json do catálogo a partir do estoque do Zicão Gestão.

Uso: python3 sync/estoque_para_catalogo.py <pasta_produtos> <pasta_vendas> [saida] [--fotos <pasta_fotos>]
  - --fotos: pasta com a coleção "fotos" do Zicão Gestão. Cada foto vira um .jpg em
    fotos/p/ (miniatura e grande). Foto que não é mais usada é apagada.
  - As pastas têm um .json por documento (o nome do arquivo é o id).
  - saida: caminho do estoque.json (padrão: estoque.json na raiz do repo).
    Se passar um .html, grava o estoque.json na mesma pasta dele.

Entra no catálogo tudo que está em estoque, com preço, fora do técnico e sem
a caixinha "Esconder do catálogo". Lacrados iguais viram um card só (sem
mostrar quantidade). Nunca grava custo, IMEI, série ou dados de cliente.
"""
import json, glob, os, re, sys, unicodedata, base64, hashlib
from collections import Counter
from datetime import datetime, timezone

args = sys.argv[1:]
fotos_dir = None
if "--fotos" in args:
    i = args.index("--fotos"); fotos_dir = args[i + 1]; del args[i:i + 2]
prod_dir, vend_dir = args[0], args[1]
raiz = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
saida = args[2] if len(args) > 2 else os.path.join(raiz, "estoque.json")
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


def slug(s):
    s = unicodedata.normalize("NFD", str(s or "")).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def cat_id(pid, p, it):
    """id do card no link do catálogo (#p-<id>); o Zicão Gestão calcula igual (catId)."""
    if it.get("cond") == "novo":
        return "n-" + slug(" ".join(x for x in [it.get("marca"), it["modelo"], it.get("cap"), it.get("cor")] if x))
    if it.get("tipo") not in APARELHOS and not p.get("imei"):
        return "a-" + slug(" ".join(x for x in [it["modelo"], it.get("cor")] if x))
    return pid


def foto_modelo_key(p):
    """mesma chave do Zicão Gestão (fotoModeloKey): marca (Android) + modelo + cor"""
    marca = p.get("marca") if p.get("tipo") == "Android" and p.get("marca") and p.get("marca") != "Outra" else ""
    return "m-" + slug(" ".join(x for x in [marca, limpa(p.get("modelo")), limpa(p.get("cor"))] if x))


fotos = {}
if fotos_dir and os.path.isdir(fotos_dir):
    for f in glob.glob(os.path.join(fotos_dir, "*.json")):
        try:
            d = json.load(open(f, encoding="utf-8"))
            m = re.match(r"data:image/(jpeg|jpg|png|webp);base64,(.+)$", d.get("img") or "", re.S)
            if m:
                fotos[os.path.basename(f)[:-5]] = (m.group(1).replace("jpeg", "jpg"), base64.b64decode(m.group(2)))
        except Exception:
            pass
pasta_fotos = os.path.join(os.path.dirname(os.path.abspath(saida)), "fotos", "p")
fotos_usadas = set()


def grava_foto(key):
    """grava miniatura e grande; devolve (miniatura, grande) relativos a fotos/"""
    if key not in fotos:
        return None
    out = []
    for k in (key, key + "-g"):
        ext, b = fotos.get(k) or fotos[key]
        nome = f"{k}-{hashlib.sha1(b).hexdigest()[:8]}.{ext}"
        os.makedirs(pasta_fotos, exist_ok=True)
        caminho = os.path.join(pasta_fotos, nome)
        if not os.path.exists(caminho):
            open(caminho, "wb").write(b)
        fotos_usadas.add(nome)
        out.append("p/" + nome)
    return out


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
    modelo = limpa(p.get("modelo"))
    if tipo in APARELHOS:  # cadastro com GB/cor no nome ("iPhone 11 64GB Preto") vira só o modelo, pra cair no grupo certo
        for extra in (p.get("cor"), p.get("armazenamento")):
            if extra and modelo.lower().endswith(" " + limpa(extra).lower()):
                modelo = modelo[: -len(limpa(extra))].strip()
    it = {"s": s, "g": g, "tipo": tipo, "modelo": modelo, "preco": preco}
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
    it["i"] = cat_id(pid, p, it)
    fs = None
    if fotos:
        if it.get("cond") == "semi" and p.get("foto"):
            fs = grava_foto(p["foto"])
        fs = fs or grava_foto(foto_modelo_key(p))
    if fs:
        it["f"], it["fg"] = fs
    itens.append(it)

ORD_S = {"apple": 0, "android": 1, "acessorios": 2}
itens.sort(key=lambda i: (ORD_S[i["s"]], i["g"], i.get("marca") or "", i["modelo"], i["preco"], -i.get("bat", 0), i.get("cor") or ""))

if fotos_dir is not None and os.path.isdir(pasta_fotos):
    for nome in os.listdir(pasta_fotos):
        if nome not in fotos_usadas:
            os.remove(os.path.join(pasta_fotos, nome))

doc = {"atualizado": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "itens": itens}
with open(saida, "w", encoding="utf-8") as f:
    json.dump(doc, f, ensure_ascii=False, separators=(",", ":"))
    f.write("\n")
c = Counter(f'{i["s"]}/{i.get("cond", "-")}' for i in itens)
print(f"estoque.json: {len(itens)} itens", dict(c), f"· {sum(1 for i in itens if i.get('f'))} com foto")
