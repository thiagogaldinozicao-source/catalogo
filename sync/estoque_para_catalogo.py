#!/usr/bin/env python3
"""Gera o estoque.json do catálogo a partir do estoque do Zicão Gestão (cópia da tarefa agendada, v1.121 — 21/11/2026).
Uso: python3 sync_catalogo.py <pasta_produtos> <pasta_vendas> <saida estoque.json> [--fotos <pasta_fotos>] [--config <geral.json>]
Nunca grava custo, IMEI inteiro (só os 4 últimos), série ou dados de cliente. Do config só copia "campanhas".
Promo: manda pn/pp/pi/pf quando a promo já vale ou começa amanhã (Brasília); o navegador troca o preço na data certa.
v1.121: lacrado (novo) sai SEM preço ("cs": 1 → o site mostra "Consulte o valor"); preço do lacrado não vai pro arquivo.
A tarefa agendada NÃO roda esta cópia do repo: o texto do script vai dentro da própria tarefa. Mudou aqui? Atualize lá também."""
import json, glob, os, re, sys, unicodedata, base64, hashlib
from collections import Counter
from datetime import datetime, timezone
from datetime import timedelta
try:
    from zoneinfo import ZoneInfo
    TZ_BR = ZoneInfo("America/Sao_Paulo")
except Exception:  # Python sem banco de fusos: Brasil está fixo em UTC-3 (sem horário de verão desde 2019)
    TZ_BR = timezone(timedelta(hours=-3))

args = sys.argv[1:]
fotos_dir = None
if "--fotos" in args:
    i = args.index("--fotos"); fotos_dir = args[i + 1]; del args[i:i + 2]
config_arq = None  # v1.120: config/geral.json do Gestão (temas Black/Natal); opcional
if "--config" in args:
    i = args.index("--config"); config_arq = args[i + 1]; del args[i:i + 2]
prod_dir, vend_dir, saida = args[0], args[1], args[2]


def hoje_br(agora=None):
    """Data (AAAA-MM-DD) em Brasília. ZICAO_AGORA (ISO com fuso) só pra teste."""
    if agora is None:
        t = os.environ.get("ZICAO_AGORA")
        agora = datetime.fromisoformat(t) if t else datetime.now(timezone.utc)
    return agora.astimezone(TZ_BR).strftime("%Y-%m-%d")


HOJE = hoje_br()
AMANHA = (datetime.strptime(HOJE, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
CAMP_PADRAO = [{"id": "black", "ativo": True, "ini": "2026-11-16", "fim": "2026-11-30"}, {"id": "natal", "ativo": True, "ini": "2026-12-01", "fim": "2026-12-25"}]
LACRADO_CONSULTA = True  # v1.121: lacrado sem preço no catálogo (Thiago 21/11: dólar subindo)


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


def preco_ef(p, dia=None):
    """Preço que vale hoje: promoção se dentro das datas (inclusive), senão o preço normal. Nunca altera o produto."""
    dia = dia or HOJE
    pp = num(p.get("promoPreco"))
    ini, fim = p.get("promoIni") or "", p.get("promoFim") or ""
    pn = num(p.get("preco"))
    return pp if 0 < pp < pn and ini and fim and ini <= dia <= fim else pn  # r5: promo só se menor que o normal


def limpa(s):
    return re.sub(r"\s+", " ", str(s or "")).strip()


def slug(s):
    s = unicodedata.normalize("NFD", str(s or "")).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def cat_id(pid, p, it):
    if it.get("cond") == "novo":
        return "n-" + slug(" ".join(x for x in [it.get("marca"), it["modelo"], it.get("cap"), it.get("cor")] if x))
    if it.get("tipo") not in APARELHOS and not p.get("imei"):
        return "a-" + slug(" ".join(x for x in [it["modelo"], it.get("cor")] if x))
    return pid


def foto_modelo_key(p):
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


itens, vistos = [], {}
for pid, p in produtos.items():
    # r6: aparelho que ainda não chegou fisicamente (anotado na obs.) não aparece como pronta entrega
    if re.search(r"n[aã]o (consta|chegou|foi entregue)|aguardando (entrega|chegar)|cliente (vai )?trazer", (p.get("obs") or ""), re.I):
        continue
    if p.get("status") != "estoque" or p.get("tecnico") or p.get("ocultarCatalogo"):
        continue
    preco = round(preco_ef(p))
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
    if tipo in APARELHOS:
        for extra in (p.get("cor"), p.get("armazenamento")):
            if extra and modelo.lower().endswith(" " + limpa(extra).lower()):
                modelo = modelo[: -len(limpa(extra))].strip()
    it = {"s": s, "g": g, "tipo": tipo, "modelo": modelo, "preco": preco}
    # o próprio catálogo calcula o preço pela data de Brasília no navegador (vira à 00:00, inclusive com a aba aberta).
    # Só manda a promo que já vale ou começa amanhã (não expõe preço de promoção com dias de antecedência).
    pp, pi, pf = num(p.get("promoPreco")), p.get("promoIni") or "", p.get("promoFim") or ""
    if 0 < pp < num(p.get("preco")) and pi and pf and pf >= HOJE and pi <= AMANHA:
        it.update({"pn": round(num(p.get("preco"))), "pp": round(pp), "pi": pi, "pf": pf})
        if not p.get("promoDe"):
            it["sd"] = 1  # r5: sem preço riscado (o Master não marcou histórico real do preço normal)
    if tipo in APARELHOS and p.get("condicao") == "Novo lacrado" and LACRADO_CONSULTA:
        for x in ("pn", "pp", "pi", "pf", "sd"):
            it.pop(x, None)
        it["preco"] = 0; it["cs"] = 1  # v1.121: "Consulte o valor" — o preço do lacrado não vai pro arquivo
    promo_k = (it.get("pp"), it.get("pi"), it.get("pf"), it.get("sd"))  # r5: unidades com promo diferente não se juntam
    if p.get("cor"):
        it["cor"] = cap1(p["cor"])
    if tipo in APARELHOS:
        novo = p.get("condicao") == "Novo lacrado"
        it["cond"] = "novo" if novo else "semi"
        if tipo == "Android" and p.get("marca") and p["marca"] != "Outra":
            it["marca"] = p["marca"]
        if p.get("armazenamento"):
            it["cap"] = limpa(p["armazenamento"])
        if novo:
            k = (tipo, it.get("marca"), it["modelo"].lower(), it.get("cap"), (it.get("cor") or "").lower(), it["preco"], promo_k)
            if k in vistos:
                vistos[k]["q"] = vistos[k].get("q", 1) + 1  # v1.120: quantidade real (indicador "últimas unidades")
                continue
            vistos[k] = it; it["q"] = 1
        else:
            if num(p.get("bateria")) > 0:
                it["bat"] = int(num(p.get("bateria")))
            o = obs_de(p)
            if o:
                it["obs"] = o
            if p.get("condicao") == "Vitrine / Recondicionado":
                it["vitrine"] = True
            for k in ("acomp", "pecas"):
                v = p.get(k)
                l = [limpa(x) for x in (v if isinstance(v, list) else str(v or "").split(",")) if limpa(x)]
                if l:
                    it[k] = l
            imei = re.sub(r"\D", "", str(p.get("imei") or ""))
            if len(imei) >= 4:
                it["k"] = imei[-4:]
    else:
        if p.get("garantiaDias") not in (None, ""):
            it["garDias"] = int(num(p.get("garantiaDias")))
        k = ("acc", it["modelo"].lower(), (it.get("cor") or "").lower(), preco, promo_k)
        if k in vistos:
            vistos[k]["q"] = vistos[k].get("q", 0) + max(1, int(num(p.get("qtd"))))
            continue
        vistos[k] = it; it["q"] = max(1, int(num(p.get("qtd"))))
    it["i"] = cat_id(pid, p, it)
    if it["i"].startswith(("n-", "a-")) and it.get("pp"):
        it["i"] += f'-p{it["pp"]}'  # r5: id único quando o mesmo modelo tem unidade com e sem promo
    fs = None
    if fotos:
        if it.get("cond") == "semi" and p.get("foto"):
            fs = grava_foto(p["foto"])
        fs = fs or grava_foto(foto_modelo_key(p))
    if fs:
        it["f"], it["fg"] = fs
    itens.append(it)

_enc = os.path.join(os.path.dirname(os.path.abspath(saida)), "sync", "encomenda.json")
if os.path.exists(_enc):
    tem = {(i["modelo"].lower(), (i.get("cap") or "").lower(), (i.get("cor") or "").lower()) for i in itens if i.get("cond") == "novo"}
    for e in json.load(open(_enc, encoding="utf-8")).get("itens", []):
        k = (e["modelo"].lower(), (e.get("cap") or "").lower(), (e.get("cor") or "").lower())
        if k in tem or not e.get("preco"):
            continue
        it = {"s": "apple", "g": "iPhone", "tipo": "iPhone", "modelo": e["modelo"], "preco": round(num(e["preco"])),
              "cor": cap1(e["cor"]), "cond": "novo", "cap": e["cap"], "enc": 1}
        if LACRADO_CONSULTA:
            it["preco"] = 0; it["cs"] = 1  # v1.121: encomenda também é lacrado → "Consulte o valor"
        it["i"] = "n-" + slug(" ".join([e["modelo"], e["cap"], e["cor"]]))
        if fotos:
            fs = grava_foto("m-" + slug(" ".join([e["modelo"], e["cor"]])))
            if fs:
                it["f"], it["fg"] = fs
        itens.append(it)

ORD_S = {"apple": 0, "android": 1, "acessorios": 2}
itens.sort(key=lambda i: (ORD_S[i["s"]], i["g"], i.get("marca") or "", i["modelo"], i["preco"], -i.get("bat", 0), i.get("cor") or ""))

if fotos_dir is not None and os.path.isdir(pasta_fotos):
    for nome in os.listdir(pasta_fotos):
        if nome not in fotos_usadas:
            os.remove(os.path.join(pasta_fotos, nome))

campanhas = CAMP_PADRAO
if config_arq and os.path.exists(config_arq):
    try:
        cs = json.load(open(config_arq, encoding="utf-8")).get("campanhas") or []
        campanhas = [{"id": c["id"], "ativo": bool(c.get("ativo", True)), "ini": c["ini"], "fim": c["fim"]} for c in cs if c.get("id") in ("black", "natal") and c.get("ini") and c.get("fim")] or CAMP_PADRAO
    except Exception as e:
        print("aviso: campanhas do config ignoradas:", e)
doc = {"atualizado": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "campanhas": campanhas, "itens": itens}
with open(saida, "w", encoding="utf-8") as f:
    json.dump(doc, f, ensure_ascii=False, separators=(",", ":"))
    f.write("\n")
c = Counter(f'{i["s"]}/{i.get("cond", "-")}' for i in itens)
print(f"estoque.json: {len(itens)} itens", dict(c), f"· {sum(1 for i in itens if i.get('f'))} com foto", f"· {sum(1 for i in itens if i.get('cs'))} lacrados sem preço")
