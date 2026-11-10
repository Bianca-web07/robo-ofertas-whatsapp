import os
import feedparser
import requests

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
WHATSAPP_WEBHOOK_URL = os.environ.get("WHATSAPP_WEBHOOK_URL")

# Feeds RSS alternados (Shopee e Mercado Livre) via RSSHub
FEEDS = [
    "https://rsshub.rssforever.com/telegram/channel/promoshopeeoficial",
    "https://rsshub.app/telegram/channel/descontosshopee",
    "https://rsshub.rssforever.com/telegram/channel/ofertasmercadolivre",
    "https://rsshub.app/telegram/channel/promocoesmercadolivre"
]

def obter_item_recente():
    for url in FEEDS:
        try:
            feed = feedparser.parse(url)
            if feed.entries:
                print(f"Ofertas encontradas na fonte: {url}")
                return feed.entries[0]
        except Exception as e:
            print(f"Erro ao tentar ler {url}: {e}")
    return None

def rodar_robo():
    item_recente = obter_item_recente()
    if not item_recente:
        print("Nenhuma oferta encontrada em nenhuma das fontes RSS.")
        return

    titulo = item_recente.get("title", "")
    link = item_recente.get("link", "")
    descricao = item_recente.get("summary", "")

    url_gemini = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    prompt = f"""Reescreva a oferta abaixo no formato de mensagem curta e extremamente persuasiva para um canal do WhatsApp (pode ser Shopee ou Mercado Livre). 
Use emojis atraentes, destaque o desconto e adicione uma chamada para ação clara no final.

Título: {titulo}
Descrição: {descricao}
Link: {link}"""

    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    
    resposta = requests.post(url_gemini, json=payload)
    dados = resposta.json()
    
    try:
        mensagem_gerada = dados['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        print("Erro ao processar resposta do Gemini:", dados)
        return

    print("--- Mensagem Criada ---")
    print(mensagem_gerada)

    # Envio para o WhatsApp via Webhook
    if WHATSAPP_WEBHOOK_URL:
        resposta_whatsapp = requests.post(WHATSAPP_WEBHOOK_URL, json={"text": mensagem_gerada, "message": mensagem_gerada})
        print("Status do Envio WhatsApp:", resposta_whatsapp.status_code)

if __name__ == "__main__":
    rodar_robo()
