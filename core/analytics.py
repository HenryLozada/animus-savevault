"""
Módulo de estadísticas de uso por juego y telemetría de memoria (Animus Analytics).
Procesa metadatos de partidas, actividad reciente y consumo de almacenamiento.
"""

from typing import List, Dict, Any
from datetime import datetime
from core.backup import BackupManager

class AnimusAnalytics:
    @staticmethod
    def get_telemetry(games: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not games:
            return {
                "total_games": 0,
                "total_size_str": "0 MB",
                "top_storage": [],
                "recent_activity": [],
                "platform_distribution": [],
                "extension_stats": [],
                "backups_total": 0
            }

        total_bytes = sum(g.get("total_size", 0) for g in games)
        total_files = sum(g.get("file_count", 0) for g in games)

        # 1. Top 6 juegos más pesados
        sorted_by_size = sorted(games, key=lambda x: x.get("total_size", 0), reverse=True)
        top_storage = []
        for g in sorted_by_size[:6]:
            size = g.get("total_size", 0)
            pct = (size / total_bytes * 100) if total_bytes > 0 else 0
            top_storage.append({
                "name": g.get("name"),
                "size_str": g.get("size_str"),
                "percentage": round(pct, 1),
                "platform": g.get("platform")
            })

        # 2. Juegos con actividad más reciente (Fecha de modificación)
        def parse_date(date_str):
            try:
                return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            except Exception:
                return datetime.min

        sorted_by_date = sorted(games, key=lambda x: parse_date(x.get("last_modified", "")), reverse=True)
        recent_activity = []
        for g in sorted_by_date[:6]:
            recent_activity.append({
                "name": g.get("name"),
                "last_modified": g.get("last_modified"),
                "platform": g.get("platform"),
                "size_str": g.get("size_str")
            })

        # 3. Distribución por Plataforma
        platforms_map = {}
        for g in games:
            p = g.get("platform", "Otro")
            # Normalizar categorías
            cat = "Otros"
            p_lower = p.lower()
            if "repack" in p_lower or "rune" in p_lower or "codex" in p_lower or "goldberg" in p_lower or "skidrow" in p_lower:
                cat = "Repacks / Emuladores"
            elif "steam" in p_lower:
                cat = "Steam Oficial"
            elif "saved games" in p_lower:
                cat = "Saved Games"
            elif "document" in p_lower:
                cat = "Documentos"
            elif "locallow" in p_lower or "unity" in p_lower:
                cat = "Unity / Indie"
            elif "rockstar" in p_lower:
                cat = "Rockstar Games"

            platforms_map[cat] = platforms_map.get(cat, 0) + 1

        platform_distribution = []
        for cat, count in sorted(platforms_map.items(), key=lambda x: x[1], reverse=True):
            pct = round((count / len(games)) * 100, 1)
            platform_distribution.append({
                "category": cat,
                "count": count,
                "percentage": pct
            })

        # 4. Distribución de extensiones de guardado
        ext_map = {}
        for g in games:
            for ext in g.get("extensions", []):
                if ext:
                    ext_map[ext] = ext_map.get(ext, 0) + 1

        top_extensions = []
        for ext, count in sorted(ext_map.items(), key=lambda x: x[1], reverse=True)[:8]:
            top_extensions.append({
                "extension": ext,
                "count": count
            })

        def format_size(b: int) -> str:
            if b < 1024: return f"{b} B"
            elif b < 1024 * 1024: return f"{b / 1024:.1f} KB"
            elif b < 1024 * 1024 * 1024: return f"{b / (1024 * 1024):.1f} MB"
            return f"{b / (1024 * 1024 * 1024):.2f} GB"

        backups = BackupManager.list_backups()

        return {
            "total_games": len(games),
            "total_files": total_files,
            "total_size_bytes": total_bytes,
            "total_size_str": format_size(total_bytes),
            "top_storage": top_storage,
            "recent_activity": recent_activity,
            "platform_distribution": platform_distribution,
            "extension_stats": top_extensions,
            "backups_total": len(backups)
        }
