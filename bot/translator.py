"""6 API с fallback."""
import httpx
import logging
from typing import Tuple, Optional
from langdetect import detect_langs, DetectorFactory, LangDetectException

DetectorFactory.seed = 0

LANGUAGES = {
    "ru": "Russian", "en": "English", "de": "German",
    "fr": "French", "es": "Spanish", "it": "Italian",
    "zh": "Chinese", "ja": "Japanese", "ko": "Korean",
    "uk": "Ukrainian", "pl": "Polish", "pt": "Portuguese",
    "tr": "Turkish", "ar": "Arabic",
}

LANGDETECT_MAP = {"zh-cn": "zh", "zh-tw": "zh", "pt-br": "pt"}
logger = logging.getLogger(__name__)


def detect_language(text: str) -> Tuple[Optional[str], float]:
    if not text or len(text.strip()) < 3:
        return None, 0.0
    try:
        results = detect_langs(text)
        if not results:
            return None, 0.0
        best = results[0]
        lang_code = LANGDETECT_MAP.get(best.lang, best.lang)
        if best.prob < 0.7 or lang_code not in LANGUAGES:
            return None, best.prob
        return lang_code, best.prob
    except LangDetectException as e:
        logger.warning(f"langdetect error: {e}")
        return None, 0.0


async def translate_mymemory(text, source, target, client):
    try:
        params = {"q": text[:500], "langpair": f"{source}|{target}"}
        r = await client.get("https://api.mymemory.translated.net/get", params=params, timeout=10.0)
        if "json" not in r.headers.get("content-type", ""):
            return None
        data = r.json()
        if data.get("responseStatus") == 200:
            t = data["responseData"]["translatedText"]
            if t.strip().lower() != text.strip().lower() or source == target:
                return t
    except Exception as e:
        logger.warning(f"MyMemory: {e}")
    return None


async def translate_google(text, source, target, client):
    try:
        params = {"client": "gtx", "sl": source, "tl": target, "dt": "t", "q": text}
        r = await client.get("https://translate.googleapis.com/translate_a/single", params=params, timeout=10.0)
        data = r.json()
        if data and data[0]:
            return "".join(item[0] for item in data[0] if item[0])
    except Exception as e:
        logger.warning(f"Google: {e}")
    return None


async def translate_libre(text, source, target, client):
    for host in ["https://libretranslate.com", "https://translate.terraprint.co"]:
        try:
            r = await client.post(f"{host}/translate", json={"q": text, "source": source, "target": target}, timeout=8.0)
            data = r.json()
            if data.get("translatedText"):
                return data["translatedText"]
        except Exception as e:
            logger.warning(f"Libre {host}: {e}")
    return None


async def translate_lingva(text, source, target, client):
    for host in ["https://lingva.ml", "https://lingva.thedaviddelta.com"]:
        try:
            r = await client.get(f"{host}/api/v1/{source}/{target}/{text}", timeout=8.0)
            data = r.json()
            if data.get("translation"):
                return data["translation"]
        except Exception as e:
            logger.warning(f"Lingva {host}: {e}")
    return None


async def translate_yandex(text, source, target, client):
    try:
        params = {"id": f"0-{len(text)}-0", "srv": "tr-text", "text": text, "lang": f"{source}-{target}"}
        headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://translate.yandex.ru/"}
        r = await client.get("https://translate.yandex.net/api/v1/tr.json/translate",
                             params=params, headers=headers, timeout=10.0)
        data = r.json()
        if data.get("text"):
            return data["text"][0]
    except Exception as e:
        logger.warning(f"Yandex: {e}")
    return None


PROVIDERS = [
    ("MyMemory", translate_mymemory),
    ("Google", translate_google),
    ("LibreTranslate", translate_libre),
    ("Lingva", translate_lingva),
    ("Yandex", translate_yandex),
]


async def translate_text(text, target_lang, source_lang=None):
    detected_lang = None
    if source_lang is None:
        detected_lang, _ = detect_language(text)
        source_lang = detected_lang or "ru"
    
    async with httpx.AsyncClient(follow_redirects=True) as client:
        for name, func in PROVIDERS:
            try:
                t = await func(text, source_lang, target_lang, client)
                if t and t.strip():
                    return t, "success", detected_lang, name
            except Exception as e:
                logger.warning(f"{name}: {e}")
    
    return "All services unavailable", "error", detected_lang, "None"


def get_languages_list_text():
    lines = ["<b>Supported languages:</b>\n"]
    items = list(LANGUAGES.values())
    for i in range(0, len(items), 2):
        left = items[i]
        right = items[i + 1] if i + 1 < len(items) else ""
        lines.append(f"  {left:<12} {right}")
    return "\n".join(lines)
