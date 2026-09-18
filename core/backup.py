"""
Módulo para realizar copias de seguridad (Backups) individuales y maestras
comprimidas en ZIP, restauración con portabilidad de rutas tras formatear PC,
y utilidades del sistema de archivos.
"""

import os
import json
import zipfile
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple

from core.windows_paths import SystemPaths

class BackupManager:
    DEFAULT_BACKUP_DIR = Path.home() / "Documents" / "SavegameBackups"

    @classmethod
    def get_backup_dir(cls) -> Path:
        cls.DEFAULT_BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        return cls.DEFAULT_BACKUP_DIR

    @classmethod
    def sanitize_filename(cls, name: str) -> str:
        invalid = '<>:"/\\|?*'
        for ch in invalid:
            name = name.replace(ch, "_")
        return name.strip()

    @classmethod
    def tokenize_path(cls, path_str: str) -> str:
        """
        Convierte una ruta absoluta de Windows en una ruta portable con tokens de entorno.
        Permite restaurar partidas después de formatear incluso si el usuario cambió de nombre.
        Ej: C:\\Users\\Anima\\Saved Games\\Juego -> %USERPROFILE%\\Saved Games\\Juego
        """
        p = Path(path_str).resolve()
        p_str = str(p)

        tokens = [
            ("%APPDATA%", str(SystemPaths.appdata_roaming().resolve())),
            ("%LOCALAPPDATA%", str(SystemPaths.appdata_local().resolve())),
            ("%LOCALAPPDATALOW%", str(SystemPaths.appdata_locallow().resolve())),
            ("%PUBLIC%", str(SystemPaths.public_documents().parent.resolve())),
            ("%PUBLIC_DOCS%", str(SystemPaths.public_documents().resolve())),
            ("%SAVED_GAMES%", str(SystemPaths.saved_games().resolve())),
            ("%USER_DOCS%", str(SystemPaths.documents().resolve())),
            ("%USERPROFILE%", str(Path.home().resolve())),
        ]

        # Ordenar por longitud de valor descendente para reemplazar primero las más específicas
        tokens.sort(key=lambda x: len(x[1]), reverse=True)

        for token, val in tokens:
            if p_str.lower().startswith(val.lower()):
                rel = p_str[len(val):].lstrip("\\/")
                return f"{token}\\{rel}" if rel else token

        return p_str

    @classmethod
    def expand_tokenized_path(cls, token_path: str) -> Path:
        """
        Expande una ruta con tokens al sistema de archivos del Windows actual.
        """
        token_map = {
            "%APPDATA%": SystemPaths.appdata_roaming(),
            "%LOCALAPPDATA%": SystemPaths.appdata_local(),
            "%LOCALAPPDATALOW%": SystemPaths.appdata_locallow(),
            "%PUBLIC%": SystemPaths.public_documents().parent,
            "%PUBLIC_DOCS%": SystemPaths.public_documents(),
            "%SAVED_GAMES%": SystemPaths.saved_games(),
            "%USER_DOCS%": SystemPaths.documents(),
            "%USERPROFILE%": Path.home(),
        }

        for token, resolved in token_map.items():
            if token_path.startswith(token):
                remainder = token_path[len(token):].lstrip("\\/")
                return (resolved / remainder).resolve()

        return Path(token_path).resolve()

    @classmethod
    def safe_zip_write(cls, zipf: zipfile.ZipFile, file_path: Path, arcname: str):
        """Escribe un archivo en el ZIP corrigiendo timestamps anteriores a 1980 (requisito del formato ZIP)."""
        try:
            zinfo = zipfile.ZipInfo.from_file(file_path, arcname)
            if zinfo.date_time[0] < 1980:
                zinfo.date_time = (2000, 1, 1, 0, 0, 0)
            with open(file_path, "rb") as f:
                zipf.writestr(zinfo, f.read(), compress_type=zipfile.ZIP_DEFLATED)
        except Exception:
            try:
                with open(file_path, "rb") as f:
                    data = f.read()
                zinfo = zipfile.ZipInfo(arcname, date_time=(2000, 1, 1, 0, 0, 0))
                zipf.writestr(zinfo, data, compress_type=zipfile.ZIP_DEFLATED)
            except Exception:
                pass

    @classmethod
    def create_backup(cls, source_path: str, game_name: str, note: str = "", is_safety: bool = False) -> Dict[str, Any]:
        """Crea una copia de seguridad individual en formato .ZIP con metadatos de versión."""
        src = Path(source_path)
        if not src.exists():
            return {"success": False, "error": f"La ruta de origen no existe: {source_path}"}

        backup_root = cls.get_backup_dir()
        safe_game_name = cls.sanitize_filename(game_name)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        prefix = f"{safe_game_name}"
        if is_safety and "_PRE_REVERT" not in prefix:
            prefix = f"{prefix}_PRE_REVERT"
        zip_filename = f"{prefix}_{timestamp}.zip"
        zip_path = backup_root / zip_filename

        # Si ya existe un archivo en el mismo segundo exacto, generar nombre único con contador
        counter = 1
        while zip_path.exists():
            zip_filename = f"{prefix}_{timestamp}_{counter}.zip"
            zip_path = backup_root / zip_filename
            counter += 1

        try:
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                file_count = 0
                total_bytes = 0

                if src.is_file():
                    cls.safe_zip_write(zipf, src, src.name)
                    file_count = 1
                    total_bytes = src.stat().st_size
                else:
                    for root, _, files in os.walk(src):
                        for file in files:
                            file_path = Path(root) / file
                            arcname = file_path.relative_to(src)
                            cls.safe_zip_write(zipf, file_path, str(arcname))
                            file_count += 1
                            total_bytes += file_path.stat().st_size

                # Escribir metadatos de versión para rastreo e historial
                version_meta = {
                    "app": "Animus SaveVault",
                    "version_format": "1.0",
                    "game_name": game_name,
                    "source_path": str(src.resolve()),
                    "token_path": cls.tokenize_path(source_path),
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "timestamp": timestamp,
                    "note": note.strip() if note else "",
                    "is_safety": is_safety,
                    "file_count": file_count,
                    "total_size": total_bytes
                }
                zipf.writestr("animus_version.json", json.dumps(version_meta, indent=2, ensure_ascii=False))

            stat = zip_path.stat()
            return {
                "success": True,
                "message": "Punto de restauración creado con éxito",
                "zip_path": str(zip_path),
                "filename": zip_filename,
                "size_bytes": stat.st_size,
                "size_str": f"{stat.st_size / (1024 * 1024):.2f} MB" if stat.st_size > 1024 * 1024 else f"{stat.st_size / 1024:.1f} KB",
                "timestamp": timestamp,
                "note": note,
                "is_safety": is_safety
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


    @classmethod
    def create_master_backup(cls, selected_games: List[Dict[str, Any]], custom_name: str = "MasterBackup") -> Dict[str, Any]:
        """
        Crea un respaldo consolidado maestro con metadatos para formateo/migración.
        Incluye un manifest.json con tokens portables para restauración en 1 clic.
        """
        if not selected_games:
            return {"success": False, "error": "No hay juegos seleccionados para el respaldo maestro."}

        backup_root = cls.get_backup_dir()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = cls.sanitize_filename(custom_name)
        zip_filename = f"AnimusVault_{safe_name}_{timestamp}.zip"
        zip_path = backup_root / zip_filename

        manifest_entries = []

        try:
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                for idx, game in enumerate(selected_games):
                    src = Path(game["path"])
                    if not src.exists():
                        continue

                    safe_title = cls.sanitize_filename(game["name"])
                    folder_in_zip = f"saves/{idx:03d}_{safe_title}"
                    token_path = cls.tokenize_path(game["path"])

                    manifest_entries.append({
                        "id": idx,
                        "name": game["name"],
                        "platform": game.get("platform", "Desconocida"),
                        "token_path": token_path,
                        "folder_in_zip": folder_in_zip,
                        "steam_appid": game.get("steam_appid", "")
                    })

                    # Empaquetar archivos del juego de forma segura
                    if src.is_file():
                        cls.safe_zip_write(zipf, src, f"{folder_in_zip}/{src.name}")
                    else:
                        for root, _, files in os.walk(src):
                            for file in files:
                                file_path = Path(root) / file
                                rel = file_path.relative_to(src)
                                cls.safe_zip_write(zipf, file_path, f"{folder_in_zip}/{rel}")

                # Escribir manifest.json en la raíz del ZIP
                manifest_data = {
                    "version": "1.0",
                    "app": "Animus SaveVault",
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "total_games": len(manifest_entries),
                    "games": manifest_entries
                }
                zipf.writestr("manifest.json", json.dumps(manifest_data, indent=2, ensure_ascii=False))

            stat = zip_path.stat()
            size_str = f"{stat.st_size / (1024 * 1024):.2f} MB" if stat.st_size > 1024 * 1024 else f"{stat.st_size / 1024:.1f} KB"
            return {
                "success": True,
                "message": f"Respaldo maestro creado con éxito ({len(manifest_entries)} juegos)",
                "zip_path": str(zip_path),
                "filename": zip_filename,
                "total_games": len(manifest_entries),
                "size_str": size_str,
                "timestamp": timestamp
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @classmethod
    def restore_master_backup(cls, zip_path_str: str) -> Dict[str, Any]:
        """
        Restaura un respaldo maestro de manera inteligente:
        Lee manifest.json, expande las rutas en el Windows actual y extrae cada juego.
        """
        zip_path = Path(zip_path_str)
        if not zip_path.exists():
            return {"success": False, "error": f"El archivo ZIP no existe: {zip_path_str}"}

        restored_games = []
        errors = []

        try:
            with zipfile.ZipFile(zip_path, "r") as zipf:
                # Comprobar manifest
                if "manifest.json" not in zipf.namelist():
                    return {"success": False, "error": "El archivo ZIP no contiene un manifest.json válido de Animus SaveVault."}

                manifest_raw = zipf.read("manifest.json").decode("utf-8")
                manifest = json.loads(manifest_raw)

                for game_entry in manifest.get("games", []):
                    name = game_entry.get("name", "Juego")
                    token_path = game_entry.get("token_path")
                    folder_in_zip = game_entry.get("folder_in_zip")

                    if not token_path or not folder_in_zip:
                        continue

                    # Resolver ruta de destino en el Windows actual
                    target_dir = cls.expand_tokenized_path(token_path)
                    target_dir.mkdir(parents=True, exist_ok=True)

                    prefix = f"{folder_in_zip}/"
                    extracted_count = 0

                    for member in zipf.namelist():
                        if member.startswith(prefix) and not member.endswith("/"):
                            rel_inside = member[len(prefix):]
                            dest_file = target_dir / rel_inside
                            dest_file.parent.mkdir(parents=True, exist_ok=True)
                            with zipf.open(member) as src_f, open(dest_file, "wb") as dst_f:
                                dst_f.write(src_f.read())
                            extracted_count += 1

                    restored_games.append({
                        "name": name,
                        "destination": str(target_dir),
                        "files_restored": extracted_count
                    })

            return {
                "success": True,
                "message": f"Se restauraron {len(restored_games)} juegos correctamente.",
                "total_restored": len(restored_games),
                "games": restored_games,
                "errors": errors
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @classmethod
    def read_version_meta(cls, zip_path: Path) -> Dict[str, Any]:
        """Lee animus_version.json del ZIP o infiere metadatos a partir del nombre del archivo."""
        meta = {}
        try:
            with zipfile.ZipFile(zip_path, "r") as zipf:
                if "animus_version.json" in zipf.namelist():
                    raw = zipf.read("animus_version.json").decode("utf-8")
                    meta = json.loads(raw)
        except Exception:
            pass

        stat = zip_path.stat()
        mtime = datetime.fromtimestamp(stat.st_mtime)

        # Si no tiene metadatos en el zip, inferir del nombre
        if not meta:
            filename = zip_path.stem
            is_safety = "_PRE_REVERT" in filename
            is_master = "MasterBackup" in filename or "AnimusVault_Master" in filename or "AnimusVault_Formateo" in filename
            import re
            clean_stem = filename.replace("_PRE_REVERT", "")
            m = re.search(r"^(.*?)(?:_(\d{8}_\d{6}))?$", clean_stem)
            if m and m.group(1):
                inferred_name = m.group(1).replace("_", " ").strip()
                ts_str = m.group(2) if m.group(2) else ""
            else:
                inferred_name = filename.replace("_", " ")
                ts_str = ""

            meta = {
                "game_name": inferred_name,
                "source_path": "",
                "token_path": "",
                "note": "Copia de seguridad previa a reversión" if is_safety else "",
                "is_safety": is_safety,
                "is_master": is_master,
                "created_at": mtime.strftime("%Y-%m-%d %H:%M:%S"),
                "timestamp": ts_str,
                "file_count": 0,
                "total_size": stat.st_size
            }

        meta["filename"] = zip_path.name
        meta["path"] = str(zip_path)
        meta["size_bytes"] = stat.st_size
        meta["size_str"] = f"{stat.st_size / (1024 * 1024):.2f} MB" if stat.st_size > 1024 * 1024 else f"{stat.st_size / 1024:.1f} KB"
        if "date" not in meta or not meta["date"]:
            meta["date"] = mtime.strftime("%Y-%m-%d %H:%M:%S")

        # Tiempo relativo para UI amigable
        diff = datetime.now() - mtime
        if diff.total_seconds() < 60:
            meta["relative_time"] = "Hace unos segundos"
        elif diff.total_seconds() < 3600:
            mins = int(diff.total_seconds() // 60)
            meta["relative_time"] = f"Hace {mins} min"
        elif diff.total_seconds() < 86400:
            hours = int(diff.total_seconds() // 3600)
            meta["relative_time"] = f"Hace {hours} h"
        else:
            days = int(diff.total_seconds() // 86400)
            meta["relative_time"] = f"Hace {days} d"

        return meta

    @classmethod
    def restore_backup(cls, zip_path_str: str, target_dir_str: str) -> Dict[str, Any]:
        """Restaura los archivos contenidos en el ZIP hacia la carpeta del juego, excluyendo metadatos internos."""
        zip_path = Path(zip_path_str)
        target_path = Path(target_dir_str)

        if not zip_path.exists():
            return {"success": False, "error": "El archivo de copia de seguridad no existe."}

        # Si el destino parece ser un archivo individual, usar su directorio padre
        if target_path.is_file() or (not target_path.exists() and target_path.suffix):
            extract_dir = target_path.parent
        else:
            extract_dir = target_path

        extract_dir.mkdir(parents=True, exist_ok=True)

        restored_files = 0
        try:
            with zipfile.ZipFile(zip_path, "r") as zipf:
                for member in zipf.infolist():
                    # Ignorar metadatos internos de Animus
                    if member.filename in ("animus_version.json", "manifest.json") or member.filename.startswith(".animus_"):
                        continue
                    zipf.extract(member, extract_dir)
                    restored_files += 1

            return {
                "success": True,
                "message": f"Partida restaurada exitosamente en {extract_dir} ({restored_files} archivos)",
                "extracted_dir": str(extract_dir),
                "files_restored": restored_files
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @classmethod
    def revert_to_version(cls, zip_path_str: str, target_dir_str: str = "", create_safety_backup: bool = True) -> Dict[str, Any]:
        """
        Revierte la partida actual al estado de la versión especificada en el ZIP.
        Crea automáticamente un respaldo de seguridad del estado presente antes de sobrescribir.
        """
        zip_path = Path(zip_path_str)
        if not zip_path.exists():
            return {"success": False, "error": f"El archivo de respaldo no existe: {zip_path_str}"}

        meta = cls.read_version_meta(zip_path)
        game_name = meta.get("game_name", "Juego")

        # Determinar destino si no se proporcionó
        if not target_dir_str:
            token_path = meta.get("token_path")
            if token_path:
                target_dir_str = str(cls.expand_tokenized_path(token_path))
            elif meta.get("source_path"):
                target_dir_str = meta.get("source_path")

        if not target_dir_str:
            return {"success": False, "error": "No se pudo determinar el directorio destino para restaurar la partida."}

        target_dir = Path(target_dir_str)

        # 1. Crear snapshot de seguridad si el destino existe y create_safety_backup es True
        safety_info = None
        if create_safety_backup and target_dir.exists():
            safety_note = f"Seguridad automática antes de revertir a versión de {meta.get('date', 'fecha previa')}"
            safety_res = cls.create_backup(
                source_path=str(target_dir),
                game_name=game_name,
                note=safety_note,
                is_safety=True
            )
            if safety_res.get("success"):
                safety_info = safety_res

        # 2. Restaurar la versión elegida
        restore_res = cls.restore_backup(str(zip_path), str(target_dir))
        if not restore_res.get("success"):
            return restore_res

        return {
            "success": True,
            "message": f"Partida revertida exitosamente al estado del {meta.get('date', 'archivo')}.",
            "target_path": str(target_dir),
            "restored_from": zip_path.name,
            "version_date": meta.get("date", ""),
            "safety_backup": safety_info
        }

    @classmethod
    def get_game_versions(cls, game_name: str, source_path: str = "") -> List[Dict[str, Any]]:
        """
        Devuelve todas las versiones / snapshots disponibles para un juego en orden cronológico inverso.
        """
        backup_root = cls.get_backup_dir()
        if not backup_root.exists():
            return []

        safe_name = cls.sanitize_filename(game_name).lower()
        norm_game_name = "".join(c for c in game_name.lower() if c.isalnum())
        norm_source_path = str(Path(source_path).resolve()).lower() if source_path else ""

        versions = []
        for zip_file in backup_root.glob("*.zip"):
            if "AnimusVault_Formateo" in zip_file.name or "AnimusVault_Master" in zip_file.name:
                continue

            meta = cls.read_version_meta(zip_file)
            matched = False

            # Comprobar coincidencia por nombre o archivo
            meta_game = meta.get("game_name", "")
            meta_norm = "".join(c for c in meta_game.lower() if c.isalnum())
            zip_stem = zip_file.stem.lower()

            if norm_game_name and meta_norm and norm_game_name == meta_norm:
                matched = True
            elif safe_name and (zip_stem.startswith(safe_name) or safe_name in zip_stem):
                matched = True
            elif norm_source_path and meta.get("source_path"):
                norm_meta_src = str(Path(meta.get("source_path")).resolve()).lower()
                if norm_meta_src == norm_source_path:
                    matched = True

            if matched:
                versions.append(meta)

        # Ordenar por fecha de modificación descendente (más reciente primero)
        versions.sort(key=lambda v: v.get("timestamp") or v.get("date") or "", reverse=True)
        return versions

    @classmethod
    def get_version_counts(cls) -> Dict[str, int]:
        """
        Devuelve un mapa con conteo de versiones para consulta rápida.
        """
        backup_root = cls.get_backup_dir()
        counts = {}
        if not backup_root.exists():
            return counts

        for zip_file in backup_root.glob("*.zip"):
            if "AnimusVault_Formateo" in zip_file.name or "AnimusVault_Master" in zip_file.name:
                continue
            meta = cls.read_version_meta(zip_file)
            game_name = meta.get("game_name", "")
            if game_name:
                norm = "".join(c for c in game_name.lower() if c.isalnum())
                counts[norm] = counts.get(norm, 0) + 1
                safe = cls.sanitize_filename(game_name).lower()
                counts[safe] = counts.get(safe, 0) + 1
            if meta.get("source_path"):
                src_key = str(Path(meta["source_path"]).resolve()).lower()
                counts[src_key] = counts.get(src_key, 0) + 1
        return counts

    @classmethod
    def delete_backup(cls, zip_path_str: str) -> Dict[str, Any]:
        """Elimina un archivo de copia de seguridad o versión."""
        zip_path = Path(zip_path_str)
        if not zip_path.exists():
            return {"success": False, "error": "El archivo de respaldo no existe."}
        try:
            zip_path.unlink()
            return {"success": True, "message": "Versión eliminada correctamente."}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @classmethod
    def list_backups(cls) -> List[Dict[str, Any]]:
        """Lista todos los backups generados con metadatos completos."""
        backup_root = cls.get_backup_dir()
        results = []
        try:
            for f in sorted(backup_root.glob("*.zip"), key=lambda x: x.stat().st_mtime, reverse=True):
                is_master = "MasterBackup" in f.name or "AnimusVault_Master" in f.name or "AnimusVault_Formateo" in f.name
                if is_master:
                    stat = f.stat()
                    mtime = datetime.fromtimestamp(stat.st_mtime)
                    size_str = f"{stat.st_size / (1024 * 1024):.2f} MB" if stat.st_size > 1024 * 1024 else f"{stat.st_size / 1024:.1f} KB"
                    results.append({
                        "filename": f.name,
                        "path": str(f),
                        "game_name": "PAQUETE MAESTRO",
                        "size_str": size_str,
                        "is_master": True,
                        "is_safety": False,
                        "note": "Copia consolidada de múltiples partidas",
                        "date": mtime.strftime("%Y-%m-%d %H:%M:%S")
                    })
                else:
                    meta = cls.read_version_meta(f)
                    meta["is_master"] = False
                    results.append(meta)
        except Exception:
            pass
        return results

    @staticmethod
    def open_in_explorer(target_path: str):
        """Abre la carpeta en el explorador de archivos de Windows."""
        p = Path(target_path)
        if not p.exists():
            p = p.parent
        if p.exists():
            if p.is_file():
                subprocess.Popen(f'explorer /select,"{p}"')
            else:
                subprocess.Popen(f'explorer "{p}"')
