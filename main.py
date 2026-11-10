import os
import re
import requests
from bs4 import BeautifulSoup

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
WHATSAPP_WEBHOOK_URL = os.environ.get("WHATSAPP_WEBHOOK_URL")

SHOPEE_SUB_ID = "18386940600"
ML_MATT_TOOL = "76918449"
ML_MATT_WORD = "biancavinte3"

CANAIS = [
    "https://t.me/s/radar_de_promo",
    "https://t.me/s/sddescontos"
]

def expandir_url(url):
    try:
        session = requests.Session()
        session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        res = session.head(url, allow_redirects=True, timeout=5)
        return res.url
    except Exception:
        return url

def injetar_afiliado(texto):
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
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    for url in CANAIS:
        try:
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, 'html.parser')
                mensagens = soup.find_all("div", class_="tgme_widget_message_text")
                for msg in reversed(mensagens):
                    texto = msg.get_text(separator="\n").strip()
                    if ("http" in texto or "https" in texto) and len(texto) > 10:
                        return texto
        except Exception as e:
            print(f"Erro ao ler canal {url}: {e}")
    return None

def gerar_texto_ia(prompt):
    if not GEMINI_API_KEY:
        print("Aviso: GEMINI_API_KEY não configurada.")
        return None
    modelos = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
    for modelo in modelos:
        url_gemini = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={GEMINI_API_KEY}"
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        try:
            resposta = requests.post(url_gemini, json=payload, timeout=15)
            dados = resposta.json()
            if resposta.status_code == 200 and 'candidates' in dados:
                return dados['candidates'][0]['content']['parts'][0]['text']
        except Exception as e:
            print(f"Erro no modelo {modelo}: {e}")
    return None

def rodar_robo():
    texto_oferta = obter_oferta_telegram()
    if not texto_oferta:
        print("❌ Nenhuma oferta encontrada.")
        return

    texto_com_afiliado = injetar_afiliado(texto_oferta)

    prompt = f"""Reescreva a oferta abaixo no formato exato de mensagem viral para o WhatsApp:

[FRASE CURTA EM MAIÚSCULAS COMO TÍTULO]

[EMOJIS RELACIONADOS] [Nome do produto]

🔥 DE [Preço Antigo, se houver] | POR [Preço Atual]
🎟️ CUPOM: [Nome do cupom, se houver]

🔗 [Mantenha a URL original exatamente como está]

Texto original:
{texto_com_afiliado}"""

    mensagem_final = gerar_texto_ia(prompt)
    if not mensagem_final:
        mensagem_final = f"🔥 NOVO ACHADINHO EM PROMOÇÃO!\n\n{texto_com_afiliado}"

    print("--- Mensagem Final ---")
    print(mensagem_final)

    if WHATSAPP_WEBHOOK_URL:
        payload_whatsapp = {
            "text": mensagem_final,
            "message": mensagem_final,
            "body": mensagem_final,
            "caption": mensagem_final
        }
        try:
            res = requests.post(WHATSAPP_WEBHOOK_URL, json=payload_whatsapp, timeout=10)
            print("Status do Envio WhatsApp:", res.status_code)
            print("Resposta do Servidor WhatsApp:", res.text)
        except Exception as e:
            print("Erro no envio:", e)

if __name__ == "__main__":
    rodar_robo()
