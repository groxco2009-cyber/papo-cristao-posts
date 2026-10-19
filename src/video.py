# -*- coding: utf-8 -*-
"""Gera Reels (vídeo vertical 1080x1920) com animação de texto, sem precisar de voz ou rosto."""
import glob
import os
import random
import subprocess

from PIL import Image, ImageDraw

import arte

W, H = 1080, 1920
FPS = 24


def _ease(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def _camada_texto(texto, cor, tamanho, extra=None, cor_extra=None):
    """Cria camada RGBA (W x 800) com texto centralizado."""
    cam = Image.new("RGBA", (W, 800), (0, 0, 0, 0))
    d = ImageDraw.Draw(cam)
    y = arte.texto_centro(d, W, 120, texto, tamanho, cor, max_w=int(W * 0.86))
    if extra:
        arte.texto_centro(d, W, y + 30, extra, 40, cor_extra or cor, negrito=False, italico=True)
    return cam


def _frame_cena(base, camada, y_final, t, dur):
    """Compõe um quadro: texto aparece subindo + fade, e some no final."""
    fade_in = _ease(t / 0.6)
    fade_out = 1.0 if t < dur - 0.4 else max(0.0, (dur - t) / 0.4)
    alpha = fade_in * fade_out
    dy = int((1 - fade_in) * 60)
    cam = camada.copy()
    a = cam.getchannel("A").point(lambda v: int(v * alpha))
    cam.putalpha(a)
    frame = base.copy()
    frame.paste(cam, (0, y_final + dy), cam)
    return frame


def _musica(duracao, saida, pasta_musicas):
    """Usa mp3 da pasta assets/musica se existir; senão gera um fundo suave sintetizado."""
    arquivos = glob.glob(os.path.join(pasta_musicas, "*.mp3")) + glob.glob(os.path.join(pasta_musicas, "*.m4a"))
    if arquivos:
        mus = random.choice(arquivos)
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-stream_loop", "-1", "-i", mus, "-t", f"{duracao}",
               "-af", f"volume=0.5,afade=t=in:d=1,afade=t=out:st={duracao-1.5}:d=1.5", "-c:a", "aac", saida]
    else:
        notas = [130.81, 196.00, 261.63, 329.63, 392.00]
        entradas = []
        for n in notas:
            entradas += ["-f", "lavfi", "-i", f"sine=frequency={n}:duration={duracao}"]
        filtro = (f"amix=inputs={len(notas)}:normalize=0,volume=0.10,lowpass=f=900,"
                  f"tremolo=f=0.35:d=0.4,afade=t=in:d=1.5,afade=t=out:st={duracao-1.8}:d=1.8")
        cmd = ["ffmpeg", "-y", "-loglevel", "error"] + entradas + ["-filter_complex", filtro, "-c:a", "aac", saida]
    subprocess.run(cmd, check=True)


def reel(cenas, tema, idx, caminho, pasta_musicas="assets/musica"):
    pal = arte.PALETAS[idx % len(arte.PALETAS)]
    esc = pal[2] == arte.WHITE
    base = arte.fundo(W, H, pal)
    arte.logo(base, W / 2, 330, 190, claro=esc)
    d = ImageDraw.Draw(base)
    arte.texto_centro(d, W, 480, "Papo Cristão", 80, pal[2])

    # cenas: (camada_texto, duracao, y)
    roteiro = []
    roteiro.append((_camada_texto(arte.ROTULOS.get(tema, "Papo Cristão").upper(), pal[3], 56), 1.6, 800))
    for c in cenas:
        roteiro.append((_camada_texto(c, pal[2], 92), 3.0, 760))
    cta = _camada_texto("Encontre alguém\nque caminha na\nmesma fé", pal[2], 84,
                        "Link na bio · É grátis", pal[4])
    roteiro.append((cta, 4.2, 700))

    total = sum(r[1] for r in roteiro)
    audio = caminho.replace(".mp4", "_audio.m4a")
    _musica(total, audio, pasta_musicas)

    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-i", audio, "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", caminho]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    cta_idx = len(roteiro) - 1
    for i, (camada, dur, y) in enumerate(roteiro):
        n = int(dur * FPS)
        for f in range(n):
            t = f / FPS
            frame_base = base
            frame = _frame_cena(frame_base, camada, y, t, dur if i != cta_idx else dur + 0.4)
            if i == cta_idx:
                # pílula do link aparece no final
                if t > 0.9:
                    arte.pilula_url(frame, 1330, tamanho=44, escuro=not esc)
            proc.stdin.write(frame.tobytes())
    proc.stdin.close()
    proc.wait()
    if proc.returncode != 0:
        raise RuntimeError("ffmpeg falhou ao gerar o reel")
    os.remove(audio)
    return caminho
