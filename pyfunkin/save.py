"""
================================================================================
PyFunkin Engine (FNF Lite) — Save System, Preferences & Story Levels (`pyfunkin/save.py`)
================================================================================
🇬🇧 EN: Clean, memory-optimized (`__slots__`) Python port of:
       - `source/funkin/Preferences.hx` (Global settings, mobile defaults, 32-bit RAM mode)
       - `source/funkin/save/Save.hx` (Highscores, Rank saving, JSON persistence)
       - `source/funkin/data/story/LevelData.hx` (`preload/data/levels/week*.json`)
       - `source/funkin/data/dialogue/ConversationData.hx`
🇺🇦 UA: Система збережень, налаштувань гравця (`Preferences`) та рівнів Story Mode:
       - Як і в офіційному `Preferences.hx`, на мобілках `downscroll` увімкнений за замовчуванням!
       - Зберігає рекорди очок та рангів кожної пісні у легкий файл `save_data.json`.
================================================================================
"""

from __future__ import annotations
import json
import os
import sys
from typing import Any, Dict, List, Optional
from .atlas import AnimationDef
from .mobile import FunkinHitboxControlSchemes
from .scoring import ScoringRank


def _is_mobile_environment() -> bool:
    """
    🇬🇧 Detects Android (Pydroid 3, Termux, Kivy/Buildozer APK) or iOS environment.
    🇺🇦 Автоматично визначає, чи запущена гра на телефоні (Android / Pydroid 3 / Termux / APK).
    """
    if "ANDROID_ARGUMENT" in os.environ or "ANDROID_ROOT" in os.environ or "PYDROID_RPC" in os.environ:
        return True
    return sys.platform in ("android", "ios")


class SaveOptions:
    """
    🇬🇧 User options stored inside `Save.instance.options` (`Preferences.hx`).
       Note from `Preferences.hx` line 101:
       `downscroll` defaults to `true` on mobile (`#if mobile ?? true #else ?? false #end`)!
    🇺🇦 Налаштування гравця. На телефонах `downscroll` увімкнений за замовчуванням,
       щоб пальці знизу екрана не закривали стрілочки, які летять зверху!
    """
    __slots__ = (
        "framerate",
        "downscroll",
        "flashingLights",
        "zoomCamera",
        "debugDisplay",
        "hapticsMode",
        "controlsScheme",
        "globalOffset",
        "audioVisualOffset",
        "volumeMaster",
        "volumeMusic",
        "volumeSFX",
        "lowMemory32BitMode",
        "botplay",
    )

    def __init__(self) -> None:
        is_mob = _is_mobile_environment()
        self.framerate: int = 60
        self.downscroll: bool = is_mob
        self.flashingLights: bool = True
        self.zoomCamera: bool = True
        self.debugDisplay: str = "On"  # 'Off' | 'On' (FPS + RAM counter)
        self.hapticsMode: str = "All"  # 'None' | 'Notes Only' | 'All'
        self.controlsScheme: str = FunkinHitboxControlSchemes.FOUR_LANES
        self.globalOffset: int = 0
        self.audioVisualOffset: int = 0
        self.volumeMaster: float = 1.0
        self.volumeMusic: float = 1.0
        self.volumeSFX: float = 0.8
        # 🇬🇧 Special PyFunkin Lite optimization for 32-bit (ARMv7) devices with <=3GB RAM!
        # 🇺🇦 Спеціальний режим економії оперативки для 32-бітних (ARMv7) смартфонів!
        self.lowMemory32BitMode: bool = (sys.maxsize <= 2**32)
        self.botplay: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {slot: getattr(self, slot) for slot in self.__slots__}

    def from_dict(self, d: Dict[str, Any]) -> None:
        for slot in self.__slots__:
            if slot in d:
                setattr(self, slot, d[slot])


class SaveScoreRecord:
    """
    🇬🇧 Saved highscore and rank for a song/difficulty (`SaveScoreData` in `Save.hx`).
    🇺🇦 Збережений рекорд очок, точності та рангу для конкретної пісні й складності.
    """
    __slots__ = ("score", "rank", "accuracy", "maxCombo")

    def __init__(self, score: int = 0, rank: str = ScoringRank.SHIT, accuracy: float = 0.0, maxCombo: int = 0) -> None:
        self.score: int = int(score)
        self.rank: str = str(rank)
        self.accuracy: float = float(accuracy)
        self.maxCombo: int = int(maxCombo)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": self.score,
            "rank": self.rank,
            "accuracy": self.accuracy,
            "maxCombo": self.maxCombo,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "SaveScoreRecord":
        return cls(
            score=int(d.get("score", 0)),
            rank=str(d.get("rank", ScoringRank.SHIT)),
            accuracy=float(d.get("accuracy", 0.0)),
            maxCombo=int(d.get("maxCombo", 0)),
        )


class Save:
    """
    🇬🇧 Handles reading and flushing save data (`Save.hx`).
    🇺🇦 Відповідає за збереження рекордів і налаштувань у файл `save_data.json`.
    """
    _instance: Optional["Save"] = None
    SAVE_FILE: str = "save_data.json"

    @classmethod
    def get_instance(cls) -> "Save":
        if cls._instance is None:
            cls._instance = Save()
            cls._instance.load()
        return cls._instance

    def __init__(self) -> None:
        self.options: SaveOptions = SaveOptions()
        self.song_scores: Dict[str, SaveScoreRecord] = {}

    def _make_key(self, song_id: str, difficulty: str = "normal", variation: str = "default") -> str:
        return f"{song_id.lower()}:{difficulty.lower()}:{variation.lower()}"

    def get_song_score(self, song_id: str, difficulty: str = "normal", variation: str = "default") -> Optional[SaveScoreRecord]:
        return self.song_scores.get(self._make_key(song_id, difficulty, variation))

    def set_song_score(
        self,
        song_id: str,
        difficulty: str,
        score: int,
        rank: str,
        accuracy: float,
        max_combo: int,
        variation: str = "default",
    ) -> bool:
        """
        🇬🇧 Updates the saved score/rank if higher than existing record. Returns `True` if new highscore!
        🇺🇦 Оновлює збережений рекорд, якщо новий результат кращий за попередній.
        """
        key = self._make_key(song_id, difficulty, variation)
        prev = self.song_scores.get(key)
        is_new_best = prev is None or score > prev.score
        best_score = max(score, prev.score) if prev else score
        best_rank = rank if (prev is None or ScoringRank.is_better(rank, prev.rank)) else prev.rank
        best_acc = max(accuracy, prev.accuracy) if prev else accuracy
        best_combo = max(max_combo, prev.maxCombo) if prev else max_combo

        self.song_scores[key] = SaveScoreRecord(
            score=best_score,
            rank=best_rank,
            accuracy=best_acc,
            maxCombo=best_combo,
        )
        self.flush()
        return is_new_best

    def flush(self, file_path: Optional[str] = None) -> None:
        target = file_path or self.SAVE_FILE
        payload = {
            "version": "2.0.0-py",
            "options": self.options.to_dict(),
            "song_scores": {k: v.to_dict() for k, v in self.song_scores.items()},
        }
        try:
            with open(target, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
        except OSError:
            pass

    def load(self, file_path: Optional[str] = None) -> None:
        target = file_path or self.SAVE_FILE
        if not os.path.exists(target):
            return
        try:
            with open(target, "r", encoding="utf-8") as f:
                data = json.load(f)
            if "options" in data:
                self.options.from_dict(data["options"])
            if "song_scores" in data:
                self.song_scores = {
                    k: SaveScoreRecord.from_dict(v) for k, v in data["song_scores"].items()
                }
        except (OSError, ValueError):
            pass


class Preferences:
    """
    🇬🇧 Global static accessors to user preferences (`source/funkin/Preferences.hx`).
    🇺🇦 Швидкий глобальний доступ до налаштувань гравця.
    """
    @classmethod
    def get_options(cls) -> SaveOptions:
        return Save.get_instance().options


# ==============================================================================
# STORY MODE LEVEL DATA (`preload/data/levels/week1.json` .. `week7.json`)
# ==============================================================================

class LevelPropData:
    """
    🇬🇧 Animated prop shown in the Story Menu (`storymenu/props/dad`, `bf`, `gf`).
    🇺🇦 Анімований персонаж у меню вибору тижня Story Mode.
    """
    __slots__ = ("assetPath", "scale", "offsets", "animations")

    def __init__(
        self,
        assetPath: str,
        scale: float = 1.0,
        offsets: Optional[List[float]] = None,
        animations: Optional[List[AnimationDef]] = None,
    ) -> None:
        self.assetPath: str = assetPath
        self.scale: float = scale
        self.offsets: List[float] = offsets if offsets is not None else [0.0, 0.0]
        self.animations: List[AnimationDef] = animations if animations is not None else []

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "LevelPropData":
        return cls(
            assetPath=str(d.get("assetPath", "")),
            scale=float(d.get("scale", 1.0)),
            offsets=[float(x) for x in d.get("offsets", [0.0, 0.0])],
            animations=[AnimationDef.from_dict(a) for a in d.get("animations", [])],
        )


class LevelData:
    """
    🇬🇧 Represents a Story Mode Week (`preload/data/levels/week1.json`, etc.).
    🇺🇦 Описує один тиждень Story Mode (назва, колір фону `#F9CF51`, список пісень `['bopeebo', 'fresh', 'dadbattle']`).
    """
    __slots__ = ("levelId", "version", "name", "titleAsset", "background", "songs", "props", "visible")

    def __init__(
        self,
        levelId: str,
        version: str = "1.0.0",
        name: str = "UNKNOWN WEEK",
        titleAsset: str = "",
        background: str = "#F9CF51",
        songs: Optional[List[str]] = None,
        props: Optional[List[LevelPropData]] = None,
        visible: bool = True,
    ) -> None:
        self.levelId: str = levelId
        self.version: str = version
        self.name: str = name
        self.titleAsset: str = titleAsset
        self.background: str = background
        self.songs: List[str] = songs if songs is not None else []
        self.props: List[LevelPropData] = props if props is not None else []
        self.visible: bool = visible

    @classmethod
    def from_json(cls, levelId: str, raw_json: str) -> "LevelData":
        d = json.loads(raw_json.lstrip("\ufeff").strip())
        return cls(
            levelId=levelId,
            version=str(d.get("version", "1.0.0")),
            name=str(d.get("name", levelId.upper())),
            titleAsset=str(d.get("titleAsset", "")),
            background=str(d.get("background", "#F9CF51")),
            songs=[str(s) for s in d.get("songs", [])],
            props=[LevelPropData.from_dict(p) for p in d.get("props", [])],
            visible=bool(d.get("visible", True)),
        )
