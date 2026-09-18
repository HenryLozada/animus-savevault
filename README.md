# Animus SaveVault 🎮

**Animus SaveVault** es una aplicación de escritorio moderna y de alto rendimiento para Windows diseñada para **localizar, catalogar, respaldar y explorar los archivos de guardado (*savegames / savedata*)** de todos tus videojuegos de PC.

---

## 🚀 Características Principales

- **Multi-Plataforma Oficial & Lanzadores de PC**:
  - **Steam**: Escaneo de manifiestos `appmanifest_*.acf`, `libraryfolders.vdf` y almacenamiento en la nube en `userdata/<SteamID>/<AppID>`.
  - **Epic Games Launcher**: Detección de manifiestos `.item` en `%PROGRAMDATA%\Epic\EpicGamesLauncher`, partidas de Unreal Engine en `%LOCALAPPDATA%\<Juego>\Saved\SaveGames` y correlación de títulos instalados.
  - **GOG Galaxy**: Detección en Registro de Windows (`HKLM\SOFTWARE\GOG.com\Games`) y base de datos local SQLite de Galaxy 2.0.
  - **EA App / Origin**: Detección en `%PROGRAMDATA%\EA Desktop\InstallData`, manifiestos de Origin y partidas en `Documentos\Electronic Arts`, `BioWare` y `Saved Games\Respawn`.
  - **Ubisoft Connect**: Resolución automática de nombres reales de juegos y escaneo de `savegames/<AccountID>/<GameID>`.
  - **Xbox Game Pass / Microsoft Store**: Detección de bibliotecas en `XboxGames` y contenedores WGS (*Windows Gaming Saves*) en `%LOCALAPPDATA%\Packages`.
  - **Heroic Games Launcher**: Integración directa con la caché JSON de juegos instalados de Epic y GOG.
  - **Rockstar Games**: Detección en `Documentos\Rockstar Games\<Juego>\Profiles` (GTA V, RDR2, etc.) correlacionado con lanzadores oficiales.


- **Soporte Completo para Repacks y Emuladores**:
  - **Goldberg SteamEmu**: Detección en `%APPDATA%\Goldberg SteamEmu Saves`.
  - **CODEX**: Detección en `C:\Users\Public\Documents\Steam\CODEX`.
  - **RUNE**: Detección en `C:\Users\Public\Documents\Steam\RUNE`.
  - **FLT (FairLight)**: Detección en `%APPDATA%\FLT`.
  - **Skidrow**: Detección en `%APPDATA%\SKIDROW` y `%LOCALAPPDATA%\SKIDROW`.
  - **EMPRESS**: Detección en `%APPDATA%\EMPRESS`.
  - **FitGirl / DODI / AnkerGames**: Reconocimiento automático de partidas de emuladores integrados.

- **Directorios Nativos de Windows & Heurística**:
  - `Saved Games` (Partidas Guardadas nativas de Windows).
  - `Documents` y `Documents\My Games`.
  - `%LOCALAPPDATA%Low` (Juegos de Unity e independientes).
  - Extensiones comunes analizadas: `.sav`, `.sl2` (FromSoftware), `.dat`, `.save`, `.bin`, `.profile`, `.json`, `.db`, `.sqlite`, `.xml`, `.bak`.

- **Acciones Rápidas & Control de Versiones**:
  - ⏱ **Historial de Versiones & Reversión**: Explora la línea temporal de estados guardados de cualquier juego, crea puntos de restauración con notas personalizadas (ej: *"Antes del Boss"*, *"Capítulo 4"*) y revierte tus partidas a estados anteriores en 1 clic con respaldo de seguridad pre-reversión automático.
  - 💾 **Crear Copia de Seguridad (.ZIP)**: Comprime y resguarda la partida con metadatos y marca de tiempo en `Mis Documentos\SavegameBackups`.
  - 📁 **Abrir en Explorador de Windows**: Llega a la carpeta exacta del juego con un solo clic.
  - 📋 **Copiar Ruta**: Botón rápido para copiar la ruta absoluta al portapapeles.
  - 🔍 **Búsqueda Instantánea & Filtros por Chips**: Filtra al instante por nombre, extensión o plataforma.

---

## 💻 Ejecución y Compilación

### Ejecutar en modo desarrollo:
```powershell
python main.py
```

### Compilar a ejecutable (.exe):
```powershell
python build.py
```
El archivo ejecutable compilado estará ubicado en:
`dist/AnimusSaveVault/AnimusSaveVault.exe`
