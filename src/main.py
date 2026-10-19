# -*- coding: utf-8 -*-
"""
Robô de posts do Papo Cristão.

Uso:
  python src/main.py gerar    --slot 1 [--out out]            -> cria arte/vídeo + legenda
  python src/main.py publicar --slot 1 --base-url https://...  -> publica no Instagram e Facebook
  python src/main.py prever   [--dias 3]                      -> mostra o que será postado
"""
import argparse
import json
import os
import random
import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.dirname(__file__))
import arte  # noqa: E402
import banco  # noqa: E402
import meta  # noqa: E402

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ESTADO = os.path.join(RAIZ, "state.json")
TZ = ZoneInfo("America/Sao_Paulo")

# Agenda diária (horário de Brasília) -> formato
SLOTS = {
    1: ("feed_a", "07:00"),     # bom dia / fé / amor
    2: ("reel", "10:30"),
    3: ("carrossel", "13:00"),
    4: ("feed_b", "18:00"),     # reflexões, dicas, engajamento
    5: ("story", "20:30"),
}

POOL_A = {"bomdia", "fe", "amor", "amizade", "solteiros"}
POOL_NAO_B = {"bomdia", "boanoite"}


# ------------------------------------------------------------------ estado
def carregar_estado():
    if os.path.exists(ESTADO):
        with open(ESTADO, encoding="utf-8") as f:
            return json.load(f)
    return {"ponteiros": {}, "postados": {}}


def salvar_estado(est):
    with open(ESTADO, "w", encoding="utf-8") as f:
        json.dump(est, f, ensure_ascii=False, indent=2)


# ------------------------------------------------------------------ escolha de conteúdo
def _embaralhado(nome, lista):
    r = random.Random(f"papo-{nome}")
    idx = list(range(len(lista)))
    r.shuffle(idx)
    return idx


def pools():
    feed = banco.FEED
    stories = list(banco.STORIES) + [(i[1], i[2], i[0]) for i in feed if i[0] == "boanoite"]
    return {
        "feed_a": [i for i in feed if i[0] in POOL_A],
        "feed_b": [i for i in feed if i[0] not in POOL_A and i[0] not in POOL_NAO_B],
        "carrossel": banco.CARROSSEIS,
        "reel": banco.REELS,
        "story": stories,
    }


def escolher(formato, ponteiro):
    lista = pools()[formato]
    ordem = _embaralhado(formato, lista)
    return lista[ordem[ponteiro % len(ordem)]], ponteiro % len(ordem)


def legenda(corpo, tema, semente):
    r = random.Random(semente)
    cta = r.choice(banco.CTAS).format(link=banco.LINK)
    tags = r.sample(banco.HASHTAGS.get(tema, banco.HASHTAGS["base"]), k=min(3, len(banco.HASHTAGS.get(tema, []))) or 1)
    tags += r.sample(banco.HASHTAGS["base"], k=3)
    tags = list(dict.fromkeys(tags))
    return f"{corpo}\n\n{cta}\n\n{' '.join(tags)}"


def chave_dia(data, slot):
    return f"{data}-{slot}"


# ------------------------------------------------------------------ gerar
def gerar(slot, out, data):
    est = carregar_estado()
    formato, _hora = SLOTS[slot]
    ponteiro = est["ponteiros"].get(formato, 0)
    item, pos = escolher(formato, ponteiro)
    os.makedirs(out, exist_ok=True)
    semente = f"{data}-{slot}"
    idx_visual = ponteiro + slot  # varia a paleta de cores
    info = {"slot": slot, "formato": formato, "data": data, "arquivos": []}

    if formato.startswith("feed"):
        tema, destaque, apoio, corpo = item
        arte.feed(destaque, apoio, tema, idx_visual, os.path.join(out, "post.jpg"))
        info.update(tipo="foto", tema=tema, legenda=legenda(corpo, tema, semente), arquivos=["post.jpg"])
    elif formato == "carrossel":
        pasta = os.path.join(out, "slides")
        os.makedirs(pasta, exist_ok=True)
        caminhos = arte.carrossel(item["capa"], item["slides"], item["tema"], idx_visual, pasta)
        info.update(tipo="carrossel", tema=item["tema"], legenda=legenda(item["legenda"], item["tema"], semente),
                    arquivos=["slides/" + os.path.basename(c) for c in caminhos])
    elif formato == "reel":
        import video
        video.reel(item["cenas"], item["tema"], idx_visual, os.path.join(out, "reel.mp4"),
                   os.path.join(RAIZ, "assets", "musica"))
        info.update(tipo="reel", tema=item["tema"], legenda=legenda(item["legenda"], item["tema"], semente),
                    arquivos=["reel.mp4"])
    elif formato == "story":
        frase, apoio, tema = item
        arte.story(frase, apoio, tema, idx_visual, os.path.join(out, "story.jpg"))
        info.update(tipo="story", tema=tema, legenda="", arquivos=["story.jpg"])

    with open(os.path.join(out, "post.json"), "w", encoding="utf-8") as f:
        json.dump(info, f, ensure_ascii=False, indent=2)
    print(f"[gerar] slot {slot} ({formato}) pronto em {out}")
    print(info.get("legenda", ""))
    return info


# ------------------------------------------------------------------ publicar
def publicar(slot, out, data, base_url, dry):
    est = carregar_estado()
    chave = chave_dia(data, slot)
    status = est["postados"].get(chave, {})
    info = json.load(open(os.path.join(out, "post.json"), encoding="utf-8"))
    tipo, leg = info["tipo"], info["legenda"]
    urls = [f"{base_url.rstrip('/')}/{a}" for a in info["arquivos"]]

    if dry:
        print(f"[DRY-RUN] publicaria {tipo}: {urls}\n{leg}")
        return 0

    token = os.environ["META_TOKEN"]
    ig_id = os.environ.get("IG_USER_ID")
    page_id = os.environ.get("FB_PAGE_ID")
    m = meta.Meta(token, ig_id, page_id)

    for u in urls:
        if not meta.esperar_url(u):
            print(f"ERRO: arquivo não ficou público: {u}")
            return 1

    erros = []
    plataformas = []
    if ig_id:
        plataformas.append(("ig", {"foto": lambda: m.ig_foto(urls[0], leg), "carrossel": lambda: m.ig_carrossel(urls, leg),
                                   "reel": lambda: m.ig_reel(urls[0], leg), "story": lambda: m.ig_story(urls[0])}))
    if page_id:
        plataformas.append(("fb", {"foto": lambda: m.fb_foto(urls[0], leg), "carrossel": lambda: m.fb_carrossel(urls, leg),
                                   "reel": lambda: m.fb_video(urls[0], leg), "story": lambda: m.fb_story(urls[0])}))
    for nome, acoes in plataformas:
        if status.get(nome):
            print(f"[{nome}] já publicado, pulando")
            continue
        try:
            res = acoes[tipo]()
            status[nome] = str(res)
            print(f"[{nome}] publicado: {res}")
        except Exception as e:  # noqa: BLE001
            erros.append(f"{nome}: {e}")
            print(f"[{nome}] ERRO: {e}")

    est["postados"][chave] = status
    if status:  # algo foi publicado: avança a fila deste formato (uma vez só)
        formato = SLOTS[slot][0]
        if not est["postados"][chave].get("_avancou"):
            est["ponteiros"][formato] = est["ponteiros"].get(formato, 0) + 1
            est["postados"][chave]["_avancou"] = True
    # mantém só os últimos 60 dias
    corte = (datetime.now(TZ) - timedelta(days=60)).strftime("%Y-%m-%d")
    est["postados"] = {k: v for k, v in est["postados"].items() if k[:10] >= corte}
    salvar_estado(est)
    return 1 if erros else 0


# ------------------------------------------------------------------ prever
def prever(dias):
    est = carregar_estado()
    pont = dict(est["ponteiros"])
    hoje = datetime.now(TZ).date()
    for d in range(dias):
        dia = hoje + timedelta(days=d)
        print(f"\n=== {dia} ===")
        for slot, (formato, hora) in SLOTS.items():
            item, _ = escolher(formato, pont.get(formato, 0))
            pont[formato] = pont.get(formato, 0) + 1
            if isinstance(item, dict):
                resumo = (item.get("capa") or " / ".join(item["cenas"])).replace("\n", " ")
            else:
                resumo = (item[1] if formato != "story" else item[0]).replace("\n", " ")
            print(f"  {hora}  {formato:10s} {resumo}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("comando", choices=["gerar", "publicar", "prever"])
    ap.add_argument("--slot", type=int, default=1, choices=list(SLOTS))
    ap.add_argument("--out", default="out")
    ap.add_argument("--base-url", default="")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--dias", type=int, default=2)
    ap.add_argument("--data", default=datetime.now(TZ).strftime("%Y-%m-%d"))
    a = ap.parse_args()
    if a.comando == "gerar":
        gerar(a.slot, a.out, a.data)
    elif a.comando == "publicar":
        sys.exit(publicar(a.slot, a.out, a.data, a.base_url, a.dry_run))
    else:
        prever(a.dias)


if __name__ == "__main__":
    main()
