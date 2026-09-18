import os
import ctypes
from ctypes import wintypes
from pathlib import Path
import winreg

# Windows KnownFolder GUIDs
class GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", wintypes.DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", wintypes.BYTE * 8)
    ]

    @classmethod
    def from_str(cls, guid_str: str):
        import uuid
        u = uuid.UUID(guid_str)
        data4 = (wintypes.BYTE * 8)(*u.bytes[8:])
        return cls(u.time_low, u.time_mid, u.time_hi_version, data4)

FOLDERID_SavedGames = GUID.from_str("4C5C32FF-BB9D-43B0-B5B4-2D72E54EAAA4")
FOLDERID_Documents = GUID.from_str("FDD39AD0-238F-46AF-ADB4-6C85480369C7")
FOLDERID_RoamingAppData = GUID.from_str("3EB685CD-9436-4359-ACF8-0C7B25F81E3D")
FOLDERID_LocalAppData = GUID.from_str("F1B32785-6FBA-4FCF-9D55-7B8E7F157091")
FOLDERID_LocalAppDataLow = GUID.from_str("A5200CA2-A703-49D1-9B5A-0267D2F5F4FF")
FOLDERID_PublicDocuments = GUID.from_str("ED4824AF-DCE4-45A8-81E2-FC7965083634")
FOLDERID_ProgramData = GUID.from_str("62AB5D82-FDC1-4DC3-A9DD-070D1D495D97")

def get_known_folder_path(folder_guid: GUID, fallback_env: str = None) -> Path:
    """Obtiene la ruta real de una carpeta conocida de Windows mediante SHGetKnownFolderPath."""
    try:
        shell32 = ctypes.windll.shell32
        SHGetKnownFolderPath = shell32.SHGetKnownFolderPath
        SHGetKnownFolderPath.argtypes = [
            ctypes.POINTER(GUID),
            wintypes.DWORD,
            wintypes.HANDLE,
            ctypes.POINTER(ctypes.c_wchar_p)
        ]
        SHGetKnownFolderPath.restype = ctypes.c_long

        path_ptr = ctypes.c_wchar_p()
        hr = SHGetKnownFolderPath(ctypes.byref(folder_guid), 0, None, ctypes.byref(path_ptr))
        if hr == 0 and path_ptr.value:
            resolved = Path(path_ptr.value)
            ctypes.windll.ole32.CoTaskMemFree(path_ptr)
            return resolved
    except Exception:
        pass

    if fallback_env and os.environ.get(fallback_env):
        return Path(os.environ[fallback_env])
    return None

class SystemPaths:
    @staticmethod
    def saved_games() -> Path:
        p = get_known_folder_path(FOLDERID_SavedGames)
        if p and p.exists():
            return p
        fallback = Path.home() / "Saved Games"
        if fallback.exists():
            return fallback
        return fallback

    @staticmethod
    def documents() -> Path:
        p = get_known_folder_path(FOLDERID_Documents)
        if p and p.exists():
            return p
        fallback = Path.home() / "Documents"
        return fallback

    @staticmethod
    def appdata_roaming() -> Path:
        roaming = os.environ.get("APPDATA")
        if roaming:
            return Path(roaming)
        p = get_known_folder_path(FOLDERID_RoamingAppData)
        return p if p else Path.home() / "AppData" / "Roaming"

    @staticmethod
    def appdata_local() -> Path:
        local = os.environ.get("LOCALAPPDATA")
        if local:
            return Path(local)
        p = get_known_folder_path(FOLDERID_LocalAppData)
        return p if p else Path.home() / "AppData" / "Local"

    @staticmethod
    def appdata_locallow() -> Path:
        local = os.environ.get("LOCALAPPDATA")
        if local:
            p = Path(local).parent / "LocalLow"
            if p.exists():
                return p
        fallback = Path.home() / "AppData" / "LocalLow"
        if fallback.exists():
            return fallback
        res = get_known_folder_path(FOLDERID_LocalAppDataLow)
        return res if res and res.name.lower() == "locallow" else fallback

    @staticmethod
    def public_documents() -> Path:
        res = get_known_folder_path(FOLDERID_PublicDocuments)
        if not res.exists():
            public = os.environ.get("PUBLIC", r"C:\Users\Public")
            return Path(public) / "Documents"
        return res

    @staticmethod
    def program_data() -> Path:
        return get_known_folder_path(FOLDERID_ProgramData, "PROGRAMDATA")

def get_steam_install_path() -> Path | None:
    """Busca la ruta de instalación de Steam en el registro de Windows."""
    for reg_key in [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Valve\Steam"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Valve\Steam"),
    ]:
        try:
            with winreg.OpenKey(reg_key[0], reg_key[1]) as key:
                val, _ = winreg.QueryValueEx(key, "InstallPath")
                p = Path(val)
                if p.exists():
                    return p
        except Exception:
            continue
    for candidate in [
        Path(r"C:\Program Files (x86)\Steam"),
        Path(r"C:\Program Files\Steam"),
        Path(r"D:\Steam"),
        Path(r"E:\Steam"),
    ]:
        if candidate.exists():
            return candidate
    return None

def get_ubisoft_save_path() -> Path | None:
    """Busca el directorio de savegames de Ubisoft Connect."""
    for reg_key in [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Ubisoft\Launcher"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Ubisoft\Launcher"),
    ]:
        try:
            with winreg.OpenKey(reg_key[0], reg_key[1]) as key:
                val, _ = winreg.QueryValueEx(key, "InstallDir")
                p = Path(val) / "savegames"
                if p.exists():
                    return p
        except Exception:
            continue
    for candidate in [
        Path(r"C:\Program Files (x86)\Ubisoft\Ubisoft Game Launcher\savegames"),
        Path(r"C:\Program Files\Ubisoft\Ubisoft Game Launcher\savegames"),
    ]:
        if candidate.exists():
            return candidate
    return None

def get_epic_manifests_path() -> Path | None:
    """Busca el directorio de manifiestos de Epic Games Launcher."""
    prog_data = SystemPaths.program_data()
    if prog_data:
        p = prog_data / "Epic" / "EpicGamesLauncher" / "Data" / "Manifests"
        if p.exists():
            return p
    return None

def get_ea_desktop_data_path() -> Path | None:
    """Busca el directorio de metadatos de instalación de EA Desktop."""
    prog_data = SystemPaths.program_data()
    if prog_data:
        p = prog_data / "EA Desktop" / "InstallData"
        if p.exists():
            return p
    return None

def get_gog_galaxy_storage_path() -> Path | None:
    """Busca el directorio de almacenamiento local de GOG Galaxy."""
    prog_data = SystemPaths.program_data()
    if prog_data:
        p = prog_data / "GOG.com" / "Galaxy" / "storage"
        if p.exists():
            return p
    return None

def get_heroic_config_path() -> Path | None:
    """Busca el directorio de configuración y caché de Heroic Games Launcher."""
    appdata = SystemPaths.appdata_roaming()
    if appdata:
        p = appdata / "heroic"
        if p.exists():
            return p
    return None

