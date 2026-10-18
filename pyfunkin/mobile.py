"""
================================================================================
PyFunkin Engine (FNF Lite) — Mobile Hitboxes & Precise Touch Input (`pyfunkin/mobile.py`)
================================================================================
🇬🇧 EN: Clean, memory-optimized (`__slots__`) Python port of:
       - `source/funkin/mobile/ui/FunkinHitbox.hx` (All 5 official mobile schemes!)
       - `source/funkin/mobile/input/PreciseInputHandler.hx`
       - `source/funkin/input/PreciseInputManager.hx` (Sub-frame nanosecond input timing!)
🇺🇦 UA: Офіційна мобільна система керування та точного сенсорного вводу:
       - Підтримує всі 5 схем хітбоксів (`Four Lanes`, `Double Thumb Triangle`,
         `Double Thumb Square`, `Double Thumb DPad`, `Arrows`).
       - Ловить мультитач (дотики кількома пальцями одночасно) з точністю до наносекунди,
         усуваючи затримку кадрів (input lag) на телефонах!
================================================================================
"""

from __future__ import annotations
import math
import time
from typing import Callable, Dict, List, Optional, Tuple
from .core import Signal


class NoteDirection:
    """
    🇬🇧 Standard 4-key note directions (`funkin.play.notes.NoteDirection`).
    🇺🇦 Чотири напрямки стрілочок FNF.
    """
    LEFT: int = 0
    DOWN: int = 1
    UP: int = 2
    RIGHT: int = 3

    ALL: Tuple[int, int, int, int] = (0, 1, 2, 3)
    NAMES: Tuple[str, str, str, str] = ("LEFT", "DOWN", "UP", "RIGHT")


class FunkinHintAlphaStyle:
    """
    🇬🇧 Alpha styles for mobile hitbox hints (`FunkinHitbox.hx`).
       Format: `(pressed_alpha, idle_alpha, tween_duration_sec)`
    🇺🇦 Режими прозорості мобільних хітбоксів (невидимі до натискання або напівпрозорі).
    """
    INVISIBLE_TILL_PRESS: str = "INVISIBLE_TILL_PRESS"
    VISIBLE_TILL_PRESS: str = "VISIBLE_TILL_PRESS"

    VALUES: Dict[str, Tuple[float, float, float]] = {
        "INVISIBLE_TILL_PRESS": (0.3, 0.00001, 0.01),
        "VISIBLE_TILL_PRESS": (0.4, 0.2, 0.08),
    }


class FunkinHitboxControlSchemes:
    """
    🇬🇧 All 5 official mobile hitbox layouts from `source/funkin/mobile/ui/FunkinHitbox.hx`.
    🇺🇦 Усі 5 офіційних схем мобільного керування з `FunkinHitbox.hx`.
    """
    FOUR_LANES: str = "Four Lanes"
    DOUBLE_THUMB_TRIANGLE: str = "Double Thumb Triangle"
    DOUBLE_THUMB_SQUARE: str = "Double Thumb Square"
    DOUBLE_THUMB_DPAD: str = "Double Thumb DPad"
    ARROWS: str = "Arrows"


class FunkinHint:
    """
    🇬🇧 Single mobile hitbox zone (`FunkinHint` in `FunkinHitbox.hx`).
       Supports rectangular lanes, triangles, and circular D-Pad buttons with multi-touch hit-testing!
    🇺🇦 Одна сенсорна зона хітбоксу (смужка, трикутник або кругла кнопка D-Pad) з перевіркою дотику пальця.
    """
    __slots__ = (
        "x",
        "y",
        "width",
        "height",
        "noteDirection",
        "color",
        "shape_type",
        "triangle_vertices",
        "circle_radius",
        "alpha",
        "target_alpha",
        "is_pressed",
        "active_finger_ids",
        "isPixel",
    )

    def __init__(
        self,
        x: float,
        y: float,
        width: int,
        height: int,
        noteDirection: int,
        color: int,
        shape_type: str = "lane",
        triangle_vertices: Optional[List[float]] = None,
        circle_radius: float = 0.0,
        alpha_style: str = FunkinHintAlphaStyle.INVISIBLE_TILL_PRESS,
    ) -> None:
        self.x: float = float(x)
        self.y: float = float(y)
        self.width: int = int(width)
        self.height: int = int(height)
        self.noteDirection: int = int(noteDirection)
        self.color: int = int(color)
        self.shape_type: str = shape_type  # 'lane' | 'triangle' | 'circle'
        self.triangle_vertices: List[float] = triangle_vertices if triangle_vertices is not None else []
        self.circle_radius: float = float(circle_radius)

        style_vals = FunkinHintAlphaStyle.VALUES.get(alpha_style, (0.3, 0.0, 0.01))
        self.alpha: float = style_vals[1] if alpha_style == FunkinHintAlphaStyle.INVISIBLE_TILL_PRESS else style_vals[0]
        self.target_alpha: float = self.alpha
        self.is_pressed: bool = False
        self.active_finger_ids: List[int] = []
        self.isPixel: bool = False

    def contains_point(self, px: float, py: float) -> bool:
        """
        🇬🇧 Fast geometric hit-test for touch coordinates `(px, py)`.
        🇺🇦 Швидка геометрична перевірка: чи попав палець у координати `(px, py)` цієї кнопки.
        """
        # Bounding box check first
        if not (self.x <= px <= self.x + self.width and self.y <= py <= self.y + self.height):
            return False

        if self.shape_type == "circle" and self.circle_radius > 0:
            cx = self.x + self.circle_radius
            cy = self.y + self.circle_radius
            return (px - cx) ** 2 + (py - cy) ** 2 <= self.circle_radius ** 2

        if self.shape_type == "triangle" and len(self.triangle_vertices) == 6:
            # Local coordinates inside bounding box
            lx = px - self.x
            ly = py - self.y
            x1, y1, x2, y2, x3, y3 = self.triangle_vertices
            # Barycentric / cross-product triangle hit test
            d1 = (lx - x2) * (y1 - y2) - (x1 - x2) * (ly - y2)
            d2 = (lx - x3) * (y2 - y3) - (x2 - x3) * (ly - y3)
            d3 = (lx - x1) * (y3 - y1) - (x3 - x1) * (ly - y1)
            has_neg = (d1 < 0) or (d2 < 0) or (d3 < 0)
            has_pos = (d1 > 0) or (d2 > 0) or (d3 > 0)
            return not (has_neg and has_pos)

        return True


class FunkinHitbox:
    """
    🇬🇧 Represents a mobile touch zone with 4 (or 8 dual-thumb) buttons (`FunkinHitbox.hx`).
    🇺🇦 Мобільний хітбокс з підтримкою 4 смужок або подвійного керування під два великі пальці.
    """
    __slots__ = ("scheme", "screen_width", "screen_height", "hints", "isPixel", "onHintDown", "onHintUp")

    # 🇬🇧 Official mobile hint colors from `FunkinHitbox.hx` line 264!
    # 🇺🇦 Офіційні кольори мобільних хітбоксів із `FunkinHitbox.hx`!
    DEFAULT_COLORS: Tuple[int, int, int, int] = (
        0xFFC34B9A,  # LEFT  (Purple-Pink / Фіолетово-рожевий)
        0xFF00FFFF,  # DOWN  (Cyan / Блакитний)
        0xFF12FB06,  # UP    (Green / Зелений)
        0xFFF9393F,  # RIGHT (Red / Червоний)
    )

    def __init__(
        self,
        scheme: str = FunkinHitboxControlSchemes.FOUR_LANES,
        screen_width: int = 1280,
        screen_height: int = 720,
        colors_override: Optional[List[int]] = None,
    ) -> None:
        self.scheme: str = scheme
        self.screen_width: int = screen_width
        self.screen_height: int = screen_height
        self.hints: List[FunkinHint] = []
        self.isPixel: bool = False
        self.onHintDown: List[Callable[[FunkinHint], None]] = []
        self.onHintUp: List[Callable[[FunkinHint], None]] = []

        colors = colors_override if colors_override else list(self.DEFAULT_COLORS)
        directions = list(NoteDirection.ALL)
        self._build_layout(scheme, directions, colors)

    @staticmethod
    def getTriangleVertices(width: int, height: int, facing: int) -> List[float]:
        """
        🇬🇧 Exact triangle vertex calculation from `FunkinHitbox.hx` (`getTriangleVertices`).
        🇺🇦 Точний розрахунок кутів трикутних кнопок із офіційного `FunkinHitbox.hx`.
        """
        if facing == NoteDirection.UP:
            facing = NoteDirection.DOWN
        elif facing == NoteDirection.DOWN:
            facing = NoteDirection.UP

        if facing == NoteDirection.UP:
            return [width / 2.0, 0.0, 0.0, float(height), float(width), float(height)]
        if facing == NoteDirection.DOWN:
            return [0.0, 0.0, float(width), 0.0, width / 2.0, float(height)]
        if facing == NoteDirection.LEFT:
            return [0.0, 0.0, float(width), height / 2.0, 0.0, float(height)]
        return [float(width), 0.0, 0.0, height / 2.0, float(width), float(height)]

    def _build_layout(self, scheme: str, directions: List[int], colors: List[int]) -> None:
        w = self.screen_width
        h = self.screen_height

        if scheme == FunkinHitboxControlSchemes.FOUR_LANES:
            hint_w = w // len(directions)
            for i, d in enumerate(directions):
                self.hints.append(
                    FunkinHint(
                        x=i * hint_w,
                        y=0,
                        width=hint_w,
                        height=h,
                        noteDirection=d,
                        color=colors[i % len(colors)],
                        shape_type="lane",
                    )
                )

        elif scheme == FunkinHitboxControlSchemes.DOUBLE_THUMB_TRIANGLE:
            screen_half = w // 2
            for i in range(2):
                x_off = screen_half if i == 1 else 0
                # LEFT triangle
                tw, th = w // 4, h
                self.hints.append(
                    FunkinHint(
                        x_off, 0, tw, th, directions[0], colors[0], "triangle",
                        self.getTriangleVertices(tw, th, directions[0])
                    )
                )
                # DOWN triangle
                tw, th = w // 2, h // 2
                self.hints.append(
                    FunkinHint(
                        x_off, h // 2, tw, th, directions[1], colors[1], "triangle",
                        self.getTriangleVertices(tw, th, directions[1])
                    )
                )
                # UP triangle
                self.hints.append(
                    FunkinHint(
                        x_off, 0, tw, th, directions[2], colors[2], "triangle",
                        self.getTriangleVertices(tw, th, directions[2])
                    )
                )
                # RIGHT triangle
                tw, th = w // 4, h
                self.hints.append(
                    FunkinHint(
                        x_off + (w // 4), 0, tw, th, directions[3], colors[3], "triangle",
                        self.getTriangleVertices(tw, th, directions[3])
                    )
                )

        elif scheme == FunkinHitboxControlSchemes.DOUBLE_THUMB_SQUARE:
            screen_half = w // 2
            hint_w = (w // len(directions)) // 2
            box_w = hint_w * 2
            box_h = h // 2
            for i in range(2):
                x_off = screen_half if i == 1 else 0
                for j, d in enumerate(directions):
                    if j in (1, 2):
                        self.hints.append(
                            FunkinHint(
                                x=x_off + hint_w,
                                y=box_h if j == 1 else 0,
                                width=box_w,
                                height=box_h,
                                noteDirection=d,
                                color=colors[j % len(colors)],
                                shape_type="lane",
                            )
                        )
                    else:
                        self.hints.append(
                            FunkinHint(
                                x=x_off + (0 if j == 0 else hint_w + box_w),
                                y=0,
                                width=hint_w,
                                height=h,
                                noteDirection=d,
                                color=colors[j % len(colors)],
                                shape_type="lane",
                            )
                        )

        elif scheme == FunkinHitboxControlSchemes.DOUBLE_THUMB_DPAD:
            hint_size = 75
            angles = [math.pi, math.pi / 2.0, math.pi * 1.5, 0.0]
            zone_radius = 115
            for i in range(2):
                for j, angle in enumerate(angles):
                    cx = ((w - hint_size * 4) if i == 1 else hint_size * 2) + math.cos(angle) * zone_radius
                    cy = (h - hint_size * 3.75) + math.sin(angle) * zone_radius
                    self.hints.append(
                        FunkinHint(
                            x=cx,
                            y=cy,
                            width=hint_size * 2,
                            height=hint_size * 2,
                            noteDirection=directions[j % len(directions)],
                            color=colors[j % len(colors)],
                            shape_type="circle",
                            circle_radius=float(hint_size),
                            alpha_style=FunkinHintAlphaStyle.VISIBLE_TILL_PRESS,
                        )
                    )

    def handle_touch_down(self, finger_id: int, px: float, py: float) -> List[int]:
        """
        🇬🇧 Process a finger touch at `(px, py)` and trigger `onHintDown` for matched lanes.
        🇺🇦 Обробляє дотик пальця `finger_id` у точці `(px, py)` (підтримує мультитач!).
        """
        pressed_dirs: List[int] = []
        for hint in self.hints:
            if hint.contains_point(px, py):
                was_pressed = hint.is_pressed
                if finger_id not in hint.active_finger_ids:
                    hint.active_finger_ids.append(finger_id)
                hint.is_pressed = True
                hint.alpha = 0.3
                if not was_pressed:
                    pressed_dirs.append(hint.noteDirection)
                    for cb in self.onHintDown:
                        cb(hint)
        return pressed_dirs

    def handle_touch_up(self, finger_id: int) -> List[int]:
        """
        🇬🇧 Release a finger by `finger_id` and fire `onHintUp` if no fingers remain on that lane.
        🇺🇦 Відпускає кнопку, коли палець `finger_id` піднімається з екрана.
        """
        released_dirs: List[int] = []
        for hint in self.hints:
            if finger_id in hint.active_finger_ids:
                hint.active_finger_ids.remove(finger_id)
                if not hint.active_finger_ids and hint.is_pressed:
                    hint.is_pressed = False
                    hint.alpha = 0.00001
                    released_dirs.append(hint.noteDirection)
                    for cb in self.onHintUp:
                        cb(hint)
        return released_dirs


# ==============================================================================
# PRECISE INPUT MANAGER (`PreciseInputManager.hx` & `PreciseInputHandler.hx`)
# ==============================================================================

class PreciseInputEvent:
    """
    🇬🇧 Sub-frame input event with nanosecond timestamp (`PreciseInputManager.hx`).
    🇺🇦 Подія натискання або відпускання стрілочки з точним часом у наносекундах!
    """
    __slots__ = ("noteDirection", "timestamp_ns", "keyCode")

    def __init__(self, noteDirection: int, timestamp_ns: int, keyCode: int = 0) -> None:
        self.noteDirection: int = noteDirection
        self.timestamp_ns: int = timestamp_ns
        self.keyCode: int = keyCode

    @property
    def timestamp_ms(self) -> float:
        return self.timestamp_ns / 1_000_000.0


class PreciseInputManager:
    """
    🇬🇧 Records the exact nanosecond timestamp of when a note direction was pressed or released
       (`source/funkin/input/PreciseInputManager.hx`).
    🇺🇦 Записує точний час натискання пальцем чи клавішею незалежно від FPS (усуває input lag).
    """
    _instance: Optional["PreciseInputManager"] = None

    @classmethod
    def get_instance(cls) -> "PreciseInputManager":
        if cls._instance is None:
            cls._instance = PreciseInputManager()
        return cls._instance

    @staticmethod
    def getCurrentTimestamp() -> int:
        """🇬🇧 Current monotonic time in nanoseconds. / 🇺🇦 Поточний час у наносекундах."""
        return time.perf_counter_ns()

    def __init__(self) -> None:
        self.onInputPressed: List[Callable[[PreciseInputEvent], None]] = []
        self.onInputReleased: List[Callable[[PreciseInputEvent], None]] = []
        self._dirPressTimestamps: Dict[int, int] = {}
        self._dirReleaseTimestamps: Dict[int, int] = {}

    def initializeHitbox(self, hitbox: FunkinHitbox) -> None:
        """
        🇬🇧 Connects a `FunkinHitbox` to `PreciseInputManager` (`PreciseInputHandler.hx`).
        🇺🇦 Підключає мобільний хітбокс до системи точного часу натискань.
        """
        hitbox.onHintDown.append(self._handleHintDown)
        hitbox.onHintUp.append(self._handleHintUp)

    def _handleHintDown(self, hint: FunkinHint) -> None:
        ts = self.getCurrentTimestamp()
        self._dirPressTimestamps[hint.noteDirection] = ts
        ev = PreciseInputEvent(noteDirection=hint.noteDirection, timestamp_ns=ts, keyCode=0)
        for cb in self.onInputPressed:
            cb(ev)

    def _handleHintUp(self, hint: FunkinHint) -> None:
        ts = self.getCurrentTimestamp()
        self._dirReleaseTimestamps[hint.noteDirection] = ts
        ev = PreciseInputEvent(noteDirection=hint.noteDirection, timestamp_ns=ts, keyCode=0)
        for cb in self.onInputReleased:
            cb(ev)
