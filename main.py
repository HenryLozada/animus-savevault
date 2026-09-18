import os
import sys
import webview
from pathlib import Path

# Agregar directorio raíz al path para ejecución directa y congelada
BASE_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
sys.path.insert(0, str(BASE_DIR))

from core.scanner import SavegameScanner
from core.backup import BackupManager
from core.cloud_sync import CloudSyncManager
from core.scheduler import BackupScheduler
from core.analytics import AnimusAnalytics
from core.image_service import GameImageService

class SaveVaultApi:
    def __init__(self):
        self.scanner = SavegameScanner()
        self.scheduler = BackupScheduler()
        self._window = None

    def set_window(self, window):
        self._window = window

    # 1. Escaneo de partidas
    def scan_games(self):
        """Escanea todas las plataformas, emuladores y directorios del sistema."""
        try:
            return self.scanner.scan_all()
        except Exception:
            return []

    def get_game_image(self, game_name: str, appid: str = "", platform: str = "", path: str = ""):
        """Obtiene URLs en alta resolución y generación procedural para un juego."""
        try:
            return GameImageService.get_game_image_data(game_name, platform, path, appid)
        except Exception:
            return {
                "appid": appid,
                "clean_name": game_name,
                "image_url": "",
                "capsule_url": "",
                "poster_url": "",
                "header_url": "",
                "procedural_banner": GameImageService.generate_procedural_banner(game_name, platform)
            }

    # 2. Respaldos individuales, versiones y maestros
    def backup_game(self, source_path: str, game_name: str, note: str = ""):
        """Crea una copia de seguridad o versión individual en formato ZIP."""
        try:
            return BackupManager.create_backup(source_path, game_name, note=note)
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_game_versions(self, game_name: str, source_path: str = ""):
        """Obtiene todas las versiones registradas para un juego en orden cronológico."""
        try:
            return BackupManager.get_game_versions(game_name, source_path)
        except Exception:
            return []

    def revert_to_version(self, zip_path: str, target_path: str = ""):
        """Revierte la partida al estado de una versión anterior, con copia de seguridad previa automática."""
        try:
            return BackupManager.revert_to_version(zip_path, target_path, create_safety_backup=True)
        except Exception as e:
            return {"success": False, "error": str(e)}

    def delete_backup(self, zip_path: str):
        """Elimina una versión o archivo de respaldo del sistema."""
        try:
            return BackupManager.delete_backup(zip_path)
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_version_counts(self):
        """Obtiene el mapa de conteo de versiones disponibles para los juegos."""
        try:
            return BackupManager.get_version_counts()
        except Exception:
            return {}

    def create_master_backup(self, selected_games: list, custom_name: str = "MasterBackup"):
        """Crea un respaldo consolidado maestro con manifest.json para formatear la PC."""
        try:
            return BackupManager.create_master_backup(selected_games, custom_name)
        except Exception as e:
            return {"success": False, "error": str(e)}

    def choose_master_backup_file(self):
        """Abre un diálogo nativo de Windows para seleccionar un archivo ZIP."""
        if not self._window:
            return None
        try:
            file_types = ("Archivos ZIP (*.zip)", "Todos los archivos (*.*)")
            res = self._window.create_file_dialog(
                webview.OPEN_DIALOG,
                allow_multiple=False,
                file_types=file_types
            )
            if res and len(res) > 0:
                return res[0]
            return None
        except Exception:
            return None

    def restore_master_backup(self, zip_path: str):
        """Restaura un respaldo maestro ubicando cada partida en su lugar original."""
        try:
            return BackupManager.restore_master_backup(zip_path)
        except Exception as e:
            return {"success": False, "error": str(e)}

    def restore_backup(self, zip_path: str, target_path: str):
        """Restaura una copia de seguridad individual ZIP."""
        try:
            return BackupManager.restore_backup(zip_path, target_path)
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_backups(self):
        """Obtiene la lista de copias de seguridad creadas."""
        try:
            return BackupManager.list_backups()
        except Exception:
            return []

    # 3. Sincronización en la Nube
    def get_cloud_providers(self):
        """Detecta qué servicios de nube están disponibles en este equipo."""
        try:
            return CloudSyncManager.detect_cloud_providers()
        except Exception:
            return []

    def sync_to_cloud(self, provider_id: str, custom_path: str = None):
        """Copia los respaldos a la carpeta del proveedor de nube seleccionado."""
        try:
            return CloudSyncManager.sync_backups_to_cloud(provider_id, custom_path)
        except Exception as e:
            return {"success": False, "error": str(e)}

    def choose_custom_cloud_folder(self):
        """Abre un diálogo nativo de Windows para elegir una carpeta personalizada de sincronización."""
        if not self._window:
            return None
        try:
            res = self._window.create_file_dialog(webview.FOLDER_DIALOG)
            if res and len(res) > 0:
                return res[0]
            return None
        except Exception:
            return None

    # 4. Programador de Respaldos Automáticos
    def get_scheduler_config(self):
        """Obtiene la configuración actual del scheduler."""
        try:
            return self.scheduler.get_config()
        except Exception:
            return {}

    def save_scheduler_config(self, config: dict):
        """Guarda la nueva configuración del scheduler."""
        try:
            self.scheduler.save_config(config)
            return {"success": True, "config": self.scheduler.get_config()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def trigger_auto_backup_now(self):
        """Fuerza la ejecución del respaldo automático."""
        try:
            return self.scheduler.trigger_auto_backup_now()
        except Exception as e:
            return {"success": False, "error": str(e)}

    # 5. Telemetría y Estadísticas
    def get_analytics(self, games: list):
        """Calcula el resumen de telemetría, almacenamiento y actividad por juego."""
        try:
            return AnimusAnalytics.get_telemetry(games)
        except Exception as e:
            return {"error": str(e)}

    # 6. Utilidades de Windows
    def open_explorer(self, target_path: str):
        """Abre la ruta especificada en el explorador de Windows."""
        try:
            BackupManager.open_in_explorer(target_path)
            return True
        except Exception:
            return False

    def open_backups_folder(self):
        """Abre el directorio de copias de seguridad en el explorador de Windows."""
        try:
            BackupManager.open_in_explorer(str(BackupManager.get_backup_dir()))
            return True
        except Exception:
            return False

def main():
    api = SaveVaultApi()
    gui_dir = BASE_DIR / "gui"
    html_path = gui_dir / "index.html"

    window = webview.create_window(
        title="ANIMUS // SaveVault - NVIDIA Power Green Architecture",
        url=str(html_path.resolve()),
        js_api=api,
        width=1280,
        height=840,
        min_size=(960, 640),
        background_color="#000000"
    )
    api.set_window(window)

    webview.start(debug=False)

if __name__ == "__main__":
    main()
