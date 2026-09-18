"""
Módulo de integración y detección de plataformas de lanzamiento de videojuegos (Launchers).
Permite descubrir bibliotecas instaladas en Epic Games, GOG Galaxy, EA App, Ubisoft Connect,
Xbox Game Pass y Heroic Launcher para correlacionar y catalogar automáticamente sus partidas.
"""

import os
import re
import json
import winreg
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any

from core.windows_paths import (
    SystemPaths,
    get_epic_manifests_path,
    get_ea_desktop_data_path,
    get_gog_galaxy_storage_path,
    get_heroic_config_path
)

@dataclass
class InstalledLauncherGame:
    name: str
    platform: str
    install_path: Optional[Path] = None
    app_id: Optional[str] = None
    catalog_id: Optional[str] = None
    extra_info: Dict[str, Any] = field(default_factory=dict)

    def normalized_name(self) -> str:
        """Devuelve una versión canónica del nombre para correlaciones seguras."""
        clean = re.sub(r"[^a-zA-Z0-9]", "", self.name.lower())
        return clean

class LauncherDetector:
    def __init__(self):
        self._installed_games: List[InstalledLauncherGame] = []
        self._games_by_norm_name: Dict[str, InstalledLauncherGame] = {}

    def scan_all_launchers(self) -> List[InstalledLauncherGame]:
        """Ejecuta la detección completa en todos los lanzadores compatibles."""
        games: List[InstalledLauncherGame] = []
        
        games.extend(self.detect_epic_games())
        games.extend(self.detect_gog_galaxy())
        games.extend(self.detect_ea_app())
        games.extend(self.detect_ubisoft_connect())
        games.extend(self.detect_xbox_gamepass())
        games.extend(self.detect_heroic_launcher())

        self._installed_games = games
        self._games_by_norm_name = {g.normalized_name(): g for g in games}
        return games

    # Alias for convenience
    detect_all = scan_all_launchers

    def get_installed_games(self) -> List[InstalledLauncherGame]:
        if not self._installed_games:
            self.scan_all_launchers()
        return self._installed_games

    def match_launcher_by_name(self, game_name: str) -> Optional[InstalledLauncherGame]:
        """Intenta asociar un nombre de juego o carpeta con un título de launcher instalado."""
        if not self._installed_games:
            self.scan_all_launchers()

        candidates_to_test = [game_name]
        if ":" in game_name:
            candidates_to_test.append(game_name.split(":", 1)[1].strip())
        if "/" in game_name:
            candidates_to_test.append(game_name.split("/", 1)[1].strip())

        for test_name in candidates_to_test:
            target_norm = re.sub(r"[^a-zA-Z0-9]", "", test_name.lower())
            if not target_norm:
                continue

            alias_target = target_norm.replace("gtav", "grandtheftautov").replace("gta", "grandtheftauto")

            for norm_candidate in [target_norm, alias_target]:
                if norm_candidate in self._games_by_norm_name:
                    return self._games_by_norm_name[norm_candidate]

                for norm_name, game in self._games_by_norm_name.items():
                    alias_norm_name = norm_name.replace("gtav", "grandtheftautov").replace("gta", "grandtheftauto")
                    if len(norm_candidate) >= 4 and len(alias_norm_name) >= 4:
                        if norm_candidate in alias_norm_name or alias_norm_name in norm_candidate:
                            return game

        return None


    # -------------------------------------------------------------------------
    # 1. EPIC GAMES LAUNCHER
    # -------------------------------------------------------------------------
    def detect_epic_games(self) -> List[InstalledLauncherGame]:
        results = []
        manifests_path = get_epic_manifests_path()
        if not manifests_path or not manifests_path.exists():
            return results

        ignored_epic_apps = {
            "unrealengine", "epicgameslauncher", "directx", "vcredist",
            "easyanticheat", "battleye"
        }

        try:
            for item_file in manifests_path.glob("*.item"):
                try:
                    with open(item_file, "r", encoding="utf-8", errors="ignore") as f:
                        data = json.load(f)
                    
                    display_name = data.get("DisplayName")
                    app_name = data.get("AppName", "")
                    install_loc = data.get("InstallLocation")
                    catalog_id = data.get("CatalogItemId", "")

                    if not display_name:
                        continue

                    if app_name.lower() in ignored_epic_apps or display_name.lower() in ignored_epic_apps:
                        continue

                    install_path = Path(install_loc) if install_loc else None

                    results.append(InstalledLauncherGame(
                        name=display_name.strip(),
                        platform="Epic Games",
                        install_path=install_path,
                        app_id=app_name,
                        catalog_id=catalog_id,
                        extra_info={"manifest_file": str(item_file)}
                    ))
                except Exception:
                    continue
        except Exception:
            pass

        return results

    # -------------------------------------------------------------------------
    # 2. GOG GALAXY
    # -------------------------------------------------------------------------
    def detect_gog_galaxy(self) -> List[InstalledLauncherGame]:
        results = []
        seen_ids = set()

        # A) Registro de Windows (HKLM\SOFTWARE\GOG.com\Games o WOW6432Node)
        for root_key in [winreg.HKEY_LOCAL_MACHINE]:
            for subpath in [r"SOFTWARE\GOG.com\Games", r"SOFTWARE\WOW6432Node\GOG.com\Games"]:
                try:
                    with winreg.OpenKey(root_key, subpath) as key:
                        count = winreg.QueryInfoKey(key)[0]
                        for i in range(count):
                            game_id = winreg.EnumKey(key, i)
                            if game_id in seen_ids:
                                continue
                            seen_ids.add(game_id)
                            try:
                                with winreg.OpenKey(key, game_id) as gkey:
                                    name = ""
                                    path_val = ""
                                    for name_attr in ["gameName", "GAMENAME"]:
                                        try:
                                            name, _ = winreg.QueryValueEx(gkey, name_attr)
                                            if name:
                                                break
                                        except Exception:
                                            pass
                                    for path_attr in ["path", "PATH"]:
                                        try:
                                            path_val, _ = winreg.QueryValueEx(gkey, path_attr)
                                            if path_val:
                                                break
                                        except Exception:
                                            pass

                                    if name:
                                        results.append(InstalledLauncherGame(
                                            name=name.strip(),
                                            platform="GOG Galaxy",
                                            install_path=Path(path_val) if path_val else None,
                                            app_id=str(game_id)
                                        ))
                            except Exception:
                                continue
                except Exception:
                    continue

        # B) Base SQLite de Galaxy 2.0 si existe
        storage_path = get_gog_galaxy_storage_path()
        if storage_path:
            db_path = storage_path / "galaxy-2.0.db"
            if db_path.exists():
                try:
                    import sqlite3
                    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
                    cursor = conn.cursor()
                    # Consultar productos instalados de GOG
                    cursor.execute("SELECT productId, title, installationPath FROM InstalledBaseProducts WHERE productId IS NOT NULL")
                    for row in cursor.fetchall():
                        pid = str(row[0])
                        if pid not in seen_ids and row[1]:
                            seen_ids.add(pid)
                            results.append(InstalledLauncherGame(
                                name=str(row[1]).strip(),
                                platform="GOG Galaxy",
                                install_path=Path(row[2]) if row[2] else None,
                                app_id=pid
                            ))
                    conn.close()
                except Exception:
                    pass

        return results

    # -------------------------------------------------------------------------
    # 3. EA APP / ELECTRONIC ARTS / ORIGIN
    # -------------------------------------------------------------------------
    def detect_ea_app(self) -> List[InstalledLauncherGame]:
        results = []
        seen_names = set()

        # A) Metadatos en ProgramData\EA Desktop\InstallData
        ea_data = get_ea_desktop_data_path()
        if ea_data and ea_data.exists():
            try:
                for entry in ea_data.iterdir():
                    if entry.is_dir():
                        title = entry.name.strip()
                        if title.lower() not in seen_names and title.lower() not in {"eadm", "installer"}:
                            seen_names.add(title.lower())
                            results.append(InstalledLauncherGame(
                                name=title,
                                platform="EA App",
                                extra_info={"ea_install_meta": str(entry)}
                            ))
            except Exception:
                pass

        # B) Manifiestos de Origin en ProgramData\Origin\LocalContent
        prog_data = SystemPaths.program_data()
        if prog_data:
            origin_content = prog_data / "Origin" / "LocalContent"
            if origin_content.exists():
                try:
                    for mfst in origin_content.glob("*/*.mfst"):
                        try:
                            # Los directorios contenedores suelen ser el ID del juego
                            game_id = mfst.parent.name
                            if game_id.lower() not in seen_names:
                                seen_names.add(game_id.lower())
                                results.append(InstalledLauncherGame(
                                    name=game_id,
                                    platform="EA App / Origin",
                                    app_id=game_id
                                ))
                        except Exception:
                            continue
                except Exception:
                    pass

        return results

    # -------------------------------------------------------------------------
    # 4. UBISOFT CONNECT
    # -------------------------------------------------------------------------
    def detect_ubisoft_connect(self) -> List[InstalledLauncherGame]:
        results = []
        seen_ids = set()

        for root_key in [winreg.HKEY_LOCAL_MACHINE]:
            for subpath in [r"SOFTWARE\Ubisoft\Launcher\Installs", r"SOFTWARE\WOW6432Node\Ubisoft\Launcher\Installs"]:
                try:
                    with winreg.OpenKey(root_key, subpath) as key:
                        count = winreg.QueryInfoKey(key)[0]
                        for i in range(count):
                            game_id = winreg.EnumKey(key, i)
                            if game_id in seen_ids:
                                continue
                            seen_ids.add(game_id)
                            try:
                                with winreg.OpenKey(key, game_id) as gkey:
                                    install_dir, _ = winreg.QueryValueEx(gkey, "InstallDir")
                                    if install_dir:
                                        p = Path(install_dir)
                                        clean_name = p.name if p.name else f"Ubisoft Game {game_id}"
                                        results.append(InstalledLauncherGame(
                                            name=clean_name,
                                            platform="Ubisoft Connect",
                                            install_path=p,
                                            app_id=str(game_id)
                                        ))
                            except Exception:
                                continue
                except Exception:
                    continue

        return results

    # -------------------------------------------------------------------------
    # 5. XBOX GAME PASS / MICROSOFT STORE
    # -------------------------------------------------------------------------
    def detect_xbox_gamepass(self) -> List[InstalledLauncherGame]:
        results = []
        seen_names = set()

        # A) Carpetas de instalación predeterminadas XboxGames en todas las unidades lógicas
        for drive_letter in "CDEFGHIJKLMNOPQRSTUVWXYZ":
            xbox_dir = Path(f"{drive_letter}:/XboxGames")
            if xbox_dir.exists() and xbox_dir.is_dir():
                try:
                    for entry in xbox_dir.iterdir():
                        if entry.is_dir() and entry.name.lower() not in seen_names:
                            seen_names.add(entry.name.lower())
                            results.append(InstalledLauncherGame(
                                name=entry.name,
                                platform="Xbox Game Pass",
                                install_path=entry
                            ))
                except Exception:
                    pass

        # B) Comprobar paquetes con carpetas WGS en %LOCALAPPDATA%\Packages
        local_appdata = SystemPaths.appdata_local()
        if local_appdata:
            packages_dir = local_appdata / "Packages"
            if packages_dir.exists():
                try:
                    for pkg in packages_dir.glob("*/SystemAppData/wgs"):
                        if pkg.is_dir():
                            pkg_name = pkg.parent.parent.name
                            # Extraer un nombre legible del paquete (ej. Microsoft.FlightSimulator_8wekyb3d8bbwe)
                            clean_name = pkg_name.split("_")[0]
                            # Limpiar prefijos corporativos comunes
                            for prefix in ["Microsoft.", "Bethesda.", "Xbox."]:
                                if clean_name.startswith(prefix):
                                    clean_name = clean_name[len(prefix):]
                            if clean_name.lower() not in seen_names:
                                seen_names.add(clean_name.lower())
                                results.append(InstalledLauncherGame(
                                    name=clean_name,
                                    platform="Xbox Game Pass",
                                    extra_info={"wgs_path": str(pkg)}
                                ))
                except Exception:
                    pass

        return results

    # -------------------------------------------------------------------------
    # 6. HEROIC GAMES LAUNCHER (Epic & GOG Open Source Client)
    # -------------------------------------------------------------------------
    def detect_heroic_launcher(self) -> List[InstalledLauncherGame]:
        results = []
        heroic_path = get_heroic_config_path()
        if not heroic_path or not heroic_path.exists():
            return results

        # 1. Epic cache en Heroic
        epic_cache = heroic_path / "store_cache" / "installed.json"
        if epic_cache.exists():
            try:
                with open(epic_cache, "r", encoding="utf-8", errors="ignore") as f:
                    data = json.load(f)
                    installed = data.get("installed", [])
                    for item in installed:
                        title = item.get("title") or item.get("appName")
                        if title:
                            results.append(InstalledLauncherGame(
                                name=title.strip(),
                                platform="Heroic (Epic)",
                                install_path=Path(item.get("install_path")) if item.get("install_path") else None,
                                app_id=item.get("appName")
                            ))
            except Exception:
                pass

        # 2. GOG cache en Heroic
        gog_cache = heroic_path / "gog_store" / "installed.json"
        if gog_cache.exists():
            try:
                with open(gog_cache, "r", encoding="utf-8", errors="ignore") as f:
                    data = json.load(f)
                    installed = data.get("installed", [])
                    for item in installed:
                        title = item.get("title")
                        if title:
                            results.append(InstalledLauncherGame(
                                name=title.strip(),
                                platform="Heroic (GOG)",
                                install_path=Path(item.get("install_path")) if item.get("install_path") else None,
                                app_id=str(item.get("app_name", ""))
                            ))
            except Exception:
                pass

        return results
