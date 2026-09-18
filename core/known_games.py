"""
Base de datos de patrones de guardado para juegos de PC conocidos,
plataformas oficiales y emuladores/repacks.
"""

from dataclasses import dataclass
from typing import List, Optional

@dataclass
class GameDefinition:
    name: str
    steam_appid: Optional[str] = None
    # Rutas relativas o patrones específicos por categoría
    saved_games_subpath: Optional[str] = None
    documents_subpath: Optional[str] = None
    appdata_local_subpath: Optional[str] = None
    appdata_locallow_subpath: Optional[str] = None
    appdata_roaming_subpath: Optional[str] = None
    extensions: Optional[List[str]] = None
    notes: Optional[str] = None

# Extensiones estándar de partidas guardadas
COMMON_SAVE_EXTENSIONS = {
    ".sav", ".save", ".dat", ".sl2", ".sl3", ".bin", ".profile",
    ".json", ".db", ".sqlite", ".xml", ".bak", ".slot", ".sav0",
    ".asav", ".gsv", ".savestat", ".sgd", ".sav_backup"
}

POPULAR_GAMES: List[GameDefinition] = [
    # CD Projekt Red
    GameDefinition(
        name="Cyberpunk 2077",
        steam_appid="1091500",
        saved_games_subpath=r"CD Projekt Red\Cyberpunk 2077",
        extensions=[".dat", ".json"]
    ),
    GameDefinition(
        name="The Witcher 3: Wild Hunt",
        steam_appid="292030",
        documents_subpath=r"The Witcher 3\gamesaves",
        extensions=[".sav"]
    ),

    # FromSoftware
    GameDefinition(
        name="Elden Ring",
        steam_appid="1245620",
        appdata_roaming_subpath=r"EldenRing",
        extensions=[".sl2", ".bak", ".co2"]
    ),
    GameDefinition(
        name="Dark Souls III",
        steam_appid="374320",
        appdata_roaming_subpath=r"DarkSoulsIII",
        extensions=[".sl2"]
    ),
    GameDefinition(
        name="Dark Souls II: Scholar of the First Sin",
        steam_appid="335300",
        appdata_roaming_subpath=r"DarkSoulsII",
        extensions=[".sl2"]
    ),
    GameDefinition(
        name="Dark Souls: Remastered",
        steam_appid="570940",
        documents_subpath=r"NBGI\DARK SOULS REMASTERED",
        extensions=[".sl2"]
    ),
    GameDefinition(
        name="Sekiro: Shadows Die Twice",
        steam_appid="814380",
        appdata_roaming_subpath=r"Sekiro",
        extensions=[".sl2"]
    ),
    GameDefinition(
        name="Armored Core VI: Fires of Rubicon",
        steam_appid="1888160",
        appdata_roaming_subpath=r"ArmoredCore6",
        extensions=[".sl2"]
    ),

    # Rockstar Games
    GameDefinition(
        name="Grand Theft Auto V",
        steam_appid="271590",
        documents_subpath=r"Rockstar Games\GTA V\Profiles",
        extensions=[".bak"]
    ),
    GameDefinition(
        name="Red Dead Redemption 2",
        steam_appid="1174180",
        documents_subpath=r"Rockstar Games\Red Dead Redemption 2\Profiles",
        extensions=[".dat"]
    ),
    GameDefinition(
        name="Red Dead Redemption",
        steam_appid="2668510",
        documents_subpath=r"Rockstar Games\Red Dead Redemption\Profiles",
        extensions=[".dat"]
    ),

    # Larian Studios
    GameDefinition(
        name="Baldur's Gate 3",
        steam_appid="1086940",
        appdata_local_subpath=r"Larian Studios\Baldur's Gate 3\PlayerProfiles\Public\Savegames\Story",
        extensions=[".lsv", ".png"]
    ),

    # Bethesda
    GameDefinition(
        name="The Elder Scrolls V: Skyrim Special Edition",
        steam_appid="489830",
        documents_subpath=r"My Games\Skyrim Special Edition\Saves",
        extensions=[".ess", ".skse", ".bak"]
    ),
    GameDefinition(
        name="The Elder Scrolls V: Skyrim",
        steam_appid="72850",
        documents_subpath=r"My Games\Skyrim\Saves",
        extensions=[".ess"]
    ),
    GameDefinition(
        name="Fallout 4",
        steam_appid="377160",
        documents_subpath=r"My Games\Fallout4\Saves",
        extensions=[".fos", ".f4se"]
    ),
    GameDefinition(
        name="Fallout: New Vegas",
        steam_appid="22380",
        documents_subpath=r"My Games\FalloutNV\Saves",
        extensions=[".fos", ".nvse"]
    ),
    GameDefinition(
        name="Starfield",
        steam_appid="1716740",
        documents_subpath=r"My Games\Starfield\Saves",
        extensions=[".sfs"]
    ),

    # Sony PlayStation PC Ports
    GameDefinition(
        name="God of War",
        steam_appid="1593500",
        saved_games_subpath=r"God of War",
        extensions=[".sav"]
    ),
    GameDefinition(
        name="Marvel's Spider-Man Remastered",
        steam_appid="1817070",
        documents_subpath=r"Marvel's Spider-Man Remastered",
        extensions=[".save"]
    ),
    GameDefinition(
        name="Marvel's Spider-Man: Miles Morales",
        steam_appid="1817190",
        documents_subpath=r"Marvel's Spider-Man Miles Morales",
        extensions=[".save"]
    ),
    GameDefinition(
        name="Ghost of Tsushima DIRECTOR'S CUT",
        steam_appid="2215430",
        documents_subpath=r"Ghost of Tsushima DIRECTOR'S CUT",
        extensions=[".sav"]
    ),
    GameDefinition(
        name="Horizon Zero Dawn",
        steam_appid="1151640",
        documents_subpath=r"Horizon Zero Dawn\Saved Game",
        extensions=[".dat", ".bin"]
    ),
    GameDefinition(
        name="Horizon Forbidden West",
        steam_appid="2420110",
        documents_subpath=r"Horizon Forbidden West Complete Edition",
        extensions=[".dat", ".bin"]
    ),
    GameDefinition(
        name="Days Gone",
        steam_appid="1259420",
        appdata_local_subpath=r"BendGame\Saved",
        extensions=[".sav"]
    ),
    GameDefinition(
        name="The Last of Us Part I",
        steam_appid="1888930",
        saved_games_subpath=r"The Last of Us Part I\users",
        extensions=[".dat"]
    ),

    # Capcom (Resident Evil, Monster Hunter, DMC)
    GameDefinition(
        name="Resident Evil 4 Remake",
        steam_appid="2050650",
        extensions=[".bin", ".dat"]
    ),
    GameDefinition(
        name="Resident Evil Village",
        steam_appid="1196590",
        extensions=[".bin", ".dat"]
    ),
    GameDefinition(
        name="Resident Evil 2 Remake",
        steam_appid="883710",
        extensions=[".bin", ".dat"]
    ),
    GameDefinition(
        name="Resident Evil 3 Remake",
        steam_appid="952060",
        extensions=[".bin", ".dat"]
    ),
    GameDefinition(
        name="Resident Evil 7 Biohazard",
        steam_appid="418370",
        extensions=[".bin", ".dat"]
    ),
    GameDefinition(
        name="Devil May Cry 5",
        steam_appid="601150",
        extensions=[".bin", ".dat"]
    ),
    GameDefinition(
        name="Monster Hunter: World",
        steam_appid="582010",
        extensions=[".bin"]
    ),
    GameDefinition(
        name="Monster Hunter Rise",
        steam_appid="1446780",
        extensions=[".bin"]
    ),

    # Unreal Engine Games (SaveGames comunes en AppData/Local/<Project>/Saved/SaveGames)
    GameDefinition(
        name="Hogwarts Legacy",
        steam_appid="990080",
        appdata_local_subpath=r"Hogwarts Legacy\Saved\SaveGames",
        extensions=[".sav"]
    ),
    GameDefinition(
        name="Palworld",
        steam_appid="1623730",
        appdata_local_subpath=r"Pal\Saved\SaveGames",
        extensions=[".sav"]
    ),
    GameDefinition(
        name="Lies of P",
        steam_appid="1627720",
        appdata_local_subpath=r"LiesofP\Saved\SaveGames",
        extensions=[".sav"]
    ),
    GameDefinition(
        name="Black Myth: Wukong",
        steam_appid="2358720",
        appdata_local_subpath=r"b1\Saved\SaveGames",
        extensions=[".sav"]
    ),
    GameDefinition(
        name="Satisfactory",
        steam_appid="526870",
        appdata_local_subpath=r"FactoryGame\Saved\SaveGames",
        extensions=[".sav"]
    ),
    GameDefinition(
        name="Remnant II",
        steam_appid="1282100",
        saved_games_subpath=r"Remnant2\Saved\SaveGames",
        extensions=[".sav"]
    ),
    GameDefinition(
        name="STAR WARS Jedi: Survivor",
        steam_appid="1774580",
        saved_games_subpath=r"Respawn\JediSurvivor",
        extensions=[".sav"]
    ),
    GameDefinition(
        name="STAR WARS Jedi: Fallen Order",
        steam_appid="1172380",
        saved_games_subpath=r"Respawn\JediFallenOrder",
        extensions=[".sav"]
    ),
    GameDefinition(
        name="Stray",
        steam_appid="1332010",
        appdata_local_subpath=r"Hk_project\Saved\SaveGames",
        extensions=[".sav"]
    ),

    # Unity & Indie Games
    GameDefinition(
        name="Hollow Knight",
        steam_appid="367520",
        appdata_locallow_subpath=r"Team Cherry\Hollow Knight",
        extensions=[".dat"]
    ),
    GameDefinition(
        name="Valheim",
        steam_appid="892970",
        appdata_locallow_subpath=r"IronGate\Valheim",
        extensions=[".db", ".fwl"]
    ),
    GameDefinition(
        name="Sons Of The Forest",
        steam_appid="1326470",
        appdata_locallow_subpath=r"Endnight\SonsOfTheForest\Saves",
        extensions=[".json"]
    ),
    GameDefinition(
        name="The Forest",
        steam_appid="242760",
        appdata_locallow_subpath=r"Endnight\TheForest",
        extensions=[".dat"]
    ),
    GameDefinition(
        name="Lethal Company",
        steam_appid="1966720",
        appdata_locallow_subpath=r"ZeekerssRBLX\Lethal Company",
        extensions=[".txt"]
    ),
    GameDefinition(
        name="Stardew Valley",
        steam_appid="413150",
        appdata_roaming_subpath=r"StardewValley\Saves",
        extensions=[".xml", ""]
    ),
    GameDefinition(
        name="Balatro",
        steam_appid="2379780",
        appdata_roaming_subpath=r"Balatro",
        extensions=[".jkr"]
    ),
    GameDefinition(
        name="Hades",
        steam_appid="1145360",
        documents_subpath=r"Saved Games\Hades",
        saved_games_subpath=r"Hades",
        extensions=[".sav"]
    ),
    GameDefinition(
        name="Hades II",
        steam_appid="1145350",
        saved_games_subpath=r"Hades II",
        extensions=[".sav"]
    ),
    GameDefinition(
        name="Terraria",
        steam_appid="105600",
        documents_subpath=r"My Games\Terraria",
        extensions=[".plr", ".wld"]
    ),
    GameDefinition(
        name="Project Zomboid",
        steam_appid="108600",
        documents_subpath=r"..\Zomboid\Saves",
        extensions=[".bin"]
    ),

    # Square Enix / JRPG
    GameDefinition(
        name="FINAL FANTASY VII REMAKE",
        steam_appid="1462040",
        documents_subpath=r"My Games\FINAL FANTASY VII REMAKE\Saved\SaveGames",
        extensions=[".sav"]
    ),
    GameDefinition(
        name="FINAL FANTASY XVI",
        steam_appid="2515020",
        documents_subpath=r"My Games\FINAL FANTASY XVI\Saved\SaveGames",
        extensions=[".sav"]
    ),
    GameDefinition(
        name="NieR:Automata",
        steam_appid="524220",
        documents_subpath=r"My Games\NieR_Automata",
        extensions=[".dat"]
    ),

    # EA Games
    GameDefinition(
        name="The Sims 4",
        steam_appid="1222670",
        documents_subpath=r"Electronic Arts\The Sims 4\saves",
        extensions=[".save"]
    ),
    GameDefinition(
        name="Dead Space (2023)",
        steam_appid="1693980",
        documents_subpath=r"Dead Space (2023)\settings",
        extensions=[".sav"]
    ),
    GameDefinition(
        name="Mass Effect Legendary Edition",
        steam_appid="1328670",
        documents_subpath=r"BioWare\Mass Effect Legendary Edition\Save",
        extensions=[".pcsav"]
    ),

    # Microsoft / Xbox Game Studios
    GameDefinition(
        name="Forza Horizon 5",
        steam_appid="1551360",
        appdata_local_subpath=r"ForzaHorizon5",
        extensions=[".dat"]
    ),
    GameDefinition(
        name="Forza Horizon 4",
        steam_appid="1293830",
        appdata_local_subpath=r"ForzaHorizon4",
        extensions=[".dat"]
    ),
]

# Mapa por Steam AppID
GAMES_BY_APPID = {g.steam_appid: g for g in POPULAR_GAMES if g.steam_appid}
