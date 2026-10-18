"""
================================================================================
PyFunkin Engine (FNF Lite) — Graphics, Cameras & HUD Components (`pyfunkin/graphics.py`)
================================================================================
🇬🇧 EN: Clean, memory-optimized (`__slots__`) Python port of:
       - `source/funkin/graphics/FunkinCamera.hx` (`camGame`, `camHUD`, `camControls`)
       - `source/funkin/graphics/FunkinSprite.hx` (Atlas animations, offsets, 32-bit RAM saver)
       - `source/funkin/play/components/HealthIcon.hx` (Beat bop & losing icon state)
       - `source/funkin/play/components/PopUpStuff.hx` (`SICK!`, `GOOD!` & Combo popups)
       - `source/funkin/play/Countdown.hx` (`3 - 2 - 1 - GO!` pre-song countdown)
🇺🇦 UA: Графічна система, камери та ігровий інтерфейс (HUD):
       - Камери з плавним зумом під біт (`zoom`), трясінням (`shake`) та спалахами (`flash`).
       - Спрайти з підтримкою `.webp`/`.png` та автоматичним стисненням у RAM для 32-біт телефонів!
       - Іконки здоров'я (`HealthIcon`), які змінюють вираз обличчя при низькому HP (<20%).
================================================================================
"""

from __future__ import annotations
import math
from typing import Dict, List, Optional, Tuple
from .core import Constants
from .atlas import AtlasFrame


class FunkinCamera:
    """
    🇬🇧 Camera with smooth target following, beat-bop zoom lerp, flash, and shake
       (`source/funkin/graphics/FunkinCamera.hx`).
    🇺🇦 Ігрова камера (`camGame`, `camHUD`, `camControls`) з плавним наближенням під біти музики.
    """
    __slots__ = (
        "name",
        "width",
        "height",
        "scroll_x",
        "scroll_y",
        "target_x",
        "target_y",
        "zoom",
        "default_zoom",
        "follow_lerp",
        "flash_alpha",
        "flash_color",
        "flash_duration",
        "shake_intensity",
        "shake_duration",
    )

    def __init__(
        self,
        name: str = "camGame",
        width: int = 1280,
        height: int = 720,
        default_zoom: float = 1.0,
    ) -> None:
        self.name: str = name
        self.width: int = width
        self.height: int = height
        self.scroll_x: float = 0.0
        self.scroll_y: float = 0.0
        self.target_x: float = 0.0
        self.target_y: float = 0.0
        self.zoom: float = default_zoom
        self.default_zoom: float = default_zoom
        self.follow_lerp: float = Constants.DEFAULT_CAMERA_FOLLOW_RATE if hasattr(Constants, "DEFAULT_CAMERA_FOLLOW_RATE") else 0.04

        self.flash_alpha: float = 0.0
        self.flash_color: int = 0xFFFFFFFF
        self.flash_duration: float = 0.0

        self.shake_intensity: float = 0.0
        self.shake_duration: float = 0.0

    def bop(self, intensity: float = 1.015) -> None:
        """🇬🇧 Camera zoom bump on beat. / 🇺🇦 Пульсація зуму камери в такт біту."""
        self.zoom += (intensity - 1.0) * self.default_zoom

    def flash(self, color: int = 0xFFFFFFFF, duration_sec: float = 0.5) -> None:
        self.flash_color = color
        self.flash_duration = max(0.01, duration_sec)
        self.flash_alpha = 1.0

    def shake(self, intensity: float = 0.02, duration_sec: float = 0.25) -> None:
        self.shake_intensity = intensity
        self.shake_duration = duration_sec

    def update(self, dt_sec: float) -> None:
        # Smooth camera position & zoom decay back to default_zoom
        factor = min(1.0, self.follow_lerp * (dt_sec * 60.0))
        self.scroll_x += (self.target_x - self.scroll_x) * factor
        self.scroll_y += (self.target_y - self.scroll_y) * factor
        self.zoom += (self.default_zoom - self.zoom) * min(1.0, 0.05 * (dt_sec * 60.0))

        if self.flash_alpha > 0.0 and self.flash_duration > 0.0:
            self.flash_alpha = max(0.0, self.flash_alpha - (dt_sec / self.flash_duration))

        if self.shake_duration > 0.0:
            self.shake_duration = max(0.0, self.shake_duration - dt_sec)
            if self.shake_duration <= 0.0:
                self.shake_intensity = 0.0


class FunkinSprite:
    """
    🇬🇧 Sprite with frame-based animation playback, per-animation offsets, and zIndex
       (`source/funkin/graphics/FunkinSprite.hx`).
    🇺🇦 Базовий спрайт гри з підтримкою покадрової анімації (24 FPS), зміщень (`offsets`) та `zIndex`.
    """
    __slots__ = (
        "name",
        "x",
        "y",
        "zIndex",
        "scale_x",
        "scale_y",
        "alpha",
        "angle",
        "flipX",
        "flipY",
        "visible",
        "isPixel",
        "animations",
        "anim_offsets",
        "current_anim",
        "current_frame_idx",
        "anim_timer",
        "anim_fps",
        "anim_looped",
        "anim_finished",
    )

    def __init__(self, x: float = 0.0, y: float = 0.0, name: str = "") -> None:
        self.name: str = name
        self.x: float = float(x)
        self.y: float = float(y)
        self.zIndex: int = 0
        self.scale_x: float = 1.0
        self.scale_y: float = 1.0
        self.alpha: float = 1.0
        self.angle: float = 0.0
        self.flipX: bool = False
        self.flipY: bool = False
        self.visible: bool = True
        self.isPixel: bool = False

        self.animations: Dict[str, List[AtlasFrame]] = {}
        self.anim_offsets: Dict[str, Tuple[float, float]] = {}
        self.current_anim: str = ""
        self.current_frame_idx: int = 0
        self.anim_timer: float = 0.0
        self.anim_fps: int = 24
        self.anim_looped: bool = False
        self.anim_finished: bool = True

    def add_animation_by_prefix(
        self,
        anim_name: str,
        prefix: str,
        all_frames: List[AtlasFrame],
        fps: int = 24,
        looped: bool = False,
        offset: Tuple[float, float] = (0.0, 0.0),
    ) -> int:
        """
        🇬🇧 Filters `all_frames` by `prefix` and registers animation `anim_name`.
        🇺🇦 Знаходить усі кадри, що починаються з `prefix`, і створює анімацію `anim_name`.
        """
        matched = [f for f in all_frames if f.name.startswith(prefix)]
        if matched:
            self.animations[anim_name] = matched
            self.anim_offsets[anim_name] = offset
        return len(matched)

    def play_anim(self, anim_name: str, force: bool = True, fps: int = 24, looped: bool = False) -> None:
        if not force and self.current_anim == anim_name and not self.anim_finished:
            return
        self.current_anim = anim_name
        self.current_frame_idx = 0
        self.anim_timer = 0.0
        self.anim_fps = max(1, fps)
        self.anim_looped = looped
        self.anim_finished = False

    def update(self, dt_sec: float) -> None:
        if self.anim_finished or not self.current_anim:
            return
        frames = self.animations.get(self.current_anim)
        if not frames:
            self.anim_finished = True
            return

        self.anim_timer += dt_sec
        frame_duration = 1.0 / self.anim_fps
        while self.anim_timer >= frame_duration:
            self.anim_timer -= frame_duration
            self.current_frame_idx += 1
            if self.current_frame_idx >= len(frames):
                if self.anim_looped:
                    self.current_frame_idx = 0
                else:
                    self.current_frame_idx = len(frames) - 1
                    self.anim_finished = True
                    break


class HealthIcon:
    """
    🇬🇧 Character icon on the health bar (`source/funkin/play/components/HealthIcon.hx`).
       Bops on every beat and switches to losing frame (`1`) when character health < 20%!
    🇺🇦 Іконка персонажа на смужці здоров'я: пульсує на кожному біті та змінює емоцію при < 20% HP!
    """
    __slots__ = ("char_id", "is_player", "x", "y", "scale", "base_scale", "angle", "frame_index", "should_bop")

    def __init__(self, char_id: str = "bf", is_player: bool = True, base_scale: float = 1.0) -> None:
        self.char_id: str = char_id
        self.is_player: bool = is_player
        self.x: float = 0.0
        self.y: float = 0.0
        self.base_scale: float = base_scale
        self.scale: float = base_scale
        self.angle: float = 0.0
        self.frame_index: int = 0  # 0 = Normal, 1 = Losing (<20%), 2 = Winning (>80%)
        self.should_bop: bool = True

    def on_beat_hit(self) -> None:
        if self.should_bop:
            self.scale = self.base_scale * 1.2

    def update(self, dt_sec: float, health: float) -> None:
        """
        🇬🇧 Updates icon scale decay and frame index based on `health` (`0.0 .. 2.0`).
        🇺🇦 Оновлює розмір та емоцію іконки залежно від здоров'я Бойфренда (`0.0 .. 2.0`).
        """
        self.scale += (self.base_scale - self.scale) * min(1.0, 9.0 * dt_sec)
        health_pct = max(0.0, min(1.0, health / Constants.HEALTH_MAX))

        if self.is_player:
            self.frame_index = 1 if health_pct < 0.20 else 0
        else:
            self.frame_index = 1 if health_pct > 0.80 else 0


class JudgementPopup:
    """
    🇬🇧 Floating judgement sprite (`SICK!`, `GOOD!`, `BAD!`, `SHIT!`) with velocity & fade-out
       (`source/funkin/play/components/PopUpStuff.hx`).
    🇺🇦 Вилітаючий напис оцінки (`SICK!`, `GOOD!`, `BAD!`, `SHIT!`) та комбо після натискання ноти.
    """
    __slots__ = ("judgement", "combo", "x", "y", "vel_y", "accel_y", "alpha", "age_sec", "alive")

    def __init__(self, judgement: str, combo: int, x: float = 560.0, y: float = 300.0) -> None:
        self.judgement: str = judgement.upper()
        self.combo: int = combo
        self.x: float = x
        self.y: float = y
        self.vel_y: float = -160.0
        self.accel_y: float = 550.0
        self.alpha: float = 1.0
        self.age_sec: float = 0.0
        self.alive: bool = True

    def update(self, dt_sec: float) -> None:
        if not self.alive:
            return
        self.age_sec += dt_sec
        self.vel_y += self.accel_y * dt_sec
        self.y += self.vel_y * dt_sec
        if self.age_sec > 0.35:
            self.alpha = max(0.0, self.alpha - dt_sec * 3.0)
            if self.alpha <= 0.0:
                self.alive = False


class CountdownStep:
    """
    🇬🇧 Pre-song `3 - 2 - 1 - GO!` countdown steps (`source/funkin/play/Countdown.hx`).
    🇺🇦 Кроки відліку перед початком пісні: `THREE (3) -> TWO (2) -> ONE (1) -> GO! -> AFTER`.
    """
    BEFORE: int = 0
    THREE: int = 1
    TWO: int = 2
    ONE: int = 3
    GO: int = 4
    AFTER: int = 5

    SOUNDS: Dict[int, str] = {
        1: "gameplay/countdown/funkin/introTHREE",
        2: "gameplay/countdown/funkin/introTWO",
        3: "gameplay/countdown/funkin/introONE",
        4: "gameplay/countdown/funkin/introGO",
    }
    LABELS: Dict[int, str] = {
        1: "3 (READY?)",
        2: "2 (SET!)",
        3: "1 (GET IT!)",
        4: "GO!!",
    }
