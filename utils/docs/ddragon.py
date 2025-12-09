import requests
import os
from typing import Dict
from dotenv import load_dotenv

load_dotenv()

# optional: use env to pin ddragon version, otherwise fetch latest
DDRAGON_CDN = "https://ddragon.leagueoflegends.com"

def _get_latest_version() -> str:
    try:
        versions = requests.get(f"{DDRAGON_CDN}/api/versions.json", timeout=5).json()
        return versions[0]
    except Exception:
        return os.getenv("DDRAGON_VERSION", "14.5.1")  # fallback

def fetch_champion_ddragon(champion: str) -> Dict[str,str]:
    """
    return dict with keys: basic, stats, skills, full
    champion should be champion key like 'Kassadin' (capitalized)
    """
    ver = _get_latest_version()
    base = f"{DDRAGON_CDN}/cdn/{ver}/data/en_US/champion"
    url = f"{base}/{champion}.json"
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    data = r.json()
    champ_data = data["data"].get(champion)
    if not champ_data:
        return {}

    basic_text = champ_data.get("blurb", "")
    stats = champ_data.get("stats", {})
    stats_text = "\n".join([f"{k}: {v}" for k, v in stats.items()])
    spells = champ_data.get("spells", [])
    spells_text = "\n\n".join([f"{s.get('name','')}: {s.get('description','')}" for s in spells])

    full_text = f"[기본]\n{basic_text}\n\n[능력치]\n{stats_text}\n\n[스킬]\n{spells_text}"
    return {"basic": basic_text, "stats": stats_text, "skills": spells_text, "full": full_text}