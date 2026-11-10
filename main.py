import os
import re
import requests
from bs4 import BeautifulSoup

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
WHATSAPP_WEBHOOK_URL = os.environ.get("WHATSAPP_WEBHOOK_URL")

# Identificadores de Afiliado
SHOPEE_SUB_ID = "18386940600"
ML_MATT_TOOL = "76918449"
ML_MATT_WORD = "biancavinte3"

# Canal público do Telegram
CANAIS = [
    "https://t.me/s/radar_de_promo"
]

def expandir_url(url):
    """Obtém a URL original do produto caso o link esteja encurtado"""
    try:
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        res = session.head(url, allow_redirects=True, timeout=5)
        return res.url
    except Exception:
        return url

def injetar_afiliado(texto):
    """Anexa as tuas tags de comissão aos links capturados"""
    urls = re.findall(r'https?://[^\s]+', texto)
    texto_convertido = texto

    for url in urls:
        url_limpa = url.rstrip('.,);]')
        url_real = expandir_url(url_limpa)
        
        if "shopee" in url_real.lower():
            divisor = "&" if "?" in url_real else "?"
            novo_link = f"{url_real}{divisor}sub_id={SHOPEE_SUB_ID}"
            texto_convertido = texto_convertido.replace(url_limpa, novo_link)
            
        elif "mercadolivre" in url_real.lower() or "mercadolibre" in url_real.lower():
            divisor = "&" if "?" in url_real else "?"
            novo_link = f"{url_real}{divisor}matt_tool={ML_MATT_TOOL}&matt_word={ML_MATT_WORD}"
            texto_convertido = texto_convertido.replace(url_limpa, novo_link)
            
    return texto_convertido

def obter_oferta_telegram():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    for url in CANAIS:
        try:
            print(f"Buscando ofertas em: {url}")
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, 'html.parser')
                mensagens = soup.find_all("div", class_="tgme_widget_message_text")
                
                # Procura a oferta mais recente que contenha um link
                for msg in reversed(mensagens):
                    texto = msg.get_text(separator="\n").strip()
                    if ("http" in texto or "https" in texto) and len(texto) > 10:
                        print("Oferta capturada com sucesso do teu canal!")
                        return texto
            else:
                print(f"Status HTTP {res.status_code} em {url}")
        except Exception as e:
            print(f"Erro ao ler {url}: {e}")
    return None

def rodar_robo():
    texto_oferta = obter_oferta_telegram()
    if not texto_oferta:
        print("Nenhuma oferta encontrada no canal.")
        return

    texto_com_afiliado = injetar_afiliado(texto_oferta)

    url_gemini = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    prompt = f"""Reescreva a oferta abaixo no formato exato de mensagem viral para o WhatsApp, seguindo rigorosamente a estrutura visual descrita:

[FRASE CURTA E PERSUASIVA EM MAIÚSCULAS COMO TÍTULO]

[EMOJIS RELACIONADOS] [Nome completo/resumido do produto ou kit]

🔥 DE [Preço De/Antigo, se houver] | POR [Preço Por/Atual]
🎟️ CUPOM: [Nome do cupom de desconto, caso exista no texto original]

🔗 [Mantenha a URL de compra exatamente como está]

Regras de formatação:
1. Comece com uma chamada curta, informal e em MAIÚSCULAS (ex: "TU VAI TREINAR TRAJADO", "MENOR PREÇO DO ANO", "PREÇO DE CUSTO").
2. Use emojis adequados ao tipo de produto (ex: camisetas 👕, calçado 👟, tecnologia 📱).
3. Na linha do preço, formate no padrão: 🔥 DE X | POR Y (ou apenas 🔥 POR Y se não houver preço antigo).
4. Se houver cupom no texto original, adicione a linha 🎟️ CUPOM: NOME. Se não houver, omita a linha do cupom.
5. MANTENHA O LINK DE COMPRA EXATAMENTE COMO ESTÁ NO TEXTO ORIGINAL.

Texto original:
{texto_com_afiliado}"""

    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    resposta = requests.post(url_gemini, json=payload)
    dados = resposta.json()
    
    try:
        mensagem_gerada = dados['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        print("Erro ao processar resposta do Gemini:", dados)
        return

    print("--- Mensagem Formatada ---")
    print(mensagem_gerada)

    if WHATSAPP_WEBHOOK_URL:
        resposta_whatsapp = requests.post(WHATSAPP_WEBHOOK_URL, json={"text": mensagem_gerada, "message": mensagem_gerada})
        print("Status do Envio WhatsApp:", resposta_whatsapp.status_code)

if __name__ == "__main__":
    rodar_robo()
