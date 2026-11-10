import os
import re
import random
import requests

# Configurações de Ambiente (Secrets)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# Seus Dados de Afiliado
SHOPEE_SUB_ID = "18386940600"
ML_MATT_TOOL = "76918449"
ML_MATT_WORD = "biancavinte3"

def injetar_afiliado_ml(url_original):
    """Injeta suas tags de afiliado no link do Mercado Livre."""
    divisor = "&" if "?" in url_original else "?"
    return f"{url_original}{divisor}matt_tool={ML_MATT_TOOL}&matt_word={ML_MATT_WORD}"

def buscar_oferta_mercadolivre():
    """Busca produtos com desconto diretamente na API do Mercado Livre."""
    # Busca produtos populares em promoção
    termos = ["smartphone", "fone bluetooth", "tv", "air fryer", "smartwatch", "oferta"]
    termo_sorteado = random.choice(termos)
    
    url = f"https://api.mercadolibre.com/sites/MLB/search?q={termo_sorteado}&sort=relevance"
    
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            dados = res.json()
            resultados = dados.get("results", [])
            
            if resultados:
                # Pega um dos primeiros produtos da lista
                item = random.choice(resultados[:5])
                
                titulo = item.get("title")
                preco = item.get("price")
                link_original = item.get("permalink")
                
                # Pega a foto do produto em alta definição
                thumbnail = item.get("thumbnail", "")
                imagem_url = thumbnail.replace("-I.jpg", "-O.jpg").replace("-V.jpg", "-O.jpg")
                if not imagem_url.startswith("http"):
                    imagem_url = thumbnail
                
                preco_formatado = f"R$ {preco:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                link_afiliado = injetar_afiliado_ml(link_original)
                
                return {
                    "titulo": titulo,
                    "preco": preco_formatado,
                    "link": link_afiliado,
                    "imagem_url": imagem_url
                }
    except Exception as e:
        print(f"Erro ao buscar na API do Mercado Livre: {e}")
        
    return None

def gerar_chamada_gemini(oferta_info):
    """Gera o texto promocional chamativo."""
    if not GEMINI_API_KEY:
        return (
            f"🔥 **OFERTA IMPERDÍVEL!**\n\n"
            f"📦 **{oferta_info['titulo']}**\n"
            f"💰 Por apenas: **{oferta_info['preco']}**\n\n"
            f"🛒 Compre aqui com desconto:\n{oferta_info['link']}"
        )

    prompt = f"""Crie um texto curto, chamativo e altamente persuasivo para canal de ofertas do WhatsApp.

Produto: {oferta_info['titulo']}
Preço: {oferta_info['preco']}
Link: {oferta_info['link']}

Regras:
1. Comece com uma frase de impacto usando emoji (ex: 🔥 OPORTUNIDADE IMPERDÍVEL!).
2. Apresente o produto e destaque o preço final em negrito.
3. Coloque uma chamada para ação clara direcionando para o link.
4. Não invente dados fora do anúncio."""

    modelos = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
    for modelo in modelos:
        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={GEMINI_API_KEY}"
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        try:
            r = requests.post(endpoint, json=payload, timeout=10)
            dados = r.json()
            if r.status_code == 200 and 'candidates' in dados:
                return dados['candidates'][0]['content']['parts'][0]['text']
        except Exception as e:
            print(f"Erro Gemini {modelo}: {e}")

    return (
        f"🚨 **PREÇO BAIXOU!**\n\n"
        f"📦 {oferta_info['titulo']}\n"
        f"💵 Por apenas: **{oferta_info['preco']}**\n\n"
        f"👉 Link com desconto: {oferta_info['link']}"
    )

def enviar_telegram(texto, imagem_url):
    """Envia a imagem e a legenda formatada para o seu Telegram."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Tokens do Telegram não encontrados nos Secrets.")
        return

    url_photo = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    
    # Envio com imagem por URL
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "photo": imagem_url,
        "caption": texto[:1024],
        "parse_mode": "Markdown"
    }
    
    res = requests.post(url_photo, data=payload)
    
    # Se falhar o envio por foto, envia como mensagem de texto
    if res.status_code != 200:
        url_msg = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url_msg, data={"chat_id": TELEGRAM_CHAT_ID, "text": texto, "parse_mode": "Markdown"})

    print(f"Status do Envio no Telegram: {res.status_code}")

def executar():
    print("🔍 Buscando ofertas no Mercado Livre...")
    oferta = buscar_oferta_mercadolivre()
    
    if not oferta:
        print("❌ Erro ao obter oferta.")
        return

    print(f"✅ Oferta encontrada: {oferta['titulo']}")
    
    chamada = gerar_chamada_gemini(oferta)
    enviar_telegram(chamada, oferta['imagem_url'])

if __name__ == "__main__":
    executar()
