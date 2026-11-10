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
        except Exception:
            pass
    return None

def gerar_texto_ia(prompt):
    if not GEMINI_API_KEY:
        return None
    modelos = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
    for modelo in modelos:
        url_gemini = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={GEMINI_API_KEY}"
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        try:
            resposta = requests.post(url_gemini, json=payload, timeout=15)
            dados = resposta.json()
            if resposta.status_code == 200 and 'candidates' in dados:
                
