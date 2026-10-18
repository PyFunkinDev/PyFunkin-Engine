"""
================================================================================
PyFunkin Engine (FNF Lite) — Asset Paths & Stage Data (`pyfunkin/paths.py`)
================================================================================
🇬🇧 EN: Clean, memory-optimized (`__slots__`) Python port of:
       - `source/funkin/Paths.hx` (Asset path resolver with Mod & `.webp` priority!)
       - `source/funkin/data/stage/StageData.hx` (Stage props, zIndex & character layout)
🇺🇦 UA: Менеджер шляхів та парсер сцен (`mainStage.json` тощо):
       - Шукає ресурси спочатку в активних модах (`mods/`), потім у поточному тижні,
         потім у `shared/` та `preload/`.
       - Автоматично підтримує стиснуті зображення `.webp` нарівні зі стандартними `.png`!
================================================================================
"""

from __future__ import annotations
import json
import os
from typing import Dict, List, Optional, Tuple, Any
from .core import Constants
from .atlas import AnimationDef


class Paths:
    """
    🇬🇧 Core class which handles determining asset paths (`source/funkin/Paths.hx`).
       Enhanced for FNF Lite to transparently resolve `.webp` compressed sprites and `mods/` overrides!
    🇺🇦 Відповідає за пошук шляхів до всіх файлів гри (музика, спрайти, чарти, шрифти, шейдери).
       Автоматично перевіряє папку `mods/` та підхоплює стиснуті `.webp` текстури!
    """
    assets_root: str = "assets"
    mods_root: str = "mods"
    current_level: Optional[str] = None
    active_mods: List[str] = []

    @classmethod
    def setCurrentLevel(cls, name: Optional[str]) -> None:
        cls.current_level = name.lower() if name is not None else None

    @staticmethod
    def stripLibrary(path: str) -> str:
        """🇬🇧 `'shared:characters/bf'` -> `'characters/bf'` / 🇺🇦 Відрізає назву бібліотеки до двокрапки."""
        parts = path.split(":", 1)
        return parts[1] if len(parts) == 2 else path

    @staticmethod
    def getLibrary(path: str) -> str:
        """🇬🇧 `'shared:characters/bf'` -> `'shared'` / 🇺🇦 Повертає назву бібліотеки до двокрапки."""
        parts = path.split(":", 1)
        return parts[0] if len(parts) == 2 else "preload"

    @classmethod
    def _resolve_candidates(cls, rel_path: str, library: Optional[str] = None) -> List[str]:
        """
        🇬🇧 Returns ordered list of candidate file paths on disk:
           1) Active mods (`mods/<mod>/<rel_path>`)
           2) Explicit library (`assets/<library>/<rel_path>`)
           3) Current level (`assets/<current_level>/<rel_path>`)
           4) Shared (`assets/shared/<rel_path>`)
           5) Preload (`assets/preload/<rel_path>` and `assets/<rel_path>`)
        🇺🇦 Формує список місць, де гра шукає файл (від модів до базової папки `preload`).
        """
        candidates: List[str] = []

        # 1. Check active mods first (Polymod-style override)
        for mod in cls.active_mods:
            candidates.append(os.path.join(cls.mods_root, mod, rel_path))
            if library:
                candidates.append(os.path.join(cls.mods_root, mod, library, rel_path))

        # 2. Check explicit library if provided
        if library and library not in ("preload", "default"):
            candidates.append(os.path.join(cls.assets_root, library, rel_path))

        # 3. Check current level (e.g. week1..week7, weekend1)
        if cls.current_level:
            candidates.append(os.path.join(cls.assets_root, cls.current_level, rel_path))

        # 4. Check shared & preload
        candidates.append(os.path.join(cls.assets_root, "shared", rel_path))
        candidates.append(os.path.join(cls.assets_root, "preload", rel_path))
        candidates.append(os.path.join(cls.assets_root, rel_path))
        return candidates

    @classmethod
    def getPath(cls, file_rel: str, library: Optional[str] = None) -> str:
        if ":" in file_rel and library is None:
            library = cls.getLibrary(file_rel)
            file_rel = cls.stripLibrary(file_rel)

        candidates = cls._resolve_candidates(file_rel, library)
        for path in candidates:
            if os.path.exists(path):
                return path
        # Return default logical path if file is not on disk yet
        lib_folder = library if (library and library not in ("preload", "default")) else "preload"
        return os.path.join(cls.assets_root, lib_folder, file_rel)

    @classmethod
    def image(cls, key: str, library: Optional[str] = None) -> str:
        """
        🇬🇧 Resolves an image path. Checks `.webp` first (for FNF Lite compressed packs) then `.png`!
        🇺🇦 Шукає картинку: спочатку перевіряє стиснутий `.webp`, а якщо немає — стандартний `.png`!
        """
        if ":" in key and library is None:
            library = cls.getLibrary(key)
            key = cls.stripLibrary(key)

        for ext in ("webp", Constants.EXT_IMAGE):
            for cand in cls._resolve_candidates(f"images/{key}.{ext}", library):
                if os.path.exists(cand):
                    return cand

        lib_folder = library if (library and library not in ("preload", "default")) else "preload"
        return os.path.join(cls.assets_root, lib_folder, f"images/{key}.{Constants.EXT_IMAGE}")

    @classmethod
    def json(cls, key: str, library: Optional[str] = None) -> str:
        return cls.getPath(f"data/{key}.{Constants.EXT_DATA}", library)

    @classmethod
    def txt(cls, key: str, library: Optional[str] = None) -> str:
        return cls.getPath(f"data/{key}.txt", library)

    @classmethod
    def xml(cls, key: str, library: Optional[str] = None) -> str:
        return cls.getPath(f"data/{key}.xml", library)

    @classmethod
    def sound(cls, key: str, library: Optional[str] = None) -> str:
        return cls.getPath(f"sounds/{key}.{Constants.EXT_SOUND}", library)

    @classmethod
    def music(cls, key: str, library: Optional[str] = None) -> str:
        return cls.getPath(f"music/{key}.{Constants.EXT_SOUND}", library)

    @classmethod
    def inst(cls, song: str, suffix: str = "", with_extension: bool = True) -> str:
        """
        🇬🇧 Gets path to `Inst.ogg` for a song (`songs/<song>/Inst<suffix>.ogg`).
        🇺🇦 Повертає шлях до інструменталу пісні (`Inst.ogg`).
        """
        ext = f".{Constants.EXT_SOUND}" if with_extension else ""
        rel = f"songs/{song.lower()}/Inst{suffix}{ext}"
        for mod in cls.active_mods:
            mod_cand = os.path.join(cls.mods_root, mod, rel)
            if os.path.exists(mod_cand):
                return mod_cand
        return os.path.join(cls.assets_root, rel)

    @classmethod
    def voices(cls, song: str, suffix: str = "") -> str:
        """
        🇬🇧 Gets path to `Voices.ogg` (or `Voices-bf.ogg` / `Voices-dad.ogg` when suffix='-bf').
        🇺🇦 Повертає шлях до вокальної доріжки пісні (`Voices.ogg`, `Voices-bf.ogg` тощо).
        """
        if suffix and not suffix.startswith("-"):
            suffix = f"-{suffix}"
        rel = f"songs/{song.lower()}/Voices{suffix}.{Constants.EXT_SOUND}"
        for mod in cls.active_mods:
            mod_cand = os.path.join(cls.mods_root, mod, rel)
            if os.path.exists(mod_cand):
                return mod_cand
        return os.path.join(cls.assets_root, rel)

    @classmethod
    def font(cls, key: str) -> str:
        return os.path.join(cls.assets_root, "fonts", key)


# ==============================================================================
# STAGE DATA PARSER (`source/funkin/data/stage/StageData.hx`)
# ==============================================================================

class StageDataProp:
    """
    🇬🇧 Single stage background/foreground prop (`StageDataProp` in `StageData.hx`).
       "Props with lower zIndex render below those with higher numbers. Just like CSS, it isn't hard." - FunkinCrew
    🇺🇦 Один об'єкт декорації на сцені (задній фон, підлога, штори, колонки тощо).
       Сортується за `zIndex` (шаром глибини) та підтримує паралакс-прокрутку `scroll`.
    """
    __slots__ = (
        "name",
        "assetPath",
        "position",
        "zIndex",
        "isPixel",
        "scale",
        "alpha",
        "danceEvery",
        "scroll",
        "animType",
        "animations",
        "flipX",
        "flipY",
    )

    def __init__(
        self,
        name: str = "",
        assetPath: str = "",
        position: Optional[List[float]] = None,
        zIndex: int = 0,
        isPixel: bool = False,
        scale: Tuple[float, float] = (1.0, 1.0),
        alpha: float = 1.0,
        danceEvery: float = 0.0,
        scroll: Optional[List[float]] = None,
        animType: str = "sparrow",
        animations: Optional[List[AnimationDef]] = None,
        flipX: bool = False,
        flipY: bool = False,
    ) -> None:
        self.name: str = name
        self.assetPath: str = assetPath
        self.position: List[float] = position if position is not None else [0.0, 0.0]
        self.zIndex: int = zIndex
        self.isPixel: bool = isPixel
        self.scale: Tuple[float, float] = scale
        self.alpha: float = alpha
        self.danceEvery: float = danceEvery
        self.scroll: List[float] = scroll if scroll is not None else [1.0, 1.0]
        self.animType: str = animType
        self.animations: List[AnimationDef] = animations if animations is not None else []
        self.flipX: bool = flipX
        self.flipY: bool = flipY

    @property
    def is_solid_color(self) -> bool:
        """
        🇬🇧 As of Stage data v1.0.1, `assetPath` can be a hex color like `'#ff0000'` to draw a rectangle!
        🇺🇦 Якщо `assetPath` починається з `'#'`, замість картинки малюється кольоровий прямокутник!
        """
        return self.assetPath.startswith("#")

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "StageDataProp":
        raw_scale = d.get("scale", 1.0)
        if isinstance(raw_scale, list) and len(raw_scale) >= 2:
            scale_tuple = (float(raw_scale[0]), float(raw_scale[1]))
        else:
            s = float(raw_scale) if not isinstance(raw_scale, list) else 1.0
            scale_tuple = (s, s)

        anims = [AnimationDef.from_dict(a) for a in d.get("animations", [])]
        return cls(
            name=str(d.get("name", "")),
            assetPath=str(d.get("assetPath", "")),
            position=[float(x) for x in d.get("position", [0.0, 0.0])],
            zIndex=int(d.get("zIndex", 0)),
            isPixel=bool(d.get("isPixel", False)),
            scale=scale_tuple,
            alpha=float(d.get("alpha", 1.0)),
            danceEvery=float(d.get("danceEvery", 0.0)),
            scroll=[float(x) for x in d.get("scroll", [1.0, 1.0])],
            animType=str(d.get("animType", "sparrow")),
            animations=anims,
            flipX=bool(d.get("flipX", False)),
            flipY=bool(d.get("flipY", False)),
        )


class StageDataCharacter:
    """
    🇬🇧 Placement and camera offset settings for `bf`, `dad`, or `gf` on a stage (`StageData.hx`).
    🇺🇦 Позиція, глибина (`zIndex`), масштаб та зміщення камери для персонажа на сцені.
    """
    __slots__ = ("role", "zIndex", "position", "scale", "cameraOffsets", "scroll", "alpha")

    def __init__(
        self,
        role: str,
        zIndex: int = 0,
        position: Optional[List[float]] = None,
        scale: float = 1.0,
        cameraOffsets: Optional[List[float]] = None,
        scroll: Optional[List[float]] = None,
        alpha: float = 1.0,
    ) -> None:
        self.role: str = role
        self.zIndex: int = zIndex
        self.position: List[float] = position if position is not None else [0.0, 0.0]
        self.scale: float = scale
        self.cameraOffsets: List[float] = cameraOffsets if cameraOffsets is not None else [0.0, 0.0]
        self.scroll: List[float] = scroll if scroll is not None else [1.0, 1.0]
        self.alpha: float = alpha

    @classmethod
    def from_dict(cls, role: str, d: Dict[str, Any]) -> "StageDataCharacter":
        return cls(
            role=role,
            zIndex=int(d.get("zIndex", 0)),
            position=[float(x) for x in d.get("position", [0.0, 0.0])],
            scale=float(d.get("scale", 1.0)),
            cameraOffsets=[float(x) for x in d.get("cameraOffsets", [0.0, 0.0])],
            scroll=[float(x) for x in d.get("scroll", [1.0, 1.0])],
            alpha=float(d.get("alpha", 1.0)),
        )


class StageData:
    """
    🇬🇧 Full stage definition loaded from `preload/data/stages/*.json` (`StageData.hx`).
    🇺🇦 Повний опис сцени (декорації, позиції персонажів, базовий зум камери).
    """
    __slots__ = ("stageId", "version", "name", "directory", "cameraZoom", "props", "characters")

    def __init__(
        self,
        stageId: str,
        version: str = "1.0.0",
        name: str = "Unknown",
        directory: str = "shared",
        cameraZoom: float = 1.0,
        props: Optional[List[StageDataProp]] = None,
        characters: Optional[Dict[str, StageDataCharacter]] = None,
    ) -> None:
        self.stageId: str = stageId
        self.version: str = version
        self.name: str = name
        self.directory: str = directory
        self.cameraZoom: float = cameraZoom
        self.props: List[StageDataProp] = props if props is not None else []
        self.characters: Dict[str, StageDataCharacter] = characters if characters is not None else {}

    def get_render_order(self) -> List[Any]:
        """
        🇬🇧 Returns all props and characters sorted ascending by `zIndex` for correct layering!
        🇺🇦 Повертає всі декорації та персонажів, відсортованих за `zIndex` (від заднього плану до переднього).
        """
        items: List[Any] = list(self.props) + list(self.characters.values())
        return sorted(items, key=lambda obj: obj.zIndex)

    @classmethod
    def from_json(cls, stageId: str, raw_json: str) -> "StageData":
        d = json.loads(raw_json.lstrip("\ufeff").strip())
        props = [StageDataProp.from_dict(p) for p in d.get("props", [])]
        chars_raw = d.get("characters", {})
        characters: Dict[str, StageDataCharacter] = {}
        for role in ("bf", "dad", "gf"):
            if role in chars_raw:
                characters[role] = StageDataCharacter.from_dict(role, chars_raw[role])
        return cls(
            stageId=stageId,
            version=str(d.get("version", "1.0.0")),
            name=str(d.get("name", stageId)),
            directory=str(d.get("directory", "shared")),
            cameraZoom=float(d.get("cameraZoom", 1.0)),
            props=props,
            characters=characters,
        )
