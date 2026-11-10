import os
import re
import requests
from bs4 import BeautifulSoup

# Configurações de Ambiente (Secrets)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# Seus Dados de Afiliado
SHOPEE_SUB_ID = "18386940600"
ML_MATT_TOOL = "76918449"
ML_MATT_WORD = "biancavinte3"

def expandir_link(url):
    """Resolve links encurtados para encontrar o domínio real (Shopee ou Mercado Livre)."""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        res = requests.head(url, headers=headers, allow_redirects=True, timeout=5)
        return res.url
    except Exception:
        return url

def injetar_links_afiliado(texto_ou_url):
    """Localiza links da Shopee e Mercado Livre e insere suas tags de comissão."""
    urls = re.findall(r'https?://[^\s]+', texto_ou_url)
    texto_convertido = texto_ou_url

    for url in urls:
        url_limpa = url.rstrip('.,);]')
        url_real = expandir_link(url_limpa)

        if "shopee" in url_real.lower():
            divisor = "&" if "?" in url_real else "?"
            novo_link = f"{url_real}{divisor}sub_id={SHOPEE_SUB_ID}"
            texto_convertido = texto_convertido.replace(url_limpa, novo_link)

        elif "mercadolivre" in url_real.lower() or "mercadolibre" in url_real.lower():
            divisor = "&" if "?" in url_real else "?"
            novo_link = f"{url_real}{divisor}matt_tool={ML_MATT_TOOL}&matt_word={ML_MATT_WORD}"
            texto_convertido = texto_convertido.replace(url_limpa, novo_link)

    return texto_convertido

def buscar_ofertas_promobit():
    """Busca ofertas reais com título, preço, link e imagem em alta definição."""
    url = "https://www.promobit.com.br/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code != 200:
            return None

        soup = BeautifulSoup(res.text, "html.parser")
        cards = soup.find_all("article")

        for card in cards:
            link_tag = card.find("a", href=True)
            img_tag = card.find("img")
            title_tag = card.find(["h2", "h3", "span"])
            price_tag = card.find(string=re.compile(r'R\$\s*\d+'))

            if link_tag and img_tag:
                rel_href = link_tag['href']
                if not rel_href.startswith("http"):
                    link_oferta = f"https://www.promobit.com.br{rel_href}"
                else:
                    link_oferta = rel_href

                imagem_url = img_tag.get("src") or img_tag.get("data-src")
                titulo = title_tag.get_text().strip() if title_tag else "Produto em Promoção"
                preco = price_tag.strip() if price_tag else ""

                if imagem_url and ("shopee" in link_oferta.lower() or "mercadolivre" in link_oferta.lower() or True):
                    return {
                        "titulo": titulo,
                        "preco": preco,
                        "link": link_oferta,
                        "imagem_url": imagem_url
                    }
    except Exception as e:
        print(f"Erro no rastreamento de ofertas: {e}")

    return None

def gerar_chamada_gemini(oferta_info, link_afiliado):
    """Gera a mensagem persuasiva para o canal do WhatsApp através do Gemini AI."""
    if not GEMINI_API_KEY:
        return (
            f"🔥 **{oferta_info['titulo']}**\n\n"
            f"💰 Por apenas: **{oferta_info['preco']}**\n\n"
            f"🛒 Compre aqui: {link_afiliado}"
        )

    prompt = f"""Você é um especialista em Copywriting para canais de ofertas no WhatsApp.
Crie um texto curto, chamativo e impossível de ignorar para a seguinte promoção:

Produto: {oferta_info['titulo']}
Preço: {oferta_info['preco']}
Link Monetizado: {link_afiliado}

Regras:
1. Comece com uma linha de impacto com emoji chamativo (ex: 🔥 OPORTUNIDADE IMPERDÍVEL!, 😱 PREÇO BAIXOU!).
2. Apresente o produto e destaque o valor final em negrito.
3. Coloque uma chamada clara indicando onde clicar para comprar.
4. Mantenha o formato exato para copiar e colar diretamente no WhatsApp.
5. NÃO invente informações que não estão no anúncio."""

    modelos = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
    for modelo in modelos:
        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={GEMINI_API_KEY}"
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        try:
            r = requests.post(endpoint, json=payload, timeout=12)
            dados = r.json()
            if r.status_code == 200 and 'candidates' in dados:
                return dados['candidates'][0]['content']['parts'][0]['text']
        except Exception as e:
            print(f"Falha na tentativa com o modelo {modelo}: {e}")

    return (
        f"🚨 **OFERTA IMPERDÍVEL!**\n\n"
        f"📦 {oferta_info['titulo']}\n"
        f"💵 Por apenas: **{oferta_info['preco']}**\n\n"
        f"👉 Link com desconto: {link_afiliado}"
    )

def enviar_pacote_telegram(texto, imagem_url):
    """Envia a foto da oferta com o texto da chamada em anexo no seu Telegram."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Credenciais do Telegram ausentes.")
        return

    # Tenta enviar a imagem diretamente via URL
    url_photo = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "photo": imagem_url,
        "caption": texto[:1024],
        "parse_mode": "Markdown"
    }
    
    res = requests.post(url_photo, data=payload)
    
    # Se a URL falhar por bloqueio de imagem externa, baixa a imagem e envia via bytes
    if res.status_code != 200:
        try:
            img_bytes = requests.get(imagem_url, timeout=5).content
            files = {'photo': ('imagem.jpg', img_bytes, 'image/jpeg')}
            payload_fallback = {
                "chat_id": TELEGRAM_CHAT_ID,
                "caption": texto[:1024],
                "parse_mode": "Markdown"
            }
            res = requests.post(url_photo, data=payload_fallback, files=files)
        except Exception as e:
            print(f"Erro ao baixar imagem para envio: {e}")
            # Em caso de erro com a imagem, envia só o texto
            url_msg = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            requests.post(url_msg, data={"chat_id": TELEGRAM_CHAT_ID, "text": texto})

    print(f"Notificação entregue no Telegram! Status: {res.status_code}")

def executar():
    print("🔍 Buscando as melhores ofertas...")
    oferta = buscar_ofertas_promobit()
    
    if not oferta:
        print("Nenhuma oferta válida encontrada nesta rodada.")
        return

    print(f"Oferta localizada: {oferta['titulo']}")
    
    # Monetiza o link
    link_afiliado = injetar_links_afiliado(oferta['link'])
    
    # Gera a chamada persuasiva com a IA
    chamada = gerar_chamada_gemini(oferta, link_afiliado)
    
    # Envia a foto + legenda pronta para o seu chat privado do Telegram
    enviar_pacote_telegram(chamada, oferta['imagem_url'])

if __name__ == "__main__":
    executar()
