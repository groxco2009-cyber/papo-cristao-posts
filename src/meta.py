# -*- coding: utf-8 -*-
"""Publicação via API oficial da Meta (Instagram + Página do Facebook)."""
import time

import requests

GRAPH = "https://graph.facebook.com/v21.0"


class MetaErro(Exception):
    pass


class Meta:
    def __init__(self, token, ig_id=None, page_id=None):
        self.token = token
        self.ig_id = ig_id
        self.page_id = page_id

    # ---------------- base ----------------
    def _post(self, caminho, dados):
        dados = dict(dados)
        dados["access_token"] = self.token
        r = requests.post(f"{GRAPH}/{caminho}", data=dados, timeout=120)
        return self._resp(r)

    def _get(self, caminho, params=None):
        params = dict(params or {})
        params["access_token"] = self.token
        r = requests.get(f"{GRAPH}/{caminho}", params=params, timeout=60)
        return self._resp(r)

    @staticmethod
    def _resp(r):
        try:
            j = r.json()
        except Exception:
            raise MetaErro(f"Resposta inválida ({r.status_code}): {r.text[:300]}")
        if r.status_code >= 400 or "error" in j:
            err = j.get("error", j)
            raise MetaErro(f"{err.get('message', err)} (code {err.get('code')}, sub {err.get('error_subcode')})")
        return j

    def _aguardar_container(self, cid, tentativas=60, espera=5):
        for _ in range(tentativas):
            s = self._get(cid, {"fields": "status_code,status"})
            codigo = s.get("status_code")
            if codigo == "FINISHED":
                return
            if codigo in ("ERROR", "EXPIRED"):
                raise MetaErro(f"Container {cid} com erro: {s}")
            time.sleep(espera)
        raise MetaErro(f"Tempo esgotado esperando o container {cid}")

    def _ig_publicar(self, cid):
        self._aguardar_container(cid)
        return self._post(f"{self.ig_id}/media_publish", {"creation_id": cid})["id"]

    # ---------------- Instagram ----------------
    def ig_foto(self, url, legenda):
        c = self._post(f"{self.ig_id}/media", {"image_url": url, "caption": legenda})["id"]
        return self._ig_publicar(c)

    def ig_carrossel(self, urls, legenda):
        filhos = []
        for u in urls:
            c = self._post(f"{self.ig_id}/media", {"image_url": u, "is_carousel_item": "true"})["id"]
            self._aguardar_container(c)
            filhos.append(c)
        c = self._post(f"{self.ig_id}/media", {"media_type": "CAROUSEL", "children": ",".join(filhos), "caption": legenda})["id"]
        return self._ig_publicar(c)

    def ig_reel(self, url, legenda):
        c = self._post(f"{self.ig_id}/media", {"media_type": "REELS", "video_url": url, "caption": legenda,
                                               "share_to_feed": "true"})["id"]
        return self._ig_publicar(c)

    def ig_story(self, url):
        c = self._post(f"{self.ig_id}/media", {"media_type": "STORIES", "image_url": url})["id"]
        return self._ig_publicar(c)

    # ---------------- Facebook (Página) ----------------
    def fb_foto(self, url, legenda):
        return self._post(f"{self.page_id}/photos", {"url": url, "caption": legenda, "published": "true"})["id"]

    def fb_carrossel(self, urls, legenda):
        ids = []
        for u in urls:
            ids.append(self._post(f"{self.page_id}/photos", {"url": u, "published": "false"})["id"])
        dados = {"message": legenda}
        for i, pid in enumerate(ids):
            dados[f"attached_media[{i}]"] = '{"media_fbid":"%s"}' % pid
        return self._post(f"{self.page_id}/feed", dados)["id"]

    def fb_video(self, url, legenda):
        """Tenta publicar como Reel; se falhar, publica como vídeo comum."""
        try:
            ini = self._post(f"{self.page_id}/video_reels", {"upload_phase": "start"})
            vid = ini["video_id"]
            r = requests.post(ini["upload_url"], headers={"Authorization": f"OAuth {self.token}", "file_url": url}, timeout=300)
            self._resp(r)
            for _ in range(40):
                st = self._get(vid, {"fields": "status"}).get("status", {})
                if st.get("uploading_phase", {}).get("status") == "complete":
                    break
                time.sleep(5)
            self._post(f"{self.page_id}/video_reels", {"upload_phase": "finish", "video_id": vid,
                                                       "video_state": "PUBLISHED", "description": legenda})
            return vid
        except Exception:
            return self._post(f"{self.page_id}/videos", {"file_url": url, "description": legenda})["id"]

    def fb_story(self, url):
        pid = self._post(f"{self.page_id}/photos", {"url": url, "published": "false"})["id"]
        res = self._post(f"{self.page_id}/photo_stories", {"photo_id": pid})
        return res.get("post_id", pid)


def esperar_url(url, tentativas=40, espera=6):
    """Espera o arquivo ficar acessível publicamente (a Meta precisa baixar da internet)."""
    for _ in range(tentativas):
        try:
            r = requests.head(url, timeout=20, allow_redirects=True)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(espera)
    return False
