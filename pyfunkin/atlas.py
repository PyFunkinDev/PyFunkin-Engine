"""
================================================================================
PyFunkin Engine (FNF Lite) — Universal Atlas & Character Parser (`pyfunkin/atlas.py`)
================================================================================
🇬🇧 EN: Clean, memory-optimized (`__slots__`) Python port of:
       - `source/funkin/data/character/CharacterData.hx`
       - `flixel.graphics.frames.FlxAtlasFrames` (Sparrow `.xml` & Packer `.txt`)
       - `flxanimate` (`spritemap1.json` + `Animation.json` Texture Atlas)
🇺🇦 UA: Універсальний завантажувач персонажів та всіх 3 форматів анімацій FNF:
       1) Sparrow Atlas (`.png` + `.xml`) — класичні персонажі (Dad, Pico, GF)
       2) Packer Atlas (`.png` + `.txt`) — піксельні персонажі (`spirit.txt`)
       3) Animate Texture Atlas (`spritemap1.json` + `Animation.json`) — нові компактні анімації (`abotSystem`, `bf`)
================================================================================
"""

from __future__ import annotations
import json
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Tuple, Any


class CharacterRenderType:
    """
    🇬🇧 Describes the available rendering types for a character (`CharacterData.hx`).
    🇺🇦 Типи рендерингу персонажів у FNF (визначають, як читати спрайти).
    """
    SPARROW: str = "sparrow"                    # .png + .xml
    PACKER: str = "packer"                      # .png + .txt (e.g. spirit.txt)
    MULTI_SPARROW: str = "multisparrow"         # Multiple .png + .xml
    ANIMATE_ATLAS: str = "animateatlas"         # spritemap1.png + spritemap1.json + Animation.json
    MULTI_ANIMATE_ATLAS: str = "multianimateatlas"
    CUSTOM: str = "custom"


class AtlasFrame:
    """
    🇬🇧 Single frame region on a spritesheet. Uses `__slots__` for minimal RAM footprint on 32-bit Android.
    🇺🇦 Один кадр на спрайт-листі. Використовує `__slots__` для мінімального споживання RAM на 32-бітних телефонах.
    """
    __slots__ = ("name", "x", "y", "width", "height", "frameX", "frameY", "frameWidth", "frameHeight", "rotated")

    def __init__(
        self,
        name: str,
        x: int,
        y: int,
        width: int,
        height: int,
        frameX: int = 0,
        frameY: int = 0,
        frameWidth: int = 0,
        frameHeight: int = 0,
        rotated: bool = False,
    ) -> None:
        self.name: str = name
        self.x: int = x
        self.y: int = y
        self.width: int = width
        self.height: int = height
        self.frameX: int = frameX
        self.frameY: int = frameY
        self.frameWidth: int = frameWidth if frameWidth > 0 else width
        self.frameHeight: int = frameHeight if frameHeight > 0 else height
        self.rotated: bool = rotated

    def __repr__(self) -> str:
        return f"AtlasFrame({self.name!r}, rect=({self.x}, {self.y}, {self.width}, {self.height}))"


class AnimationDef:
    """
    🇬🇧 Animation definition inside a character or prop JSON (`AnimationData.hx`).
    🇺🇦 Налаштування однієї анімації персонажа (наприклад, `idle`, `singLEFT`, `singUP`).
    """
    __slots__ = ("name", "prefix", "frameRate", "looped", "offsets", "flipX", "flipY", "frameIndices", "assetPath")

    def __init__(
        self,
        name: str,
        prefix: str = "",
        frameRate: int = 24,
        looped: bool = False,
        offsets: Optional[List[float]] = None,
        flipX: bool = False,
        flipY: bool = False,
        frameIndices: Optional[List[int]] = None,
        assetPath: Optional[str] = None,
    ) -> None:
        self.name: str = name
        self.prefix: str = prefix
        self.frameRate: int = frameRate
        self.looped: bool = looped
        self.offsets: List[float] = offsets if offsets is not None else [0.0, 0.0]
        self.flipX: bool = flipX
        self.flipY: bool = flipY
        self.frameIndices: List[int] = frameIndices if frameIndices is not None else []
        self.assetPath: Optional[str] = assetPath

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "AnimationDef":
        return cls(
            name=str(d.get("name", "")),
            prefix=str(d.get("prefix", "")),
            frameRate=int(d.get("frameRate") or 24),
            looped=bool(d.get("looped", False)),
            offsets=[float(x) for x in d.get("offsets", [0.0, 0.0])],
            flipX=bool(d.get("flipX", False)),
            flipY=bool(d.get("flipY", False)),
            frameIndices=[int(i) for i in d.get("frameIndices", [])],
            assetPath=d.get("assetPath"),
        )


class CharacterData:
    """
    🇬🇧 The JSON data schema used to define a character (`source/funkin/data/character/CharacterData.hx`).
       Pro tip from FunkinCrew: On pixel-art levels, save sprites small and set `scale` to 6 to save memory!
    🇺🇦 Паспорт персонажа з файлу `preload/data/characters/*.json`.
       Порада від розробників FNF: на піксельних рівнях зберігайте спрайти маленькими і ставте `scale = 6` для економії RAM!
    """
    __slots__ = (
        "charId",
        "version",
        "name",
        "renderType",
        "assetPath",
        "scale",
        "offsets",
        "cameraOffsets",
        "isPixel",
        "danceEvery",
        "singTime",
        "startingAnimation",
        "flipX",
        "animations",
    )

    DEFAULT_SINGTIME: float = 8.0
    DEFAULT_DANCEEVERY: float = 1.0
    DEFAULT_FRAMERATE: int = 24
    DEFAULT_SCALE: float = 1.0

    def __init__(
        self,
        charId: str,
        version: str = "1.0.2",
        name: str = "Untitled Character",
        renderType: str = CharacterRenderType.SPARROW,
        assetPath: str = "",
        scale: float = 1.0,
        offsets: Optional[List[float]] = None,
        cameraOffsets: Optional[List[float]] = None,
        isPixel: bool = False,
        danceEvery: float = 1.0,
        singTime: float = 8.0,
        startingAnimation: str = "idle",
        flipX: bool = False,
        animations: Optional[List[AnimationDef]] = None,
    ) -> None:
        self.charId: str = charId
        self.version: str = version
        self.name: str = name
        self.renderType: str = renderType
        self.assetPath: str = assetPath
        self.scale: float = scale
        self.offsets: List[float] = offsets if offsets is not None else [0.0, 0.0]
        self.cameraOffsets: List[float] = cameraOffsets if cameraOffsets is not None else [0.0, 0.0]
        self.isPixel: bool = isPixel
        self.danceEvery: float = danceEvery
        self.singTime: float = singTime
        self.startingAnimation: str = startingAnimation
        # 🇬🇧 "Whether or not the whole ass sprite is flipped by default. Useful for Pico." - FunkinCrew
        # 🇺🇦 «Чи віддзеркалений спрайт за замовчуванням. Корисно для грабельного Піко.» - FunkinCrew
        self.flipX: bool = flipX
        self.animations: List[AnimationDef] = animations if animations is not None else []

    @classmethod
    def from_json(cls, charId: str, raw_json: str) -> "CharacterData":
        # 🇬🇧 Clean trailing garbage characters just like `loadCharacterFile()` in CharacterData.hx
        # 🇺🇦 Очищаємо зайві символи в кінці файлу точно як у `loadCharacterFile()` в оригіналі
        cleaned = raw_json.strip()
        while cleaned and not cleaned.endswith("}"):
            cleaned = cleaned[:-1]

        d = json.loads(cleaned)
        anims = [AnimationDef.from_dict(a) for a in d.get("animations", [])]
        return cls(
            charId=charId,
            version=str(d.get("version", "1.0.2")),
            name=str(d.get("name", "Untitled Character")),
            renderType=str(d.get("renderType", CharacterRenderType.SPARROW)),
            assetPath=str(d.get("assetPath", "")),
            scale=float(d.get("scale", cls.DEFAULT_SCALE)),
            offsets=[float(x) for x in d.get("offsets", [0.0, 0.0])],
            cameraOffsets=[float(x) for x in d.get("cameraOffsets", [0.0, 0.0])],
            isPixel=bool(d.get("isPixel", False)),
            danceEvery=float(d.get("danceEvery", cls.DEFAULT_DANCEEVERY)),
            singTime=float(d.get("singTime", cls.DEFAULT_SINGTIME)),
            startingAnimation=str(d.get("startingAnimation", "idle")),
            flipX=bool(d.get("flipX", False)),
            animations=anims,
        )


# ==============================================================================
# 3 UNIVERSAL ATLAS PARSERS (`.xml`, `.txt`, `spritemap1.json` + `Animation.json`)
# ==============================================================================

def parse_sparrow_xml(xml_text: str) -> List[AtlasFrame]:
    """
    🇬🇧 Format #1: Sparrow v2 XML Atlas (`.png` + `.xml` exported from Adobe Animate).
    🇺🇦 Формат №1: Класичний Sparrow XML атлас (`.png` + `.xml` із Adobe Animate).
    """
    root = ET.fromstring(xml_text.strip())
    frames: List[AtlasFrame] = []
    for sub in root.findall("SubTexture"):
        attr = sub.attrib
        frames.append(
            AtlasFrame(
                name=attr["name"],
                x=int(attr["x"]),
                y=int(attr["y"]),
                width=int(attr["width"]),
                height=int(attr["height"]),
                frameX=int(attr.get("frameX", 0)),
                frameY=int(attr.get("frameY", 0)),
                frameWidth=int(attr.get("frameWidth", attr["width"])),
                frameHeight=int(attr.get("frameHeight", attr["height"])),
                rotated=(attr.get("rotated", "false").lower() == "true"),
            )
        )
    return frames


def parse_packer_txt(txt_text: str) -> List[AtlasFrame]:
    """
    🇬🇧 Format #2: SpriteSheet Packer TXT Atlas (`.png` + `.txt`, used by `spirit.txt` in Week 6!).
       Line format: `idle spirit_0 = 0 1028 128 128`
    🇺🇦 Формат №2: Текстовий атлас Packer (`.png` + `.txt`, використовується Духом `spirit.txt` у 6 тижні!).
       Формат рядка: `назва_кадру = X Y Ширина Висота`
    """
    frames: List[AtlasFrame] = []
    for line in txt_text.splitlines():
        line = line.strip()
        if not line or "=" not in line:
            continue
        name_part, coords_part = line.split("=", 1)
        x, y, w, h = (int(v) for v in coords_part.split())
        frames.append(AtlasFrame(name=name_part.strip(), x=x, y=y, width=w, height=h))
    return frames


def parse_animate_atlas(spritemap_json: str, animation_json: str) -> Tuple[List[AtlasFrame], Dict[str, Any]]:
    """
    🇬🇧 Format #3: Adobe Animate Texture Atlas (`spritemap1.json` + `Animation.json`, e.g., `abotSystem`, `bf`).
       Stores small reusable limb/part sprites (`SubTexture` in `ATLAS.SPRITES`) and matrix timelines (`Animation.json`).
    🇺🇦 Формат №3: Найкомпактніший формат Texture Atlas (`spritemap1.json` + `Animation.json`, як у `abotSystem` та `bf`).
       Зберігає окремі детальки персонажа на маленькій картинці та збирає їх у русі як конструктор LEGO!
    """
    # Remove UTF-8 BOM if present (Adobe Animate often exports JSON with \ufeff BOM!)
    s_data = json.loads(spritemap_json.lstrip("\ufeff").strip())
    a_data = json.loads(animation_json.lstrip("\ufeff").strip())

    sprites_raw = s_data.get("ATLAS", {}).get("SPRITES", [])
    sprites: List[AtlasFrame] = []
    for item in sprites_raw:
        sp = item.get("SPRITE", item)
        sprites.append(
            AtlasFrame(
                name=str(sp["name"]),
                x=int(sp["x"]),
                y=int(sp["y"]),
                width=int(sp["w"]),
                height=int(sp["h"]),
                rotated=bool(sp.get("rotated", False)),
            )
        )

    # Extract symbol names and timeline info from Animation.json
    symbols_dict = a_data.get("SD", {}).get("S", []) if "SD" in a_data else a_data.get("SYMBOL_DICTIONARY", {}).get("Symbols", [])
    symbol_names = [s.get("SN") or s.get("SYMBOL_name", "") for s in symbols_dict]
    anim_name = a_data.get("AN", {}).get("N") or a_data.get("ANIMATION", {}).get("SYMBOL_name", "Main")
    framerate = a_data.get("MD", {}).get("FRT") or a_data.get("metadata", {}).get("framerate", 24)

    summary = {
        "animation_name": anim_name,
        "framerate": framerate,
        "total_unique_parts": len(sprites),
        "total_symbols": len(symbol_names),
        "sample_symbols": symbol_names[:8],
    }
    return sprites, summary
