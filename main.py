import os
import random
import re
import requests

# Credenciais dos Secrets do GitHub
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# Credenciais de Afiliado
SHOPEE_SUB_ID = "18386940600"
ML_MATT_TOOL = "76918449"
ML_MATT_WORD = "biancavinte3"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
}


def aplicar_afiliado_ml(url_original):
  divisor = "&" if "?" in url_original else "?"
  return f"{url_original}{divisor}matt_tool={ML_MATT_TOOL}&matt_word={ML_MATT_WORD}"


def aplicar_afiliado_shopee(url_original):
  divisor = "&" if "?" in url_original else "?"
  return f"{url_original}{divisor}sub_id={SHOPEE_SUB_ID}"


# ==========================================
# OPÇÃO 1: API de Busca Mercado Livre
# ==========================================
def buscar_opcao_1_ml_busca():
  termos = [
      "fone bluetooth",
      "smartwatch",
      "air fryer",
      "carregador portatil",
      "caixa de som",
      "mochila",
      "lampada inteligente",
  ]
  termo = random.choice(termos)

  try:
    url = "https://api.mercadolibre.com/sites/MLB/search"
    res = requests.get(
        url, headers=HEADERS, params={"q": termo, "limit": 10}, timeout=8
    )

    if res.status_code == 200:
      resultados = res.json().get("results", [])
      validos = [r for r in resultados if r.get("price") and r.get("title")]

      if validos:
        item = random.choice(validos[:5])
        preco = item.get("price")
        preco_fmt = (
            f"R$ {preco:,.2f}"
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )

        thumb = item.get("thumbnail", "")
        img = thumb.replace("-I.jpg", "-O.jpg").replace("-V.jpg", "-O.jpg")

        return {
            "fonte": "Mercado Livre (Busca)",
            "titulo": item.get("title"),
            "preco": preco_fmt,
            "link": aplicar_afiliado_ml(item.get("permalink")),
            "imagem_url": img if img.startswith("http") else thumb,
        }
  except Exception as e:
    print(f"Opção 1 falhou: {e}")
  return None


# ==========================================
# OPÇÃO 2: Tendências / Mais Vendidos Mercado Livre
# ==========================================
def buscar_opcao_2_ml_tendencias():
  try:
    url = "https://api.mercadolibre.com/sites/MLB/trends/search"
    res = requests.get(url, headers=HEADERS, timeout=8)

    if res.status_code == 200:
      tendencias = res.json()
      if tendencias:
        palavra_em_alta = random.choice(tendencias[:5]).get("keyword", "ofertas")
        url_busca = "https://api.mercadolibre.com/sites/MLB/search"
        res_busca = requests.get(
            url_busca,
            headers=HEADERS,
            params={"q": palavra_em_alta, "limit": 5},
            timeout=8,
        )

        if res_busca.status_code == 200:
          resultados = res_busca.json().get("results", [])
          if resultados:
            item = resultados[0]
            preco = item.get("price", 0)
            preco_fmt = (
                f"R$ {preco:,.2f}"
                .replace(",", "X")
                .replace(".", ",")
                .replace("X", ".")
            )
            thumb = item.get("thumbnail", "")
            img = thumb.replace("-I.jpg", "-O.jpg")

            return {
                "fonte": "Mercado Livre (Tendências)",
                "titulo": item.get("title"),
                "preco": preco_fmt,
                "link": aplicar_afiliado_ml(item.get("permalink")),
                "imagem_url": img if img.startswith("http") else thumb,
            }
  except Exception as e:
    print(f"Opção 2 falhou: {e}")
  return None


# ==========================================
# OPÇÃO 3: Ofertas Destaque Promobit
# ==========================================
def buscar_opcao_3_promobit():
  try:
    from bs4 import BeautifulSoup

    res = requests.get("https://www.promobit.com.br/", headers=HEADERS, timeout=8)
    if res.status_code == 200:
      soup = BeautifulSoup(res.text, "html.parser")
      cards = soup.find_all("article")

      for card in cards:
        link_tag = card.find("a", href=True)
        img_tag = card.find("img")
        title_tag = card.find(["h2", "h3", "span"])
        price_tag = card.find(string=re.compile(r"R\$\s*\d+"))

        if link_tag and img_tag and title_tag:
          href = link_tag["href"]
          link_final = (
              href
              if href.startswith("http")
              else f"https://www.promobit.com.br{href}"
          )
          img_url = img_tag.get("src") or img_tag.get("data-src")

          if "mercadolivre" in link_final.lower():
            link_monetizado = aplicar_afiliado_ml(link_final)
          elif "shopee" in link_final.lower():
            link_monetizado = aplicar_afiliado_shopee(link_final)
          else:
            link_monetizado = link_final

          return {
              "fonte": "Promobit Web",
              "titulo": title_tag.get_text().strip(),
              "preco": price_tag.strip() if price_tag else "Confira no site",
              "link": link_monetizado,
              "imagem_url": img_url,
          }
  except Exception as e:
    print(f"Opção 3 falhou: {e}")
  return None


# ==========================================
# OPÇÃO 4: Reserva Garantida (Anti-Falha)
# ==========================================
def buscar_opcao_4_reserva():
  print("⚠️ Utilizando Oferta de Reserva Garantida.")
  return {
      "fonte": "Reserva de Segurança",
      "titulo": (
          "Fone de Ouvido Sem Fio Bluetooth TWS - Bateria de Longa Duração"
      ),
      "preco": "R$ 39,90",
      "link": aplicar_afiliado_ml("https://www.mercadolivre.com.br"),
      "imagem_url": (
          "https://http2.mlstatic.com/D_NQ_NP_2X_735878-MLA48821941421_012022-F.jpg"
      ),
  }


def obter_oferta_garantida():
  """Executa em cascata: Opção 1 -> Opção 2 -> Opção 3 -> Opção 4"""
  oferta = buscar_opcao_1_ml_busca()
  if oferta:
    return oferta

  oferta = buscar_opcao_2_ml_tendencias()
  if oferta:
    return oferta

  oferta = buscar_opcao_3_promobit()
  if oferta:
    return oferta

  return buscar_opcao_4_reserva()


def gerar_legenda(oferta):
  if GEMINI_API_KEY:
    prompt = f"""Crie uma legenda super atrativa para postar em canal de ofertas do WhatsApp.

Produto: {oferta['titulo']}
Preço: {oferta['preco']}
Link: {oferta['link']}

Formato desejado:
- Linha 1: Frase curta de impacto com emoji chamativo.
- Linha 2: Nome do produto e preço destacado.
- Linha 3: Chamada clara para comprar com o link.
- Sem enrolação ou introduções."""

    for modelo in ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]:
      url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={GEMINI_API_KEY}"
      try:
        r = requests.post(
            url,
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=10,
        )
        if r.status_code == 200 and "candidates" in r.json():
          return r.json()["candidates"][0]["content"]["parts"][0]["text"]
      except Exception:
        pass

  # Fallback padrão
  return (
      f"🔥 **ACHADINHO EM PROMOÇÃO!**\n\n"
      f"📦 **{oferta['titulo']}**\n"
      f"💰 Por apenas: **{oferta['preco']}**\n\n"
      f"🛒 Compre com desconto aqui:\n{oferta['link']}"
  )


def enviar_telegram(legenda, imagem_url):
  if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
    print("❌ TELEGRAM_TOKEN ou TELEGRAM_CHAT_ID ausentes nos Secrets.")
    return

  url_photo = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
  data = {
      "chat_id": TELEGRAM_CHAT_ID,
      "photo": imagem_url,
      "caption": legenda[:1024],
      "parse_mode": "Markdown",
  }

  res = requests.post(url_photo, data=data, timeout=12)

  if res.status_code != 200:
    url_msg = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(
        url_msg,
        data={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": legenda,
            "parse_mode": "Markdown",
        },
        timeout=10,
    )

  print(f" Status do Envio Telegram: {res.status_code}")


def executar():
  print("🚀 Iniciando busca automática de ofertas...")
  oferta = obter_oferta_garantida()

  print(f" Origem da Oferta: {oferta['fonte']}")
  print(f" Produto: {oferta['titulo']}")

  legenda = gerar_legenda(oferta)
  enviar_telegram(legenda, oferta["imagem_url"])


if __name__ == "__main__":
  executar()
