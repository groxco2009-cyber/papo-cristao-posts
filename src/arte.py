# -*- coding: utf-8 -*-
"""Gera as artes (feed, story, carrossel) com a identidade visual do Papo Cristão."""
import math
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

NAVY = (31, 53, 87)
BLUE = (47, 128, 192)
LIGHT_BLUE = (74, 159, 220)
ORANGE = (255, 164, 92)
WHITE = (255, 255, 255)
URL_TXT = "papo-cristao.onrender.com"

# paleta: (topo, base, texto principal, destaque, texto apoio, usa_cartao_claro)
PALETAS = [
    ((234, 243, 252), (253, 233, 214), NAVY, BLUE, (74, 98, 130)),       # marca
    ((31, 53, 87), (47, 128, 192), WHITE, (255, 205, 160), (214, 230, 245)),  # escuro
    ((255, 245, 233), (255, 218, 184), NAVY, (214, 110, 40), (110, 82, 60)),  # pêssego
    ((222, 236, 250), (180, 213, 242), NAVY, (31, 100, 170), (60, 90, 125)),  # azul claro
]

_FONT_DIRS = [
    os.path.join(os.path.dirname(__file__), "..", "assets", "fonts"),
    "/usr/share/fonts/truetype/dejavu",
    "/usr/share/fonts/dejavu",
    "C:/Windows/Fonts",
]


def _find(names):
    for d in _FONT_DIRS:
        for n in names:
            p = os.path.join(d, n)
            if os.path.exists(p):
                return p
    return None


def fonte(tamanho, negrito=True, italico=False):
    if negrito:
        nomes = ["DejaVuSans-Bold.ttf", "arialbd.ttf", "segoeuib.ttf"]
    elif italico:
        nomes = ["DejaVuSans-Oblique.ttf", "ariali.ttf", "segoeuii.ttf"]
    else:
        nomes = ["DejaVuSans.ttf", "arial.ttf", "segoeui.ttf"]
    p = _find(nomes)
    return ImageFont.truetype(p, tamanho) if p else ImageFont.load_default()


def fundo(w, h, paleta):
    top, base = paleta[0], paleta[1]
    img = Image.new("RGB", (w, h), top)
    px = ImageDraw.Draw(img)
    for y in range(h):
        t = y / (h - 1)
        c = tuple(int(top[i] + (base[i] - top[i]) * t) for i in range(3))
        px.line([(0, y), (w, y)], fill=c)
    return img


def _coracao_pontos(cx, cy, size, n=160):
    pts = []
    for i in range(n):
        t = 2 * math.pi * i / n
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append((cx + x * size / 34, cy - y * size / 34))
    return pts


def logo(img, cx, cy, size, claro=False):
    """Coração azul com cruz (balão de conversa)."""
    S = 4
    layer = Image.new("RGBA", (img.width * S, img.height * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    cor = (255, 255, 255, 255) if claro else LIGHT_BLUE + (255,)
    pts = [(x * S, y * S) for x, y in _coracao_pontos(cx, cy, size)]
    d.polygon(pts, fill=cor)
    # cauda do balão
    tail = [(cx - size * 0.28, cy + size * 0.38), (cx - size * 0.52, cy + size * 0.62), (cx - size * 0.05, cy + size * 0.5)]
    d.polygon([(x * S, y * S) for x, y in tail], fill=cor)
    # cruz
    cw = size * 0.11
    ch = size * 0.52
    cruz_cor = BLUE + (255,) if claro else (255, 255, 255, 255)
    d.rounded_rectangle([(cx - cw) * S, (cy - ch * 0.55) * S, (cx + cw) * S, (cy + ch * 0.45) * S], radius=cw * S * 0.4, fill=cruz_cor)
    d.rounded_rectangle([(cx - ch * 0.42) * S, (cy - ch * 0.18) * S, (cx + ch * 0.42) * S, (cy - ch * 0.18 + cw * 1.4) * S], radius=cw * S * 0.3, fill=ORANGE + (255,))
    layer = layer.resize(img.size, Image.LANCZOS)
    img.paste(layer, (0, 0), layer)


def _largura(draw, txt, f):
    b = draw.textbbox((0, 0), txt, font=f)
    return b[2] - b[0]


def texto_centro(draw, w, y, texto, tamanho, cor, negrito=True, italico=False, max_w=None, espaco=1.22):
    """Desenha texto multilinha centralizado, reduzindo a fonte para caber. Retorna y final."""
    max_w = max_w or int(w * 0.84)
    linhas = texto.split("\n")
    f = fonte(tamanho, negrito, italico)
    while tamanho > 20 and max(_largura(draw, l, f) for l in linhas) > max_w:
        tamanho -= 2
        f = fonte(tamanho, negrito, italico)
    for l in linhas:
        lw = _largura(draw, l, f)
        draw.text(((w - lw) / 2, y), l, font=f, fill=cor)
        y += int(tamanho * espaco)
    return y


def pilula_url(img, y, tamanho=40, escuro=True):
    d = ImageDraw.Draw(img)
    f = fonte(tamanho)
    tw = _largura(d, URL_TXT, f)
    pad_x, pad_y = 56, 28
    w = img.width
    x0 = (w - tw) / 2 - pad_x
    x1 = (w + tw) / 2 + pad_x
    y1 = y + tamanho + 2 * pad_y
    d.rounded_rectangle([x0, y, x1, y1], radius=(y1 - y) / 2, fill=NAVY if escuro else WHITE)
    d.text(((w - tw) / 2, y + pad_y - 4), URL_TXT, font=f, fill=WHITE if escuro else NAVY)
    return y1


def _escuro(paleta):
    return paleta[2] == WHITE


def _montar(w, h, paleta, titulo, apoio, topo_logo, y_texto, tam_titulo, y_pilula, rotulo=None):
    img = fundo(w, h, paleta)
    d = ImageDraw.Draw(img)
    esc = _escuro(paleta)
    logo(img, w / 2 - 190, topo_logo, 120, claro=esc)
    d = ImageDraw.Draw(img)
    d.text((w / 2 - 105, topo_logo - 38), "Papo Cristão", font=fonte(66), fill=paleta[2])
    if rotulo:
        f = fonte(30)
        tw = _largura(d, rotulo.upper(), f)
        d.rounded_rectangle([(w - tw) / 2 - 28, y_texto - 100, (w + tw) / 2 + 28, y_texto - 44], radius=28,
                            fill=(20, 38, 66) if esc else (255, 255, 255))
        d.text(((w - tw) / 2, y_texto - 92), rotulo.upper(), font=f, fill=paleta[3])
    y = texto_centro(d, w, y_texto, titulo, tam_titulo, paleta[2])
    if apoio:
        texto_centro(d, w, y + 30, apoio, 42, paleta[4], negrito=False, italico=True)
    pilula_url(img, y_pilula, escuro=not esc)
    return img


ROTULOS = {
    "amor": "Amor cristão", "solteiros": "Solteiros", "amizade": "Amizades", "divorciados": "Recomeço",
    "viuvos": "Acolhimento", "fe": "Palavra", "bomdia": "Bom dia", "boanoite": "Boa noite",
    "encontros": "Encontros", "relacionamento": "Relacionamento", "engajamento": "Participe", "chamada": "Venha",
}


def feed(titulo, apoio, tema, idx, caminho):
    pal = PALETAS[idx % len(PALETAS)]
    img = _montar(1080, 1350, pal, titulo, apoio, 170, 540, 96, 1130, ROTULOS.get(tema))
    img.save(caminho, quality=95)
    return caminho


def story(titulo, apoio, tema, idx, caminho):
    """1080x1920 com margens seguras (topo ~250px e rodapé ~340px livres)."""
    pal = PALETAS[idx % len(PALETAS)]
    img = _montar(1080, 1920, pal, titulo, apoio, 380, 760, 108, 1380, ROTULOS.get(tema))
    d = ImageDraw.Draw(img)
    texto_centro(d, 1080, 1560, "Link na bio", 40, pal[3])
    img.save(caminho, quality=95)
    return caminho


def carrossel(capa, slides, tema, idx, pasta):
    """Retorna lista de caminhos: capa + slides + chamada final."""
    pal = PALETAS[idx % len(PALETAS)]
    esc = _escuro(pal)
    caminhos = []
    total = len(slides) + 2
    # capa
    img = _montar(1080, 1350, pal, capa, "Arraste para o lado  →", 170, 520, 70, 1130, ROTULOS.get(tema))
    p = os.path.join(pasta, "slide_01.jpg")
    img.save(p, quality=95)
    caminhos.append(p)
    # slides
    for i, (t, txt) in enumerate(slides, start=2):
        img = fundo(1080, 1350, pal)
        d = ImageDraw.Draw(img)
        logo(img, 130, 120, 80, claro=esc)
        d = ImageDraw.Draw(img)
        d.text((190, 92), "Papo Cristão", font=fonte(40), fill=pal[2])
        # cartão
        d.rounded_rectangle([80, 300, 1000, 960], radius=48, fill=(255, 255, 255))
        y = texto_centro(d, 1080, 390, t, 80, NAVY, max_w=800)
        # texto do corpo quebrado automaticamente
        corpo = _quebrar(d, txt, fonte(56, False), 780)
        texto_centro(d, 1080, y + 50, corpo, 56, (60, 80, 110), negrito=False, max_w=800, espaco=1.35)
        d.text((960 - _largura(d, f"{i}/{total}", fonte(30)), 1240), f"{i}/{total}", font=fonte(30), fill=pal[4])
        pilula_url(img, 1110, tamanho=34, escuro=not esc)
        p = os.path.join(pasta, f"slide_{i:02d}.jpg")
        img.save(p, quality=95)
        caminhos.append(p)
    # chamada final
    img = _montar(1080, 1350, pal, "Encontre alguém\nque caminha na\nmesma fé", "É grátis e leva menos de 2 minutos", 170, 470, 78, 1130, None)
    p = os.path.join(pasta, f"slide_{total:02d}.jpg")
    img.save(p, quality=95)
    caminhos.append(p)
    return caminhos


def _quebrar(draw, txt, f, max_w):
    palavras = txt.split()
    linhas, atual = [], ""
    for p in palavras:
        teste = (atual + " " + p).strip()
        if _largura(draw, teste, f) <= max_w:
            atual = teste
        else:
            linhas.append(atual)
            atual = p
    if atual:
        linhas.append(atual)
    return "\n".join(linhas)
