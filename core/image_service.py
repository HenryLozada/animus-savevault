"""
Servicio de Adquisición, Optimización y Caché de Imágenes en Alta Resolución.
ANIMUS // Abstergo SaveVault - Memory Matrix Image Engine
Proporciona portadas oficiales en ultra alta definición (Hero Art 1920x620, Capsules 616x353)
con caché local en disco y generador procedural holográfico para evitar cualquier espacio en blanco.
"""

import os
import re
import json
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

# Rutas del sistema
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
IMAGES_DIR = DATA_DIR / "game_images"
MANIFEST_PATH = DATA_DIR / "game_images_manifest.json"

# Diccionario curado de identificadores conocidos, nombres alternativos de carpetas y AppIDs oficiales
KNOWN_GAME_MAPPINGS: Dict[str, Dict[str, Any]] = {
    # Unreal Engine / Epic / Nombres de carpetas comunes
    "mgsdelta": {"appid": "2417610", "clean_name": "METAL GEAR SOLID Δ: SNAKE EATER"},
    "silenthill2": {"appid": "2124490", "clean_name": "SILENT HILL 2"},
    "mortalshell2": {"appid": "2584270", "clean_name": "Mortal Shell II"},
    "overcooked2": {"appid": "728880", "clean_name": "Overcooked! 2"},
    "bodycam": {"appid": "2406770", "clean_name": "Bodycam"},
    "biomutant": {"appid": "597820", "clean_name": "BIOMUTANT"},
    "meteorite": {"appid": "2406770", "clean_name": "Meteorite"}, # Fallback a engine art
    "watch_dogs": {"appid": "243470", "clean_name": "Watch Dogs"},
    "watch dogs": {"appid": "243470", "clean_name": "Watch Dogs"},
    
    # Rockstar Games
    "rockstar games: gtav enhanced": {"appid": "271590", "clean_name": "Grand Theft Auto V"},
    "rockstar games: red dead redemption 2": {"appid": "1174180", "clean_name": "Red Dead Redemption 2"},
    "rockstar games: launcher": {"appid": "271590", "clean_name": "Rockstar Games Launcher", "custom_tag": "ROCKSTAR"},
    "rockstar games: social club": {"appid": "271590", "clean_name": "Rockstar Social Club", "custom_tag": "ROCKSTAR"},
    
    # Ubisoft Connect
    "ubisoft game id 4923": {"appid": "582160", "clean_name": "Assassin's Creed Origins"},
    "assassin's creed origins": {"appid": "582160", "clean_name": "Assassin's Creed Origins"},
    
    # PlayStation PC / Sony
    "the last of us part i": {"appid": "1888930", "clean_name": "The Last of Us Part I"},
    "marvel's spider-man remastered": {"appid": "1817070", "clean_name": "Marvel's Spider-Man Remastered"},
    "marvel's spider-man: miles morales": {"appid": "1817190", "clean_name": "Marvel's Spider-Man: Miles Morales"},
    
    # EA & CD Projekt & Respawn
    "star wars jedi: fallen order": {"appid": "1172380", "clean_name": "STAR WARS Jedi: Fallen Order"},
    "cd projekt red": {"appid": "1091500", "clean_name": "CD Projekt Red Vault", "custom_tag": "CDPR"},
    "respawn": {"appid": "1172380", "clean_name": "Respawn Entertainment", "custom_tag": "RESPAWN"},
    
    # Steam Utility AppIDs
    "steam appid 241100": {"appid": "367670", "clean_name": "Controller Companion"},
    "steam appid 7": {"appid": "753", "clean_name": "Steam Matrix Core", "custom_tag": "STEAM"},
    "steam appid 760": {"appid": "753", "clean_name": "Steam Screenshots & Cloud", "custom_tag": "STEAM"},
}


class GameImageService:
    """Motor de resolución, descarga y caché de portadas en HD para Animus SaveVault."""
    
    _manifest: Dict[str, Any] = {}
    _initialized: bool = False

    @classmethod
    def _init_service(cls):
        if cls._initialized:
            return
        IMAGES_DIR.mkdir(parents=True, exist_ok=True)
        if MANIFEST_PATH.exists():
            try:
                with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
                    cls._manifest = json.load(f)
            except Exception:
                cls._manifest = {}
        cls._initialized = True

    @classmethod
    def _save_manifest(cls):
        try:
            with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
                json.dump(cls._manifest, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    @staticmethod
    def clean_game_name(raw_name: str) -> str:
        """Limpia tags de emuladores, repacks y grupos de la scene para optimizar la búsqueda."""
        name = raw_name
        # Remover grupos de scene comunes
        patterns = [
            r"\(.*?repack.*?\)",
            r"\(.*?rune.*?\)",
            r"\(.*?codex.*?\)",
            r"\(.*?skidrow.*?\)",
            r"\(.*?goldberg.*?\)",
            r"\(.*?flt.*?\)",
            r"\(.*?empress.*?\)",
            r"\(.*?fitgirl.*?\)",
            r"\(.*?dodi.*?\)",
            r"\(.*?tenoke.*?\)",
            r"\[.*?\]",
        ]
        for pat in patterns:
            name = re.sub(pat, "", name, flags=re.IGNORECASE)
            
        # Limpiar prefijos de lanzadores o plataformas
        if name.startswith("Rockstar Games:"):
            name = name.replace("Rockstar Games:", "").strip()
            
        name = name.strip()
        # Normalizar caracteres especiales
        name = name.replace("™", "").replace("®", "").replace("Δ", "Delta")
        return name

    @classmethod
    def resolve_appid(cls, raw_name: str, platform: str = "", current_appid: str = "") -> Tuple[Optional[str], str]:
        """Determina el AppID de Steam oficial más preciso para el juego dado."""
        if current_appid and current_appid.isdigit() and int(current_appid) > 100:
            return current_appid, raw_name

        norm_key = raw_name.lower().strip()
        if norm_key in KNOWN_GAME_MAPPINGS:
            data = KNOWN_GAME_MAPPINGS[norm_key]
            return data["appid"], data["clean_name"]

        clean = cls.clean_game_name(raw_name)
        norm_clean = clean.lower().strip()
        if norm_clean in KNOWN_GAME_MAPPINGS:
            data = KNOWN_GAME_MAPPINGS[norm_clean]
            return data["appid"], data["clean_name"]

        # Si tenemos un current_appid numérico (incluso pequeño)
        if current_appid and current_appid.isdigit():
            return current_appid, clean

        # Consultar manifiesto en disco
        cls._init_service()
        if norm_clean in cls._manifest and cls._manifest[norm_clean].get("appid"):
            return cls._manifest[norm_clean]["appid"], clean

        # Buscar en Steam Store Search API (limitado a títulos relevantes)
        if len(clean) >= 3 and not clean.lower().startswith("steam appid"):
            try:
                q = urllib.parse.quote(clean)
                url = f"https://store.steampowered.com/api/storesearch/?term={q}&l=english&cc=US"
                req = urllib.request.Request(url, headers={"User-Agent": "AnimusSaveVault/4.0 (Windows NT 10.0)"})
                with urllib.request.urlopen(req, timeout=1.8) as resp:
                    res_json = json.loads(resp.read().decode("utf-8"))
                    items = res_json.get("items", [])
                    if items:
                        first_id = str(items[0]["id"])
                        cls._manifest[norm_clean] = {"appid": first_id, "resolved_name": items[0]["name"]}
                        cls._save_manifest()
                        return first_id, clean
            except Exception:
                pass

        return None, clean

    @classmethod
    def get_steam_cdn_urls(cls, appid: str) -> Dict[str, str]:
        """Genera URLs directas a los servidores CDN globales de Steam con resolución máxima."""
        cdn = "https://shared.cloudflare.steamstatic.com/store_item_assets/steam/apps"
        return {
            # Hero Banner cinemático de ultra alta definición (1920x620)
            "hero": f"{cdn}/{appid}/library_hero.jpg",
            # Cápsula nítida retina (616x353) - Excelente para cards en formato horizontal
            "capsule": f"{cdn}/{appid}/capsule_616x353.jpg",
            # Poster vertical 2X en ultra resolución (1200x1800)
            "poster": f"{cdn}/{appid}/library_600x900_2x.jpg",
            # Header estándar oficial (460x215)
            "header": f"{cdn}/{appid}/header.jpg"
        }

    @staticmethod
    def generate_procedural_banner(title: str, platform: str = "") -> str:
        """Genera un banner holográfico estilo matriz cibernética Animus / Abstergo en SVG en caso de ausencia de red."""
        clean_title = title.replace("<", "&lt;").replace(">", "&gt;").replace("&", "&amp;")
        words = clean_title.split()
        initials = "".join(w[0] for w in words if w and w[0].isalnum())[:4].upper()
        if not initials:
            initials = "AV"

        # Colores temáticos Animus
        accent = "#00f0ff"
        accent_glow = "rgba(0, 240, 255, 0.4)"
        if "epic" in platform.lower():
            accent = "#ffffff"
            accent_glow = "rgba(255, 255, 255, 0.3)"
        elif "ea" in platform.lower():
            accent = "#ff4d4d"
            accent_glow = "rgba(255, 77, 77, 0.3)"
        elif "repack" in platform.lower():
            accent = "#a855f7"
            accent_glow = "rgba(168, 85, 247, 0.3)"
        elif "ubisoft" in platform.lower():
            accent = "#38bdf8"
            accent_glow = "rgba(56, 189, 248, 0.3)"

        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 240" width="100%" height="100%">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0a0e17"/>
      <stop offset="50%" stop-color="#05070c"/>
      <stop offset="100%" stop-color="#030407"/>
    </linearGradient>
    <linearGradient id="gridGlow" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="{accent}" stop-opacity="0.15"/>
      <stop offset="100%" stop-color="transparent"/>
    </linearGradient>
    <pattern id="matrixGrid" width="24" height="24" patternUnits="userSpaceOnUse">
      <path d="M 24 0 L 0 0 0 24" fill="none" stroke="rgba(255, 255, 255, 0.04)" stroke-width="1"/>
    </pattern>
    <radialGradient id="hologram" cx="80%" cy="40%" r="60%">
      <stop offset="0%" stop-color="{accent}" stop-opacity="0.22"/>
      <stop offset="100%" stop-color="transparent"/>
    </radialGradient>
  </defs>

  <rect width="600" height="240" fill="url(#bg)"/>
  <rect width="600" height="240" fill="url(#matrixGrid)"/>
  <rect width="600" height="240" fill="url(#hologram)"/>
  <rect x="0" y="0" width="600" height="3" fill="{accent}"/>

  <!-- Abstergo Triangular Geometry / Cyber Polygon -->
  <g transform="translate(420, 30) scale(0.85)" opacity="0.18">
    <polygon points="100,0 200,170 0,170" fill="none" stroke="{accent}" stroke-width="3"/>
    <polygon points="100,30 170,150 30,150" fill="none" stroke="{accent}" stroke-width="1.5"/>
    <line x1="100" y1="0" x2="100" y2="170" stroke="{accent}" stroke-width="1"/>
  </g>

  <!-- Hexadecimal Memory Telemetry Matrix -->
  <text x="35" y="45" font-family="'Consolas', 'Courier New', monospace" font-size="10" fill="{accent}" opacity="0.6" letter-spacing="2">// ABSTERGO MEMORY SECTOR</text>
  <text x="35" y="62" font-family="'Consolas', 'Courier New', monospace" font-size="9" fill="#718096" opacity="0.8" letter-spacing="1">HEX: 0x7F8B // {platform.upper()}</text>

  <!-- Big Stylized Initials Monogram -->
  <text x="540" y="195" text-anchor="end" font-family="'Segoe UI', -apple-system, sans-serif" font-size="96" font-weight="900" fill="white" opacity="0.05" letter-spacing="-4">{initials}</text>

  <!-- Central Title Display -->
  <text x="35" y="145" font-family="'Segoe UI', -apple-system, sans-serif" font-size="24" font-weight="800" fill="#ffffff" letter-spacing="0.5">{clean_title[:32]}</text>
  <text x="35" y="172" font-family="'Segoe UI', -apple-system, sans-serif" font-size="12" font-weight="600" fill="{accent}" letter-spacing="3">{platform.upper()}</text>

  <!-- Modern HUD Bottom Line -->
  <line x1="35" y1="192" x2="180" y2="192" stroke="{accent}" stroke-width="2"/>
  <circle cx="180" cy="192" r="3" fill="{accent}"/>
</svg>"""

        encoded = urllib.parse.quote(svg)
        return f"data:image/svg+xml;utf8,{encoded}"

    @classmethod
    def get_game_image_data(
        cls,
        raw_name: str,
        platform: str = "",
        save_path: str = "",
        steam_appid: str = ""
    ) -> Dict[str, str]:
        """
        Retorna la estructura completa de imágenes para un juego:
        - image_url: URL primaria (Hero 1920x620)
        - capsule_url: URL secundaria retina (616x353)
        - poster_url: URL de poster vertical (1200x1800)
        - header_url: URL de header estándar
        - procedural_banner: SVG generado con estética Animus (cero espacios vacíos)
        """
        appid, clean_title = cls.resolve_appid(raw_name, platform, steam_appid)
        procedural = cls.generate_procedural_banner(clean_title or raw_name, platform)

        if appid:
            cdn_urls = cls.get_steam_cdn_urls(appid)
            return {
                "appid": appid,
                "clean_name": clean_title,
                "image_url": cdn_urls["hero"],
                "capsule_url": cdn_urls["capsule"],
                "poster_url": cdn_urls["poster"],
                "header_url": cdn_urls["header"],
                "procedural_banner": procedural
            }
        else:
            return {
                "appid": "",
                "clean_name": clean_title,
                "image_url": procedural,
                "capsule_url": procedural,
                "poster_url": procedural,
                "header_url": procedural,
                "procedural_banner": procedural
            }
