"""
Motor de escaneo inteligente y optimizado de partidas guardadas (Savegame Locator)
Detecta plataformas oficiales, repacks/emuladores y heurística en directorios del sistema.
"""

import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Set, Tuple

from core.windows_paths import (
    SystemPaths,
    get_steam_install_path,
    get_ubisoft_save_path
)
from core.known_games import (
    POPULAR_GAMES,
    GAMES_BY_APPID,
    COMMON_SAVE_EXTENSIONS
)
from core.launchers import LauncherDetector
from core.image_service import GameImageService


IGNORED_DIR_NAMES = {
    "node_modules", ".git", ".vscode", "cache", "temp", "tmp",
    "adobe", "microsoft", "visual studio", "windowspowershell",
    "custom office templates", "zoom", "docker", "android",
    "google", "discord", "spotify", "slack", "outlook", "onenote",
    "my music", "my pictures", "my videos", "savegamebackups",
    "animus_savevault", "animusvault"
}

class SavegameItem:
    def __init__(
        self,
        name: str,
        platform: str,
        save_path: Path,
        file_count: int,
        total_size: int,
        last_modified: datetime,
        extensions: List[str],
        steam_appid: str = "",
        image_url: str = "",
        capsule_url: str = "",
        poster_url: str = "",
        header_url: str = "",
        procedural_banner: str = ""
    ):
        self.name = name
        self.platform = platform
        self.save_path = save_path
        self.file_count = file_count
        self.total_size = total_size
        self.last_modified = last_modified
        self.extensions = extensions
        self.steam_appid = steam_appid
        self.image_url = image_url
        self.capsule_url = capsule_url
        self.poster_url = poster_url
        self.header_url = header_url
        self.procedural_banner = procedural_banner

    def to_dict(self) -> Dict[str, Any]:
        size_str = self.format_size(self.total_size)
        return {
            "name": self.name,
            "platform": self.platform,
            "path": str(self.save_path),
            "file_count": self.file_count,
            "total_size": self.total_size,
            "size_str": size_str,
            "last_modified": self.last_modified.strftime("%Y-%m-%d %H:%M:%S") if self.last_modified else "Desconocida",
            "extensions": self.extensions,
            "steam_appid": self.steam_appid,
            "image_url": self.image_url,
            "capsule_url": self.capsule_url,
            "poster_url": self.poster_url,
            "header_url": self.header_url,
            "procedural_banner": self.procedural_banner
        }

    @staticmethod
    def format_size(bytes_size: int) -> str:
        if bytes_size < 1024:
            return f"{bytes_size} B"
        elif bytes_size < 1024 * 1024:
            return f"{bytes_size / 1024:.1f} KB"
        elif bytes_size < 1024 * 1024 * 1024:
            return f"{bytes_size / (1024 * 1024):.1f} MB"
        else:
            return f"{bytes_size / (1024 * 1024 * 1024):.2f} GB"

class SavegameScanner:
    def __init__(self):
        self.steam_games_cache: Dict[str, str] = {}
        self.launcher_detector = LauncherDetector()
        self._load_steam_installed_game_names()
        try:
            self.launcher_detector.scan_all_launchers()
        except Exception:
            pass


    def _load_steam_installed_game_names(self):
        """Intenta leer los nombres de los juegos desde los archivos appmanifest_*.acf de Steam."""
        steam_path = get_steam_install_path()
        if not steam_path or not steam_path.exists():
            return

        library_paths = [steam_path]
        vdf_path = steam_path / "steamapps" / "libraryfolders.vdf"
        if vdf_path.exists():
            try:
                with open(vdf_path, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        if '"path"' in line.lower():
                            parts = line.strip().split('"')
                            if len(parts) >= 4:
                                p = Path(parts[3])
                                if p.exists() and p not in library_paths:
                                    library_paths.append(p)
            except Exception:
                pass

        for lib in library_paths:
            apps_dir = lib / "steamapps"
            if apps_dir.exists():
                for acf in apps_dir.glob("appmanifest_*.acf"):
                    appid = acf.stem.replace("appmanifest_", "")
                    try:
                        with open(acf, "r", encoding="utf-8", errors="ignore") as f:
                            for line in f:
                                if '"name"' in line:
                                    parts = line.strip().split('"')
                                    if len(parts) >= 4:
                                        self.steam_games_cache[appid] = parts[3]
                                        break
                    except Exception:
                        pass

    def _inspect_directory(self, folder: Path, max_depth: int = 3, max_files: int = 500) -> Tuple[int, int, datetime, List[str]]:
        """Calcula el conteo de archivos, tamaño, fecha más reciente y extensiones de forma rápida."""
        file_count = 0
        total_size = 0
        latest_mod = 0.0
        extensions = set()

        try:
            for root, dirs, files in os.walk(folder):
                rel = Path(root).relative_to(folder)
                
                # Podar carpetas ignoradas o si alcanzamos la profundidad máxima
                if len(rel.parts) >= max_depth:
                    dirs[:] = []
                else:
                    dirs[:] = [d for d in dirs if not d.startswith(".") and d.lower() not in IGNORED_DIR_NAMES]

                for f in files:
                    fp = Path(root) / f
                    try:
                        stat = fp.stat()
                        file_count += 1
                        total_size += stat.st_size
                        if stat.st_mtime > latest_mod:
                            latest_mod = stat.st_mtime
                        ext = fp.suffix.lower()
                        if ext:
                            extensions.add(ext)
                        if file_count >= max_files:
                            break
                    except (PermissionError, FileNotFoundError, OSError):
                        continue
                if file_count >= max_files:
                    break
        except (PermissionError, FileNotFoundError, OSError):
            pass

        mod_date = datetime.fromtimestamp(latest_mod) if latest_mod > 0 else datetime.now()
        return file_count, total_size, mod_date, sorted(list(extensions))

    def _has_save_indicators(self, folder: Path) -> bool:
        """Determina rápidamente si una carpeta contiene guardados."""
        if not folder.exists() or not folder.is_dir():
            return False
        
        folder_lower = folder.name.lower()
        if folder_lower in IGNORED_DIR_NAMES:
            return False

        save_keywords = {"save", "saves", "saved", "savedata", "savegame", "savegames", "profile", "profiles", "gamesaves", "slot"}
        if any(k in folder_lower for k in save_keywords):
            return True

        try:
            entries = list(folder.iterdir())[:30]
            for entry in entries:
                if entry.is_file():
                    if entry.suffix.lower() in COMMON_SAVE_EXTENSIONS:
                        return True
                elif entry.is_dir():
                    if any(k in entry.name.lower() for k in save_keywords):
                        return True
        except (PermissionError, FileNotFoundError, OSError):
            return False
        return False

    def scan_steam_official(self) -> List[SavegameItem]:
        """Escanea partidas guardadas en Steam Cloud / userdata."""
        results = []
        steam_path = get_steam_install_path()
        if not steam_path:
            return results

        userdata_path = steam_path / "userdata"
        if not userdata_path.exists():
            return results

        try:
            for user_dir in userdata_path.iterdir():
                if not user_dir.is_dir() or user_dir.name == "0":
                    continue

                for app_dir in user_dir.iterdir():
                    if not app_dir.is_dir():
                        continue
                    appid = app_dir.name
                    if not appid.isdigit():
                        continue

                    remote_dir = app_dir / "remote"
                    target_dir = remote_dir if remote_dir.exists() else app_dir

                    files, size, mtime, exts = self._inspect_directory(target_dir, max_depth=3)
                    if files == 0:
                        continue

                    game_name = None
                    if appid in GAMES_BY_APPID:
                        game_name = GAMES_BY_APPID[appid].name
                    elif appid in self.steam_games_cache:
                        game_name = self.steam_games_cache[appid]
                    else:
                        game_name = f"Steam AppID {appid}"

                    results.append(SavegameItem(
                        name=game_name,
                        platform="Steam",
                        save_path=target_dir,
                        file_count=files,
                        total_size=size,
                        last_modified=mtime,
                        extensions=exts,
                        steam_appid=appid
                    ))
        except Exception:
            pass

        return results

    def scan_repacks_and_emulators(self) -> List[SavegameItem]:
        results = []
        appdata_roaming = SystemPaths.appdata_roaming()
        appdata_local = SystemPaths.appdata_local()
        public_docs = SystemPaths.public_documents()

        ignored_emu_folders = {"settings", "controller", "depots", "stats", "achievements"}

        # 1. Goldberg SteamEmu
        goldberg_path = appdata_roaming / "Goldberg SteamEmu Saves"
        if goldberg_path.exists():
            try:
                for app_dir in goldberg_path.iterdir():
                    if not app_dir.is_dir() or app_dir.name.lower() in ignored_emu_folders:
                        continue
                    appid = app_dir.name
                    game_name = self._resolve_game_name_by_appid(appid)
                    files, size, mtime, exts = self._inspect_directory(app_dir)
                    if files > 0:
                        results.append(SavegameItem(
                            name=f"{game_name}",
                            platform="Repack / Goldberg",
                            save_path=app_dir,
                            file_count=files,
                            total_size=size,
                            last_modified=mtime,
                            extensions=exts,
                            steam_appid=appid if appid.isdigit() else ""
                        ))
            except Exception:
                pass

        # 2. CODEX en Public Documents
        codex_path = public_docs / "Steam" / "CODEX"
        if codex_path.exists():
            try:
                for app_dir in codex_path.iterdir():
                    if not app_dir.is_dir():
                        continue
                    appid = app_dir.name
                    game_name = self._resolve_game_name_by_appid(appid)
                    files, size, mtime, exts = self._inspect_directory(app_dir)
                    if files > 0:
                        results.append(SavegameItem(
                            name=f"{game_name} (CODEX Repack)",
                            platform="Repack / CODEX",
                            save_path=app_dir,
                            file_count=files,
                            total_size=size,
                            last_modified=mtime,
                            extensions=exts,
                            steam_appid=appid if appid.isdigit() else ""
                        ))
            except Exception:
                pass

        # 3. RUNE en Public Documents
        rune_path = public_docs / "Steam" / "RUNE"
        if rune_path.exists():
            try:
                for app_dir in rune_path.iterdir():
                    if not app_dir.is_dir():
                        continue
                    appid = app_dir.name
                    game_name = self._resolve_game_name_by_appid(appid)
                    files, size, mtime, exts = self._inspect_directory(app_dir)
                    if files > 0:
                        results.append(SavegameItem(
                            name=f"{game_name} (RUNE Repack)",
                            platform="Repack / RUNE",
                            save_path=app_dir,
                            file_count=files,
                            total_size=size,
                            last_modified=mtime,
                            extensions=exts,
                            steam_appid=appid if appid.isdigit() else ""
                        ))
            except Exception:
                pass

        # 4. FLT en AppData Roaming
        flt_path = appdata_roaming / "FLT"
        if flt_path.exists():
            try:
                for app_dir in flt_path.iterdir():
                    if not app_dir.is_dir():
                        continue
                    appid = app_dir.name
                    game_name = self._resolve_game_name_by_appid(appid)
                    files, size, mtime, exts = self._inspect_directory(app_dir)
                    if files > 0:
                        results.append(SavegameItem(
                            name=f"{game_name} (FLT Repack)",
                            platform="Repack / FLT",
                            save_path=app_dir,
                            file_count=files,
                            total_size=size,
                            last_modified=mtime,
                            extensions=exts,
                            steam_appid=appid if appid.isdigit() else ""
                        ))
            except Exception:
                pass

        # 5. EMPRESS en AppData Roaming
        empress_path = appdata_roaming / "EMPRESS"
        if empress_path.exists():
            try:
                for app_dir in empress_path.iterdir():
                    if not app_dir.is_dir():
                        continue
                    appid = app_dir.name
                    game_name = self._resolve_game_name_by_appid(appid)
                    files, size, mtime, exts = self._inspect_directory(app_dir)
                    if files > 0:
                        results.append(SavegameItem(
                            name=f"{game_name} (EMPRESS Repack)",
                            platform="Repack / EMPRESS",
                            save_path=app_dir,
                            file_count=files,
                            total_size=size,
                            last_modified=mtime,
                            extensions=exts,
                            steam_appid=appid if appid.isdigit() else ""
                        ))
            except Exception:
                pass

        # 6. Skidrow en AppData Roaming / Local
        for sk_root in [appdata_roaming / "SKIDROW", appdata_local / "SKIDROW"]:
            if sk_root.exists():
                try:
                    for app_dir in sk_root.iterdir():
                        if not app_dir.is_dir():
                            continue
                        appid = app_dir.name
                        game_name = self._resolve_game_name_by_appid(appid)
                        files, size, mtime, exts = self._inspect_directory(app_dir)
                        if files > 0:
                            results.append(SavegameItem(
                                name=f"{game_name} (Skidrow Repack)",
                                platform="Repack / Skidrow",
                                save_path=app_dir,
                                file_count=files,
                                total_size=size,
                                last_modified=mtime,
                                extensions=exts,
                                steam_appid=appid if appid.isdigit() else ""
                            ))
                except Exception:
                    pass

        return results

    def _resolve_game_name_by_appid(self, appid: str) -> str:
        if not appid or not appid.isdigit():
            return f"Juego ({appid})"

        if appid in GAMES_BY_APPID:
            return GAMES_BY_APPID[appid].name
        if appid in self.steam_games_cache:
            return self.steam_games_cache[appid]

        # Intentar leer desde caché en disco
        cache_file = Path(__file__).parent.parent / "data" / "steam_cache.json"
        if cache_file.exists():
            try:
                import json
                with open(cache_file, "r", encoding="utf-8") as f:
                    disk_cache = json.load(f)
                    if appid in disk_cache:
                        self.steam_games_cache[appid] = disk_cache[appid]
                        return disk_cache[appid]
            except Exception:
                pass

        # Consultar API de Steam de forma rápida
        try:
            import urllib.request
            import json
            req = urllib.request.Request(
                f"https://store.steampowered.com/api/appdetails?appids={appid}",
                headers={"User-Agent": "AnimusSaveVault/1.0"}
            )
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if str(appid) in data and data[str(appid)].get("success"):
                    game_name = data[str(appid)]["data"]["name"]
                    self.steam_games_cache[appid] = game_name
                    # Guardar en disco
                    cache_file.parent.mkdir(parents=True, exist_ok=True)
                    existing = {}
                    if cache_file.exists():
                        try:
                            with open(cache_file, "r", encoding="utf-8") as f:
                                existing = json.load(f)
                        except Exception:
                            pass
                    existing[appid] = game_name
                    with open(cache_file, "w", encoding="utf-8") as f:
                        json.dump(existing, f, indent=2)
                    return game_name
        except Exception:
            pass

        return f"Juego (Steam AppID {appid})"

    def scan_known_catalog(self) -> List[SavegameItem]:
        """Comprueba el catálogo de juegos conocidos."""
        results = []
        saved_games = SystemPaths.saved_games()
        documents = SystemPaths.documents()
        appdata_local = SystemPaths.appdata_local()
        appdata_locallow = SystemPaths.appdata_locallow()
        appdata_roaming = SystemPaths.appdata_roaming()

        for game in POPULAR_GAMES:
            candidates = []
            if game.saved_games_subpath:
                candidates.append((saved_games / game.saved_games_subpath, "Saved Games"))
            if game.documents_subpath:
                candidates.append((documents / game.documents_subpath, "Documentos"))
            if game.appdata_local_subpath:
                candidates.append((appdata_local / game.appdata_local_subpath, "AppData Local"))
            if game.appdata_locallow_subpath:
                candidates.append((appdata_locallow / game.appdata_locallow_subpath, "AppData LocalLow"))
            if game.appdata_roaming_subpath:
                candidates.append((appdata_roaming / game.appdata_roaming_subpath, "AppData Roaming"))

            for path, platform_tag in candidates:
                if path.exists() and path.is_dir():
                    files, size, mtime, exts = self._inspect_directory(path)
                    if files > 0:
                        results.append(SavegameItem(
                            name=game.name,
                            platform=f"{platform_tag}",
                            save_path=path,
                            file_count=files,
                            total_size=size,
                            last_modified=mtime,
                            extensions=exts,
                            steam_appid=game.steam_appid or ""
                        ))
        return results

    def scan_standard_windows_directories(self) -> List[SavegameItem]:
        """Escaneo heurístico optimizado en carpetas típicas."""
        results = []
        discovered_paths: Set[str] = set()

        # 1. Saved Games
        saved_games = SystemPaths.saved_games()
        if saved_games.exists():
            try:
                for entry in saved_games.iterdir():
                    if entry.is_dir() and entry.name.lower() not in IGNORED_DIR_NAMES:
                        files, size, mtime, exts = self._inspect_directory(entry, max_depth=3)
                        if files > 0:
                            item = SavegameItem(
                                name=entry.name,
                                platform="Saved Games",
                                save_path=entry,
                                file_count=files,
                                total_size=size,
                                last_modified=mtime,
                                extensions=exts
                            )
                            results.append(item)
                            discovered_paths.add(str(entry.resolve()).lower())
            except Exception:
                pass

        # 2. Documents\My Games
        my_games = SystemPaths.documents() / "My Games"
        if my_games.exists():
            try:
                for entry in my_games.iterdir():
                    if entry.is_dir() and entry.name.lower() not in IGNORED_DIR_NAMES:
                        saves_sub = entry / "Saves"
                        target = saves_sub if saves_sub.exists() else entry
                        files, size, mtime, exts = self._inspect_directory(target, max_depth=3)
                        if files > 0:
                            path_str = str(target.resolve()).lower()
                            if path_str not in discovered_paths:
                                results.append(SavegameItem(
                                    name=entry.name,
                                    platform="Documents / My Games",
                                    save_path=target,
                                    file_count=files,
                                    total_size=size,
                                    last_modified=mtime,
                                    extensions=exts
                                ))
                                discovered_paths.add(path_str)
            except Exception:
                pass

        # 3. Documents (raíz de Documentos: BioWare, Rockstar Games, etc.)
        docs = SystemPaths.documents()
        if docs.exists():
            try:
                for entry in docs.iterdir():
                    if not entry.is_dir() or entry.name.lower() in IGNORED_DIR_NAMES:
                        continue
                    if entry.name.lower() in {"rockstar games", "bioware", "electronic arts", "wb games", "square enix", "capcom"}:
                        for sub in entry.iterdir():
                            if sub.is_dir():
                                files, size, mtime, exts = self._inspect_directory(sub, max_depth=3)
                                if files > 0:
                                    p_str = str(sub.resolve()).lower()
                                    if p_str not in discovered_paths:
                                        results.append(SavegameItem(
                                            name=f"{entry.name}: {sub.name}",
                                            platform=f"{entry.name}",
                                            save_path=sub,
                                            file_count=files,
                                            total_size=size,
                                            last_modified=mtime,
                                            extensions=exts
                                        ))
                                        discovered_paths.add(p_str)
                    elif self._has_save_indicators(entry):
                        files, size, mtime, exts = self._inspect_directory(entry, max_depth=2)
                        if files > 0:
                            p_str = str(entry.resolve()).lower()
                            if p_str not in discovered_paths:
                                results.append(SavegameItem(
                                    name=entry.name,
                                    platform="Documents",
                                    save_path=entry,
                                    file_count=files,
                                    total_size=size,
                                    last_modified=mtime,
                                    extensions=exts
                                ))
                                discovered_paths.add(p_str)
            except Exception:
                pass

        # 4. AppData\LocalLow
        locallow = SystemPaths.appdata_locallow()
        if locallow.exists():
            try:
                for dev_dir in locallow.iterdir():
                    if dev_dir.is_dir() and dev_dir.name.lower() not in IGNORED_DIR_NAMES:
                        for game_dir in dev_dir.iterdir():
                            if game_dir.is_dir():
                                files, size, mtime, exts = self._inspect_directory(game_dir, max_depth=2)
                                if files > 0 and (any(e in COMMON_SAVE_EXTENSIONS for e in exts) or self._has_save_indicators(game_dir)):
                                    p_str = str(game_dir.resolve()).lower()
                                    if p_str not in discovered_paths:
                                        results.append(SavegameItem(
                                            name=f"{game_dir.name}",
                                            platform="LocalLow (Unity/Indie)",
                                            save_path=game_dir,
                                            file_count=files,
                                            total_size=size,
                                            last_modified=mtime,
                                            extensions=exts
                                        ))
                                        discovered_paths.add(p_str)
            except Exception:
                pass

        # 5. Ubisoft Connect
        ubi_path = get_ubisoft_save_path()
        if ubi_path and ubi_path.exists():
            try:
                ubi_games_map = {g.app_id: g.name for g in self.launcher_detector.detect_ubisoft_connect() if g.app_id}
                for user_dir in ubi_path.iterdir():
                    if user_dir.is_dir():
                        for game_id_dir in user_dir.iterdir():
                            if game_id_dir.is_dir():
                                files, size, mtime, exts = self._inspect_directory(game_id_dir, max_depth=2)
                                if files > 0:
                                    ubi_known = {
                                        "4923": ("Assassin's Creed Origins", "582160"),
                                        "3539": ("Assassin's Creed Odyssey", "812140"),
                                        "5059": ("Assassin's Creed Valhalla", "2208920"),
                                        "1875": ("Watch Dogs 2", "447040"),
                                    }
                                    gid = game_id_dir.name
                                    resolved_name = ubi_games_map.get(gid)
                                    steam_aid = ""
                                    if not resolved_name and gid in ubi_known:
                                        resolved_name, steam_aid = ubi_known[gid]
                                    if not resolved_name:
                                        resolved_name = f"Ubisoft Game ID {gid}"

                                    results.append(SavegameItem(
                                        name=resolved_name,
                                        platform="Ubisoft Connect",
                                        save_path=game_id_dir,
                                        file_count=files,
                                        total_size=size,
                                        last_modified=mtime,
                                        extensions=exts,
                                        steam_appid=steam_aid
                                    ))
            except Exception:
                pass

        return results

    def scan_epic_and_unreal(self) -> List[SavegameItem]:
        """Detecta partidas de juegos de Epic Games y títulos en Unreal Engine en AppData\\Local."""
        results = []
        appdata_local = SystemPaths.appdata_local()
        if not appdata_local or not appdata_local.exists():
            return results

        discovered_paths = set()

        # 1. Escaneo de juegos instalados por Epic Games Launcher
        try:
            epic_installed = self.launcher_detector.detect_epic_games()
            for eg in epic_installed:
                candidates = [
                    appdata_local / eg.name / "Saved" / "SaveGames",
                    appdata_local / eg.name.replace(" ", "") / "Saved" / "SaveGames",
                ]
                if eg.app_id:
                    candidates.append(appdata_local / eg.app_id / "Saved" / "SaveGames")

                if eg.install_path and eg.install_path.exists():
                    candidates.extend([
                        eg.install_path / "Saved" / "SaveGames",
                        eg.install_path / "Saves",
                        eg.install_path / "save"
                    ])

                for cand in candidates:
                    if cand.exists() and cand.is_dir():
                        norm_p = str(cand.resolve()).lower()
                        if norm_p not in discovered_paths:
                            files, size, mtime, exts = self._inspect_directory(cand, max_depth=3)
                            if files > 0:
                                results.append(SavegameItem(
                                    name=eg.name,
                                    platform="Epic Games",
                                    save_path=cand,
                                    file_count=files,
                                    total_size=size,
                                    last_modified=mtime,
                                    extensions=exts
                                ))
                                discovered_paths.add(norm_p)
        except Exception:
            pass

        # 2. Escaneo heurístico en AppData\\Local de carpetas Saved\\SaveGames (Unreal Engine / Epic)
        try:
            for entry in appdata_local.iterdir():
                if not entry.is_dir() or entry.name.lower() in IGNORED_DIR_NAMES:
                    continue
                saved_games_dir = entry / "Saved" / "SaveGames"
                if saved_games_dir.exists() and saved_games_dir.is_dir():
                    norm_p = str(saved_games_dir.resolve()).lower()
                    if norm_p not in discovered_paths:
                        files, size, mtime, exts = self._inspect_directory(saved_games_dir, max_depth=3)
                        if files > 0:
                            matched = self.launcher_detector.match_launcher_by_name(entry.name)
                            platform_label = matched.platform if matched else "Epic / Unreal Engine"
                            game_name = matched.name if matched else entry.name

                            results.append(SavegameItem(
                                name=game_name,
                                platform=platform_label,
                                save_path=saved_games_dir,
                                file_count=files,
                                total_size=size,
                                last_modified=mtime,
                                extensions=exts
                            ))
                            discovered_paths.add(norm_p)
        except Exception:
            pass

        return results

    def scan_xbox_wgs(self) -> List[SavegameItem]:
        """Detecta partidas guardadas de Xbox Game Pass / Windows Gaming Saves (WGS)."""
        results = []
        appdata_local = SystemPaths.appdata_local()
        if not appdata_local or not appdata_local.exists():
            return results

        packages_dir = appdata_local / "Packages"
        if not packages_dir.exists() or not packages_dir.is_dir():
            return results

        try:
            for pkg in packages_dir.glob("*/SystemAppData/wgs"):
                if pkg.is_dir():
                    files, size, mtime, exts = self._inspect_directory(pkg, max_depth=3)
                    if files > 0:
                        pkg_folder_name = pkg.parent.parent.name
                        clean_name = pkg_folder_name.split("_")[0]
                        for prefix in ["Microsoft.", "Bethesda.", "Xbox.", "ElectronicArts."]:
                            if clean_name.startswith(prefix):
                                clean_name = clean_name[len(prefix):]

                        import re
                        readable_name = re.sub(r"([a-z])([A-Z])", r"\1 \2", clean_name)

                        results.append(SavegameItem(
                            name=readable_name,
                            platform="Xbox Game Pass",
                            save_path=pkg,
                            file_count=files,
                            total_size=size,
                            last_modified=mtime,
                            extensions=exts
                        ))
        except Exception:
            pass

        return results

    def scan_all(self) -> List[Dict[str, Any]]:
        """Ejecuta todos los escaneos y desduplica por ruta."""
        all_items: List[SavegameItem] = []
        seen_paths: Set[str] = set()

        # 1. Catálogo conocido de juegos
        for item in self.scan_known_catalog():
            norm_p = str(item.save_path.resolve()).lower()
            if norm_p not in seen_paths:
                seen_paths.add(norm_p)
                all_items.append(item)

        # 2. Steam oficial (userdata)
        for item in self.scan_steam_official():
            norm_p = str(item.save_path.resolve()).lower()
            if norm_p not in seen_paths:
                seen_paths.add(norm_p)
                all_items.append(item)

        # 3. Epic Games & Unreal Engine (AppData\\Local)
        for item in self.scan_epic_and_unreal():
            norm_p = str(item.save_path.resolve()).lower()
            if norm_p not in seen_paths:
                seen_paths.add(norm_p)
                all_items.append(item)

        # 4. Xbox Game Pass / WGS
        for item in self.scan_xbox_wgs():
            norm_p = str(item.save_path.resolve()).lower()
            if norm_p not in seen_paths:
                seen_paths.add(norm_p)
                all_items.append(item)

        # 5. Repacks y emuladores
        for item in self.scan_repacks_and_emulators():
            norm_p = str(item.save_path.resolve()).lower()
            if norm_p not in seen_paths:
                seen_paths.add(norm_p)
                all_items.append(item)

        # 6. Directorios estándar de Windows (Saved Games, Documents, LocalLow, Ubisoft)
        for item in self.scan_standard_windows_directories():
            norm_p = str(item.save_path.resolve()).lower()
            if norm_p not in seen_paths:
                seen_paths.add(norm_p)
                all_items.append(item)

        # Enriquecer plataforma si coincide con un juego de launcher instalado
        for item in all_items:
            if item.platform in {"Saved Games", "Documents", "Documents / My Games", "Electronic Arts", "BioWare", "Rockstar Games"}:
                matched = self.launcher_detector.match_launcher_by_name(item.name)
                if matched:
                    item.platform = f"{matched.platform} / {item.platform}"

            # Asignar portadas e imágenes HD de alta resolución oficiales
            img_data = GameImageService.get_game_image_data(
                item.name,
                item.platform,
                str(item.save_path),
                item.steam_appid
            )
            item.image_url = img_data.get("image_url", "")
            item.capsule_url = img_data.get("capsule_url", "")
            item.poster_url = img_data.get("poster_url", "")
            item.header_url = img_data.get("header_url", "")
            item.procedural_banner = img_data.get("procedural_banner", "")
            if not item.steam_appid and img_data.get("appid"):
                item.steam_appid = img_data["appid"]

        all_items.sort(key=lambda x: x.name.lower())
        return [i.to_dict() for i in all_items]

