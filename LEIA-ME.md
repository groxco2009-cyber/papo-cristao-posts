# Robô de Posts do Papo Cristão

Todo dia, sozinho, o robô cria e publica **5 conteúdos** no Instagram e na Página do Facebook:

| Horário (Brasília) | Conteúdo |
|---|---|
| 07:00 | Post de imagem (bom dia, fé, amor, amizade) |
| 10:30 | Reel em vídeo |
| 13:00 | Carrossel (várias telas) |
| 18:00 | Post de imagem (reflexão, dica, pergunta) |
| 20:30 | Story |

Os textos vêm do arquivo `src/banco.py` (mais de 50 posts, 14 carrosséis, 22 reels e 20 stories). A ordem é embaralhada e só repete depois de usar tudo. Cada legenda leva uma chamada diferente com o link do site e hashtags variadas.

---

## PASSO 1: Preparar as contas (uma vez só)

1. O Instagram **papocristaoapp** precisa ser conta **Profissional** (Configurações > Tipo de conta > Mudar para conta profissional > Criador ou Empresa).
2. Ligue o Instagram à Página do Facebook do Papo Cristão (Instagram > Editar perfil > Páginas, ou nas configurações da Página > Contas vinculadas).

## PASSO 2: Gerar a chave de acesso da Meta (uma vez só, cerca de 20 min)

1. Entre em **developers.facebook.com** com o seu Facebook e clique em **Meus Apps > Criar app**. Tipo: **Empresa (Business)**. Nome: Papo Cristao Bot.
2. Dentro do app, vá em **Ferramentas > Explorador da API do Graph** (Graph API Explorer).
3. Em "Aplicativo da Meta" escolha o app que criou. Em "Permissões" adicione:
   `instagram_basic`, `instagram_content_publish`, `pages_show_list`, `pages_read_engagement`, `pages_manage_posts`, `business_management`
4. Clique em **Gerar token de acesso**, aceite e selecione a Página e o Instagram do Papo Cristão.
5. Para o token não vencer: vá em **Ferramentas > Depurador de token de acesso**, cole o token e clique em **Estender token de acesso**. Copie o token longo.
6. De volta ao Explorador, cole o token longo e consulte: `me/accounts`. Vai aparecer a sua Página com um `access_token` (esse é o **token da Página, que não expira**) e o `id` (esse é o **FB_PAGE_ID**).
7. Consulte: `ID_DA_PAGINA?fields=instagram_business_account`. O número que aparecer é o **IG_USER_ID**.

Guarde os 3 valores: **META_TOKEN** (token da Página), **FB_PAGE_ID** e **IG_USER_ID**.

> Como o app é seu e a conta é sua, não precisa passar por revisão da Meta.

## PASSO 3: Colocar o robô no GitHub

1. Crie um repositório **público** no GitHub chamado `papo-cristao-posts` (precisa ser público para o GitHub Pages funcionar de graça).
2. Descompacte a pasta deste robô e, no PowerShell, dentro dela:

```
git init
git add .
git commit -m "robo de posts"
git branch -M main
git remote add origin https://github.com/SEU_USUARIO/papo-cristao-posts.git
git push -u origin main
```

3. No repositório: **Settings > Secrets and variables > Actions > New repository secret**. Crie 3 segredos:
   `META_TOKEN`, `IG_USER_ID`, `FB_PAGE_ID` (com os valores do passo 2).
4. **Settings > Pages > Build and deployment > Source: GitHub Actions**.

## PASSO 4: Testar

1. Aba **Actions > Postar no Papo Cristão > Run workflow**, deixe `slot = 1` e **teste marcado**. Ele gera tudo e mostra o que postaria, sem publicar.
2. Se ficou verde, rode de novo com **teste desmarcado** e confira se o post apareceu no Instagram e no Facebook.
3. Pronto. A partir daí ele roda sozinho nos 5 horários, todos os dias.

---

## Dicas importantes

- **Link clicável:** no Instagram, link na legenda não é clicável. Coloque `papo-cristao.onrender.com` na **bio** do perfil (as legendas já dizem "link na bio").
- **Música nos reels:** por padrão o reel leva um fundo musical suave sintetizado. Para músicas melhores, coloque arquivos `.mp3` **livres de direitos autorais** na pasta `assets/musica` (por exemplo, da Biblioteca de Áudio do YouTube). O robô sorteia uma.
- **Mais textos:** abra `src/banco.py`, copie uma linha existente e mude o texto. Se quiser, peça aqui que eu escrevo mais.
- **Como o agendamento funciona:** o robô acorda a cada 30 minutos, vê qual post está na hora (ou atrasado até 5 horas) e publica. Se o GitHub falhar um disparo, o próximo recupera. Os horários dos posts ficam em `src/main.py` (`HORAS`), em horário de Brasília.
- **Execuções vazias:** na aba Actions vão aparecer várias execuções rápidas (uns 15 segundos) por dia. São as vezes em que o robô acordou e não havia post na hora. É normal.
- **GitHub pausa agendamentos** se o repositório ficar 60 dias sem atividade. O robô faz um commit diário (arquivo `state.json`), então isso não deve acontecer.
- **Se der erro de token** (código 190 ou 200): gere o token novamente (passo 2) e atualize o segredo `META_TOKEN`.
- **Ver a prévia da fila:** `python src/main.py prever --dias 3` mostra o que vai ser postado.
- **Contas novas:** nas primeiras semanas, 5 posts por dia é intenso. Se notar queda de alcance, reduza editando as linhas `cron` do `postar.yml`.
