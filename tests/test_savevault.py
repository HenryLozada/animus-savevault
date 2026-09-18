"""
Banco de pruebas automatizadas (Unit & Integration Tests) para Animus SaveVault.
Verifica robustez, tolerancia a fallos y funcionamiento de todos los módulos.
"""

import os
import sys
import shutil
import zipfile
import tempfile
import unittest
from pathlib import Path

# Asegurar que el directorio raíz del proyecto esté en el sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.windows_paths import (
    SystemPaths,
    get_steam_install_path,
    get_epic_manifests_path,
    get_ea_desktop_data_path,
    get_gog_galaxy_storage_path,
    get_heroic_config_path
)
from core.launchers import LauncherDetector, InstalledLauncherGame
from core.scanner import SavegameScanner
from core.backup import BackupManager
from core.analytics import AnimusAnalytics
from core.cloud_sync import CloudSyncManager
from core.scheduler import BackupScheduler
from main import SaveVaultApi


class TestWindowsPaths(unittest.TestCase):
    def test_paths_return_valid_types(self):
        """Verifica que los resolutores de rutas del sistema devuelvan Path o None sin fallar."""
        self.assertIsInstance(SystemPaths.saved_games(), Path)
        self.assertIsInstance(SystemPaths.documents(), Path)
        self.assertIsInstance(SystemPaths.appdata_local(), Path)
        self.assertIsInstance(SystemPaths.appdata_locallow(), Path)
        self.assertIsInstance(SystemPaths.appdata_roaming(), Path)
        self.assertIsInstance(SystemPaths.public_documents(), Path)

        # Rutas específicas de lanzadores (pueden no existir físicamente pero la función debe responder)
        for fn in [get_steam_install_path, get_epic_manifests_path, get_ea_desktop_data_path, get_gog_galaxy_storage_path, get_heroic_config_path]:
            res = fn()
            self.assertTrue(res is None or isinstance(res, Path))


class TestLaunchers(unittest.TestCase):
    def setUp(self):
        self.detector = LauncherDetector()

    def test_installed_launcher_game_normalization(self):
        """Verifica la normalización canónica de nombres de juegos para correlación."""
        game = InstalledLauncherGame(name="Grand Theft Auto V: Enhanced", platform="Epic Games")
        self.assertEqual(game.normalized_name(), "grandtheftautovenhanced")

    def test_scan_all_launchers_and_alias(self):
        """Verifica que scan_all_launchers y su alias detect_all se ejecuten sin lanzar excepciones."""
        games = self.detector.scan_all_launchers()
        self.assertIsInstance(games, list)

        # Probar alias
        games_alias = self.detector.detect_all()
        self.assertEqual(len(games), len(games_alias))

    def test_match_launcher_by_name(self):
        """Verifica la correlación difusa con juegos registrados y heurística de prefijos."""
        dummy_game = InstalledLauncherGame(
            name="Cyberpunk 2077",
            platform="GOG Galaxy",
            install_path=Path(r"C:\Games\Cyberpunk 2077")
        )
        self.detector._installed_games.append(dummy_game)
        self.detector._games_by_norm_name[dummy_game.normalized_name()] = dummy_game

        matched = self.detector.match_launcher_by_name("Cyberpunk 2077")
        self.assertIsNotNone(matched)
        self.assertEqual(matched.platform, "GOG Galaxy")


class TestScanner(unittest.TestCase):
    def setUp(self):
        self.scanner = SavegameScanner()

    def test_scan_all_returns_structured_data(self):
        """Verifica que el escáner devuelva una lista de partidas con todos los campos requeridos."""
        games = self.scanner.scan_all()
        self.assertIsInstance(games, list)

        required_keys = {
            "name", "platform", "path", "file_count",
            "total_size", "size_str", "last_modified", "extensions"
        }

        for game in games:
            self.assertIsInstance(game, dict)
            for k in required_keys:
                self.assertIn(k, game, f"Falta la clave obligatoria '{k}' en el resultado del escáner")
            self.assertGreaterEqual(game["file_count"], 0)
            self.assertGreaterEqual(game["total_size"], 0)


class TestBackupManager(unittest.TestCase):
    def setUp(self):
        # Crear directorios temporales aislados para no alterar los respaldos reales del usuario
        self.temp_dir = tempfile.TemporaryDirectory()
        self.mock_saves = Path(self.temp_dir.name) / "MockSave"
        self.mock_saves.mkdir(parents=True, exist_ok=True)

        # Crear archivos simulados de guardado
        (self.mock_saves / "slot1.sav").write_bytes(b"DATA_SAVE_SLOT_1_SAMPLE")
        (self.mock_saves / "settings.ini").write_text("[Settings]\nVolume=100")

        self.backup_dir = Path(self.temp_dir.name) / "Backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # Redirigir el directorio de respaldos en BackupManager
        self.original_backup_dir = BackupManager.DEFAULT_BACKUP_DIR
        BackupManager.DEFAULT_BACKUP_DIR = self.backup_dir

    def tearDown(self):
        BackupManager.DEFAULT_BACKUP_DIR = self.original_backup_dir
        self.temp_dir.cleanup()

    def test_create_backup_and_versions(self):
        """Verifica la creación de respaldos ZIP, manifest y gestión de versiones."""
        res = BackupManager.create_backup(str(self.mock_saves), "TestGame", note="Test Save Point")
        self.assertTrue(res.get("success"), f"Fallo al crear respaldo: {res}")

        zip_path = Path(res["zip_path"])
        self.assertTrue(zip_path.exists())

        # Verificar contenido del ZIP
        with zipfile.ZipFile(zip_path, "r") as zf:
            namelist = zf.namelist()
            self.assertIn("slot1.sav", namelist)
            self.assertIn("settings.ini", namelist)

        # Verificar consulta de versiones
        versions = BackupManager.get_game_versions("TestGame", str(self.mock_saves))
        self.assertGreaterEqual(len(versions), 1)
        self.assertEqual(versions[0]["note"], "Test Save Point")

        # Verificar conteo de versiones (claves normalizadas en minúsculas)
        counts = BackupManager.get_version_counts()
        self.assertGreaterEqual(counts.get("testgame", 0), 1)

    def test_revert_version_with_safety_backup(self):
        """Verifica que la reversión a una versión anterior restaure los archivos y cree copia de seguridad."""
        res1 = BackupManager.create_backup(str(self.mock_saves), "TestGame", note="V1 Original")
        zip_v1 = res1["zip_path"]

        # Modificar archivo de guardado
        (self.mock_saves / "slot1.sav").write_bytes(b"DATA_MODIFIED_SLOT_CORRUPTED")

        # Revertir a V1
        revert_res = BackupManager.revert_to_version(zip_v1, str(self.mock_saves), create_safety_backup=True)
        self.assertTrue(revert_res.get("success"), f"Fallo al revertir: {revert_res}")

        # El contenido debe volver a ser el original
        restored_data = (self.mock_saves / "slot1.sav").read_bytes()
        self.assertEqual(restored_data, b"DATA_SAVE_SLOT_1_SAMPLE")

        # Debe haberse creado un respaldo de seguridad previo a la reversión
        self.assertIn("safety_backup", revert_res)
        safety_zip = Path(revert_res["safety_backup"]["zip_path"])
        self.assertTrue(safety_zip.exists())

    def test_create_and_restore_master_backup(self):
        """Verifica la generación y restauración de un paquete consolidado Maestro."""
        selected_games = [{
            "name": "TestGame",
            "path": str(self.mock_saves),
            "platform": "Documents"
        }]

        # Crear respaldo maestro
        master_res = BackupManager.create_master_backup(selected_games, "UnitMasterBackup")
        self.assertTrue(master_res.get("success"))
        master_zip = Path(master_res["zip_path"])
        self.assertTrue(master_zip.exists())

        # Simular pérdida de archivos
        shutil.rmtree(self.mock_saves)
        self.assertFalse(self.mock_saves.exists())

        # Restaurar desde el respaldo maestro
        restore_res = BackupManager.restore_master_backup(str(master_zip))
        self.assertTrue(restore_res.get("success"))
        self.assertTrue(self.mock_saves.exists())
        self.assertTrue((self.mock_saves / "slot1.sav").exists())


class TestAnalytics(unittest.TestCase):
    def test_analytics_with_empty_data(self):
        """Verifica que la telemetría maneje de forma segura listas vacías."""
        report = AnimusAnalytics.get_telemetry([])
        self.assertEqual(report["total_games"], 0)
        self.assertEqual(report["total_size_str"], "0 MB")
        self.assertEqual(report["platform_distribution"], [])

    def test_analytics_calculation(self):
        """Verifica el cálculo de estadísticas y métricas agregadas."""
        mock_games = [
            {"name": "Game A", "platform": "Steam", "total_size": 1000, "size_str": "1 KB", "file_count": 5, "last_modified": "2026-01-01 12:00:00"},
            {"name": "Game B", "platform": "Epic Games", "total_size": 2000, "size_str": "2 KB", "file_count": 10, "last_modified": "2026-01-02 12:00:00"},
            {"name": "Game C", "platform": "Steam", "total_size": 3000, "size_str": "3 KB", "file_count": 15, "last_modified": "2026-01-03 12:00:00"},
        ]
        report = AnimusAnalytics.get_telemetry(mock_games)
        self.assertEqual(report["total_games"], 3)
        self.assertEqual(len(report["top_storage"]), 3)
        self.assertEqual(len(report["recent_activity"]), 3)
        categories = {p["category"]: p["count"] for p in report["platform_distribution"]}
        self.assertEqual(categories.get("Steam Oficial"), 2)


class TestSchedulerAndCloud(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.scheduler = BackupScheduler()
        self.scheduler.config_file = Path(self.temp_dir.name) / "scheduler.json"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_scheduler_save_and_load(self):
        """Verifica el guardado y recuperación de la configuración del programador de respaldos."""
        cfg = {"enabled": True, "interval_hours": 6, "retention_days": 15}
        self.scheduler.save_config(cfg)

        loaded = self.scheduler.get_config()
        self.assertTrue(loaded.get("enabled"))
        self.assertEqual(loaded.get("interval_hours"), 6)
        self.assertEqual(loaded.get("retention_days"), 15)

    def test_cloud_providers_detection(self):
        """Verifica que la detección de proveedores en la nube se ejecute de forma segura."""
        providers = CloudSyncManager.detect_cloud_providers()
        self.assertIsInstance(providers, list)
        for p in providers:
            self.assertIn("id", p)
            self.assertIn("name", p)
            self.assertIn("available", p)


class TestSaveVaultApi(unittest.TestCase):
    def setUp(self):
        self.api = SaveVaultApi()

    def test_api_methods_never_crash(self):
        """Verifica que ningún método expuesto a JavaScript lance excepciones no controladas."""
        self.assertIsInstance(self.api.scan_games(), list)
        self.assertIsInstance(self.api.get_version_counts(), dict)
        self.assertIsInstance(self.api.get_backups(), list)
        self.assertIsInstance(self.api.get_cloud_providers(), list)
        self.assertIsInstance(self.api.get_scheduler_config(), dict)
        self.assertIsInstance(self.api.get_analytics([]), dict)


if __name__ == "__main__":
    unittest.main()
