"""
Módulo para detectar e integrar almacenamiento en la nube en Windows:
- Microsoft OneDrive
- Google Drive
- Dropbox
- Carpetas personalizadas / Red local (NAS)
"""

import os
import shutil
import json
import winreg
from pathlib import Path
from typing import Dict, List, Any, Optional

from core.backup import BackupManager

class CloudSyncManager:
    @staticmethod
    def detect_cloud_providers() -> List[Dict[str, Any]]:
        """Detecta qué servicios de almacenamiento en la nube están instalados en el PC."""
        providers = []

        # 1. Microsoft OneDrive
        onedrive_paths = []
        for env_var in ["OneDrive", "OneDriveConsumer", "OneDriveCommercial"]:
            val = os.environ.get(env_var)
            if val and Path(val).exists():
                onedrive_paths.append(Path(val))

        # Registro de OneDrive
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\OneDrive") as key:
                val, _ = winreg.QueryValueEx(key, "UserFolder")
                if val and Path(val).exists() and Path(val) not in onedrive_paths:
                    onedrive_paths.append(Path(val))
        except Exception:
            pass

        if onedrive_paths:
            primary_od = onedrive_paths[0]
            providers.append({
                "id": "onedrive",
                "name": "Microsoft OneDrive",
                "path": str(primary_od),
                "sync_folder": str(primary_od / "Animus_SaveVault"),
                "available": True,
                "icon": "cloud"
            })

        # 2. Google Drive
        gdrive_candidates = [
            Path(r"G:\Mi unidad"),
            Path(r"G:\My Drive"),
            Path(r"H:\Mi unidad"),
            Path(r"H:\My Drive"),
            Path.home() / "Google Drive"
        ]
        found_gdrive = None
        for candidate in gdrive_candidates:
            if candidate.exists():
                found_gdrive = candidate
                break

        if found_gdrive:
            providers.append({
                "id": "gdrive",
                "name": "Google Drive",
                "path": str(found_gdrive),
                "sync_folder": str(found_gdrive / "Animus_SaveVault"),
                "available": True,
                "icon": "google"
            })

        # 3. Dropbox
        dropbox_path = None
        # Leer info.json de Dropbox si existe
        info_json = Path.home() / "AppData" / "Local" / "Dropbox" / "info.json"
        if not info_json.exists():
            info_json = Path.home() / "AppData" / "Roaming" / "Dropbox" / "info.json"

        if info_json.exists():
            try:
                with open(info_json, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for k in ["personal", "business"]:
                        if k in data and "path" in data[k]:
                            p = Path(data[k]["path"])
                            if p.exists():
                                dropbox_path = p
                                break
            except Exception:
                pass

        if not dropbox_path:
            candidate = Path.home() / "Dropbox"
            if candidate.exists():
                dropbox_path = candidate

        if dropbox_path:
            providers.append({
                "id": "dropbox",
                "name": "Dropbox",
                "path": str(dropbox_path),
                "sync_folder": str(dropbox_path / "Animus_SaveVault"),
                "available": True,
                "icon": "box"
            })

        return providers

    @classmethod
    def sync_backups_to_cloud(cls, provider_id: str, custom_path: Optional[str] = None) -> Dict[str, Any]:
        """Copia todos los respaldos existentes hacia la carpeta de la nube elegida."""
        target_dir = None

        if provider_id == "custom" and custom_path:
            target_dir = Path(custom_path)
        else:
            providers = cls.detect_cloud_providers()
            for p in providers:
                if p["id"] == provider_id:
                    target_dir = Path(p["sync_folder"])
                    break

        if not target_dir:
            return {"success": False, "error": f"No se pudo resolver el destino para el proveedor: {provider_id}"}

        try:
            target_dir.mkdir(parents=True, exist_ok=True)
            source_dir = BackupManager.get_backup_dir()

            synced_files = []
            for zip_file in source_dir.glob("*.zip"):
                dest_file = target_dir / zip_file.name
                # Solo copiar si no existe o si es más reciente
                if not dest_file.exists() or zip_file.stat().st_mtime > dest_file.stat().st_mtime:
                    shutil.copy2(zip_file, dest_file)
                    synced_files.append(zip_file.name)

            return {
                "success": True,
                "message": f"Sincronización completada. {len(synced_files)} archivos actualizados.",
                "target_dir": str(target_dir),
                "synced_count": len(synced_files),
                "synced_files": synced_files
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
