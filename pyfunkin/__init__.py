"""
================================================================================
PyFunkin Engine (`FNF Lite`) — Official Python Package (`pyfunkin`)
================================================================================
🇬🇧 EN: Lightweight, cross-platform Friday Night Funkin' Engine in Python.
       Created by @PyFunkinDev (https://github.com/PyFunkinDev/PyFunkin-Engine).
🇺🇦 UA: Легкий кросплатформений рушій Friday Night Funkin' на Python.
       Розробник: @PyFunkinDev (https://github.com/PyFunkinDev/PyFunkin-Engine).
================================================================================
"""

from .core import (
    Conductor,
    Constants,
    Signal,
    SongEventData,
    SongNoteData,
    SongTimeChange,
    round_decimal,
)
from .atlas import (
    AnimationDef,
    AtlasFrame,
    CharacterData,
    CharacterRenderType,
    parse_animate_atlas,
    parse_packer_txt,
    parse_sparrow_xml,
)
from .scoring import (
    Highscore,
    Scoring,
    ScoringRank,
    ScoringSystem,
    Tallies,
)
from .paths import (
    Paths,
    StageData,
    StageDataCharacter,
    StageDataProp,
)
from .mobile import (
    FunkinHint,
    FunkinHintAlphaStyle,
    FunkinHitbox,
    FunkinHitboxControlSchemes,
    NoteDirection,
    PreciseInputEvent,
    PreciseInputManager,
)
from .modding import (
    HybridModHandler,
    ModMetadata,
    ScriptEvent,
    ScriptEventType,
)
from .save import (
    LevelData,
    LevelPropData,
    Preferences,
    Save,
    SaveOptions,
    SaveScoreRecord,
)
from .audio import (
    FunkinSound,
    VoicesGroup,
)
from .graphics import (
    CountdownStep,
    FunkinCamera,
    FunkinSprite,
    HealthIcon,
    JudgementPopup,
)
from .states import (
    FreeplayState,
    GameOverSubState,
    MainMenuState,
    MusicBeatState,
    OptionsState,
    PauseSubState,
    ResultState,
    StoryMenuState,
    TitleState,
)
from .playstate import (
    PlayState,
    Strumline,
)
from .main import (
    FunkinDebugDisplay,
    FunkinMemory,
    PyFunkinEngineApp,
    run_self_test,
)

__version__ = Constants.VERSION
__author__ = "PyFunkinDev"

__all__ = [
    "Conductor",
    "Constants",
    "Signal",
    "SongEventData",
    "SongNoteData",
    "SongTimeChange",
    "round_decimal",
    "AnimationDef",
    "AtlasFrame",
    "CharacterData",
    "CharacterRenderType",
    "parse_animate_atlas",
    "parse_packer_txt",
    "parse_sparrow_xml",
    "Highscore",
    "Scoring",
    "ScoringRank",
    "ScoringSystem",
    "Tallies",
    "Paths",
    "StageData",
    "StageDataCharacter",
    "StageDataProp",
    "FunkinHint",
    "FunkinHintAlphaStyle",
    "FunkinHitbox",
    "FunkinHitboxControlSchemes",
    "NoteDirection",
    "PreciseInputEvent",
    "PreciseInputManager",
    "HybridModHandler",
    "ModMetadata",
    "ScriptEvent",
    "ScriptEventType",
    "LevelData",
    "LevelPropData",
    "Preferences",
    "Save",
    "SaveOptions",
    "SaveScoreRecord",
    "FunkinSound",
    "VoicesGroup",
    "CountdownStep",
    "FunkinCamera",
    "FunkinSprite",
    "HealthIcon",
    "JudgementPopup",
    "FreeplayState",
    "GameOverSubState",
    "MainMenuState",
    "MusicBeatState",
    "OptionsState",
    "PauseSubState",
    "ResultState",
    "StoryMenuState",
    "TitleState",
    "PlayState",
    "Strumline",
    "FunkinDebugDisplay",
    "FunkinMemory",
    "PyFunkinEngineApp",
    "run_self_test",
]
