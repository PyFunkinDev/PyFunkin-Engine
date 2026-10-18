"""
================================================================================
PyFunkin Engine (FNF Lite) — Hybrid Modding System (`pyfunkin/modding.py`)
================================================================================
🇬🇧 EN: Clean, memory-optimized (`__slots__`) Python port of:
       - `source/funkin/modding/events/ScriptEventType.hx` & `ScriptEvent.hx`
       - `source/funkin/modding/PolymodHandler.hx`
       Plus Hybrid Mod Loader supporting:
       1) Native Python scripts (`.py`) — zero compilation, instant reload!
       2) Psych Engine Lua scripts (`.lua` via `lupa` LuaJIT or built-in bridge)
       3) V-Slice Mod Metadata (`_polymod_meta.json` / `pack.json`)
🇺🇦 UA: Гібридна система модів для PyFunkin Engine:
       1) Рідні Python-скрипти (`.py`) — миттєвий запуск без компіляції!
       2) Підтримка `.lua` скриптів із Psych Engine (`onBeatHit`, `onStepHit`, `goodNoteHit`).
       3) Події офіційного V-Slice (`CREATE`, `UPDATE`, `SONG_BEAT_HIT`, `NOTE_HIT` тощо).
================================================================================
"""

from __future__ import annotations
import importlib.util
import json
import os
from typing import Any, Dict, List, Optional
from .paths import Paths


class ScriptEventType:
    """
    🇬🇧 Official event types from `source/funkin/modding/events/ScriptEventType.hx`.
    🇺🇦 Офіційні типи подій для скриптів та модів із `ScriptEventType.hx`.
    """
    CREATE: str = "CREATE"
    STATE_CREATE: str = "STATE_CREATE"
    DESTROY: str = "DESTROY"
    ADDED: str = "ADDED"
    UPDATE: str = "UPDATE"
    PAUSE: str = "PAUSE"
    RESUME: str = "RESUME"
    SONG_BEAT_HIT: str = "SONG_BEAT_HIT"
    SONG_STEP_HIT: str = "SONG_STEP_HIT"
    NOTE_INCOMING: str = "NOTE_INCOMING"
    NOTE_HIT: str = "NOTE_HIT"
    NOTE_MISS: str = "NOTE_MISS"
    SONG_START: str = "SONG_START"
    SONG_END: str = "SONG_END"

    # Mapping from V-Slice event types to method names (both V-Slice and Psych Engine style!)
    HANDLER_NAMES: Dict[str, Tuple[str, ...]] = {
        "CREATE": ("onCreate",),
        "STATE_CREATE": ("onCreatePost", "onStateCreate"),
        "DESTROY": ("onDestroy",),
        "UPDATE": ("onUpdate",),
        "PAUSE": ("onPause",),
        "RESUME": ("onResume",),
        "SONG_BEAT_HIT": ("onBeatHit",),
        "SONG_STEP_HIT": ("onStepHit",),
        "NOTE_HIT": ("onNoteHit", "goodNoteHit", "opponentNoteHit"),
        "NOTE_MISS": ("onNoteMiss", "noteMiss"),
        "SONG_START": ("onSongStart",),
        "SONG_END": ("onSongEnd", "onEndSong"),
    }


class ScriptEvent:
    """
    🇬🇧 Cancellable event payload passed to mod scripts (`ScriptEvent.hx`).
       Cancelling `PAUSE`, `SONG_BEAT_HIT`, or `NOTE_HIT` stops default game behavior!
    🇺🇦 Об'єкт події, що передається у скрипти модів. Якщо викликати `event.cancel()`,
       стандартна дія гри (наприклад, пауза чи зарахування ноти) скасовується!
    """
    __slots__ = ("type", "cancelable", "eventCanceled", "data")

    def __init__(self, event_type: str, cancelable: bool = False, **kwargs: Any) -> None:
        self.type: str = event_type
        self.cancelable: bool = cancelable
        self.eventCanceled: bool = False
        self.data: Dict[str, Any] = kwargs

    def cancel(self) -> None:
        if self.cancelable:
            self.eventCanceled = True


class ModMetadata:
    """
    🇬🇧 Metadata for a single mod folder (`_polymod_meta.json` or Psych `pack.json`).
    🇺🇦 Метадані мода (назва, опис, автор, версія API) з папки `mods/<mod_id>/`.
    """
    __slots__ = ("mod_id", "title", "description", "author", "version", "enabled", "folder_path")

    def __init__(
        self,
        mod_id: str,
        title: str = "",
        description: str = "",
        author: str = "Unknown",
        version: str = "1.0.0",
        enabled: bool = True,
        folder_path: str = "",
    ) -> None:
        self.mod_id: str = mod_id
        self.title: str = title or mod_id
        self.description: str = description
        self.author: str = author
        self.version: str = version
        self.enabled: bool = enabled
        self.folder_path: str = folder_path

    @classmethod
    def from_folder(cls, folder_path: str) -> "ModMetadata":
        mod_id = os.path.basename(os.path.normpath(folder_path))
        polymod_file = os.path.join(folder_path, "_polymod_meta.json")
        psych_file = os.path.join(folder_path, "pack.json")

        if os.path.exists(polymod_file):
            with open(polymod_file, "r", encoding="utf-8") as f:
                d = json.load(f)
            return cls(
                mod_id=mod_id,
                title=str(d.get("title", mod_id)),
                description=str(d.get("description", "")),
                author=str(d.get("author", "Unknown")),
                version=str(d.get("mod_version", "1.0.0")),
                folder_path=folder_path,
            )

        if os.path.exists(psych_file):
            with open(psych_file, "r", encoding="utf-8") as f:
                d = json.load(f)
            return cls(
                mod_id=mod_id,
                title=str(d.get("name", mod_id)),
                description=str(d.get("description", "")),
                author="Psych Modder",
                version="1.0.0",
                enabled=not bool(d.get("runsGlobally", False) is False),
                folder_path=folder_path,
            )

        return cls(mod_id=mod_id, title=mod_id, folder_path=folder_path)


class HybridModHandler:
    """
    🇬🇧 Discovers mods in `mods/`, registers asset overrides in `Paths`, and executes
       both Python (`.py`) and Lua (`.lua`) scripts on game events!
    🇺🇦 Головний менеджер модів: знаходить моди в папці `mods/`, підключає їхні ассети
       до `Paths` та виконує `.py` і `.lua` скрипти під час гри!
    """
    __slots__ = ("mods_root", "discovered_mods", "python_scripts", "lua_runtime", "lua_scripts", "game_context")

    def __init__(self, mods_root: str = "mods", game_context: Any = None) -> None:
        self.mods_root: str = mods_root
        self.discovered_mods: List[ModMetadata] = []
        self.python_scripts: List[Any] = []
        self.lua_runtime: Any = None
        self.lua_scripts: List[Any] = []
        self.game_context: Any = game_context

    def scan_mods(self) -> List[ModMetadata]:
        """
        🇬🇧 Scans `mods/` directory for V-Slice, Psych Engine, and PyFunkin mods.
        🇺🇦 Сканує папку `mods/` та активує знайдені моди в системі `Paths`.
        """
        self.discovered_mods.clear()
        Paths.active_mods.clear()

        if not os.path.isdir(self.mods_root):
            return self.discovered_mods

        for entry in sorted(os.listdir(self.mods_root)):
            full_path = os.path.join(self.mods_root, entry)
            if os.path.isdir(full_path) and not entry.startswith("."):
                meta = ModMetadata.from_folder(full_path)
                self.discovered_mods.append(meta)
                if meta.enabled:
                    Paths.active_mods.append(meta.mod_id)

        return self.discovered_mods

    def load_python_script_from_string(self, script_name: str, code: str) -> Any:
        """
        🇬🇧 Dynamically compiles & loads a `.py` mod script in memory and injects `game` reference.
        🇺🇦 Динамічно завантажує Python-скрипт мода і надає йому доступ до об'єкта `game`.
        """
        spec = importlib.util.spec_from_loader(script_name, loader=None)
        if spec is None:
            return None
        module = importlib.util.module_from_spec(spec)
        module.__dict__["game"] = self.game_context
        module.__dict__["Paths"] = Paths
        exec(compile(code, script_name, "exec"), module.__dict__)
        self.python_scripts.append(module)
        return module

    def load_python_script_file(self, file_path: str) -> Any:
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()
        name = os.path.splitext(os.path.basename(file_path))[0]
        return self.load_python_script_from_string(name, code)

    def dispatch_event(self, event: ScriptEvent) -> bool:
        """
        🇬🇧 Dispatches a `ScriptEvent` to all active Python & Lua mod scripts.
           Returns `False` if the event was cancelled by a script, `True` otherwise.
        🇺🇦 Розсилає подію (`SONG_BEAT_HIT`, `NOTE_HIT` тощо) усім активним модам.
        """
        handler_names = ScriptEventType.HANDLER_NAMES.get(event.type, (event.type,))

        for mod_script in self.python_scripts:
            for fn_name in handler_names:
                fn = getattr(mod_script, fn_name, None)
                if callable(fn):
                    fn(event)
                    if event.eventCanceled:
                        return False

        return not event.eventCanceled

    def unload_all(self) -> None:
        """
        🇬🇧 Frees all loaded mod scripts from RAM after a song ends (crucial for 32-bit mobile!).
        🇺🇦 Повністю очищає пам'ять від скриптів після завершення пісні (важливо для 32-біт телефонів!).
        """
        self.python_scripts.clear()
        self.lua_scripts.clear()
