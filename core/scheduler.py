"""
Motor de respaldos automáticos programados en segundo plano (Daemon Scheduler)
con persistencia de configuración en JSON.
"""

import os
import json
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any

from core.backup import BackupManager
from core.scanner import SavegameScanner
from core.cloud_sync import CloudSyncManager

CONFIG_FILE = Path(__file__).resolve().parent.parent / "data" / "config.json"

class BackupScheduler:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._init_scheduler()
            return cls._instance

    def _init_scheduler(self):
        self.config = self._load_config()
        self.thread = None
        self.running = False
        if self.config.get("enabled", False):
            self.start()

    def _load_config(self) -> Dict[str, Any]:
        default_cfg = {
            "enabled": False,
            "interval_hours": 6,
            "cloud_sync_enabled": False,
            "cloud_provider": "onedrive",
            "custom_cloud_path": "",
            "last_auto_backup": None,
            "last_backup_status": "Sin ejecuciones previas"
        }
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    default_cfg.update(data)
            except Exception:
                pass
        return default_cfg

    def save_config(self, new_config: Dict[str, Any]):
        self.config.update(new_config)
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

        # Si se activó o desactivó, ajustar el hilo
        if self.config.get("enabled", False):
            if not self.running:
                self.start()
        else:
            self.stop()

    def get_config(self) -> Dict[str, Any]:
        return dict(self.config)

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._worker_loop, daemon=True, name="AnimusSchedulerThread")
        self.thread.start()

    def stop(self):
        self.running = False

    def _worker_loop(self):
        while self.running:
            try:
                if self.config.get("enabled", False):
                    last_str = self.config.get("last_auto_backup")
                    interval = max(1, self.config.get("interval_hours", 6))
                    should_run = False

                    if not last_str:
                        should_run = True
                    else:
                        try:
                            last_time = datetime.strptime(last_str, "%Y-%m-%d %H:%M:%S")
                            if datetime.now() - last_time >= timedelta(hours=interval):
                                should_run = True
                        except Exception:
                            should_run = True

                    if should_run:
                        self.trigger_auto_backup_now()

            except Exception:
                pass

            # Dormir 60 segundos antes de volver a verificar
            time.sleep(60)

    def trigger_auto_backup_now(self) -> Dict[str, Any]:
        """Ejecuta un respaldo maestro automático y sincroniza con la nube si está activo."""
        try:
            scanner = SavegameScanner()
            games = scanner.scan_all()
            if not games:
                return {"success": False, "error": "No se encontraron partidas para respaldar"}

            # Crear respaldo maestro automático
            res = BackupManager.create_master_backup(games, "AutoSync")
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if res.get("success"):
                self.config["last_auto_backup"] = now_str
                self.config["last_backup_status"] = f"Completado exitosamente ({res.get('total_games', 0)} juegos)"

                # Sincronizar a la nube si está activado
                if self.config.get("cloud_sync_enabled", False):
                    prov = self.config.get("cloud_provider", "onedrive")
                    custom_p = self.config.get("custom_cloud_path")
                    CloudSyncManager.sync_backups_to_cloud(prov, custom_p)

                self.save_config({})
                return {"success": True, "message": f"Respaldo automático completado a las {now_str}"}
            else:
                self.config["last_backup_status"] = f"Error: {res.get('error', 'Fallo al comprimir')}"
                self.save_config({})
                return res
        except Exception as e:
            return {"success": False, "error": str(e)}
