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


def buscar_oferta():
  """Busca um produto na API pública do Mercado Livre."""
  termos = [
      "fone bluetooth",
      "smartwatch",
      "air fryer",
      "carregador portatil",
      "caixa de som",
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
            "titulo": item.get("title"),
            "preco": preco_fmt,
            "link": aplicar_afiliado_ml(item.get("permalink")),
            "imagem_url": img if img.startswith("http") else thumb,
        }
  except Exception as e:
    print(f"Erro na busca: {e}")

  # Oferta de segurança
  return {
      "titulo": (
          "Fone de Ouvido Sem Fio Bluetooth TWS - Bateria de Longa Duração"
      ),
      "preco": "R$ 39,90",
      "link": aplicar_afiliado_ml("https://www.mercadolivre.com.br"),
      "imagem_url": (
          "https://http2.mlstatic.com/D_NQ_NP_2X_735878-MLA48821941421_012022-F.jpg"
      ),
  }


def gerar_legenda_html(oferta):
  """Gera texto formatado em HTML seguro para o Telegram."""
  titulo_limpo = (
      oferta["titulo"].replace("<", "&lt;").replace(">", "&gt;")
  )

  if GEMINI_API_KEY:
    prompt = f"""Crie uma legenda super atrativa para canal de ofertas do WhatsApp.

Produto: {titulo_limpo}
Preço: {oferta['preco']}
Link: {oferta['link']}

Regras:
1. Linha 1: Frase curta de impacto com emoji chamativo.
2. Linha 2: Nome do produto e preço.
3. Linha 3: Link de compra.
4. Use texto simples, sem formatação markdown (* ou _)."""

    for modelo in ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]:
      url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={GEMINI_API_KEY}"
      try:
        r = requests.post(
            url,
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=8,
        )
        if r.status_code == 200 and "candidates" in r.json():
          texto_ia = r.json()["candidates"][0]["content"]["parts"][0]["text"]
          return texto_ia.replace("<", "&lt;").replace(">", "&gt;")
      except Exception:
        pass

  return (
      f"🔥 <b>ACHADINHO EM PROMOÇÃO!</b>\n\n"
      f"📦 <b>{titulo_limpo}</b>\n"
      f"💰 Por apenas: <b>{oferta['preco']}</b>\n\n"
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
      "parse_mode": "HTML",
  }

  res = requests.post(url_photo, data=data, timeout=12)

  if res.status_code == 200:
    print("✅ Notificação enviada com sucesso ao Telegram!")
  else:
    print(f"⚠️ Envio com foto falhou (Status {res.status_code}). Tentando apenas texto...")
    url_msg = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    res_msg = requests.post(
        url_msg,
        data={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": legenda,
            "parse_mode": "HTML",
        },
        timeout=10,
    )
    print(f"Status do Envio de Texto: {res_msg.status_code}")
    if res_msg.status_code != 200:
      print(f"Resposta de Erro do Telegram: {res_msg.text}")


def executar():
  print("🚀 Buscando produto...")
  oferta = buscar_oferta()

  print(f"📦 Produto localizado: {oferta['titulo']}")
  legenda = gerar_legenda_html(oferta)
  enviar_telegram(legenda, oferta["imagem_url"])


if __name__ == "__main__":
  executar()
