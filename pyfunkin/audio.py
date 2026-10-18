"""
================================================================================
PyFunkin Engine (FNF Lite) — Audio & Multi-Track Voices (`pyfunkin/audio.py`)
================================================================================
🇬🇧 EN: Clean, memory-optimized (`__slots__`) Python port of:
       - `source/funkin/audio/FunkinSound.hx` (Audio stream & SFX wrapper)
       - `source/funkin/audio/VoicesGroup.hx` (Split `Voices-bf.ogg` + `Voices-dad.ogg`
         and legacy shared `Voices.ogg` with independent `playerVolume` muting on miss!)
🇺🇦 UA: Аудіосистема та синхронізація вокальних доріжок:
       - Програє `Inst.ogg` та окремі голоси `Voices-bf.ogg` і `Voices-dad.ogg` синхронно!
       - Коли Бойфренд промахується по ноті (`Miss`), `playerVolume` стає `0.0` (голос BF замовкає,
         а інструментал і голос противника продовжують грати — точно як в оригіналі!).
================================================================================
"""

from __future__ import annotations
import os
import time
from typing import List, Optional

try:
    import pygame
    HAS_PYGAME = True
except ImportError:
    HAS_PYGAME = False


class FunkinSound:
    """
    🇬🇧 Wrapper around `pygame.mixer.Sound` / `Channel` (`source/funkin/audio/FunkinSound.hx`).
       Includes a monotonic timer fallback so gameplay works even if `.ogg` files aren't downloaded yet!
    🇺🇦 Обгортка над звуковим потоком (`Inst.ogg`, `Voices.ogg`, звукові ефекти меню).
       Працює навіть без аудіофайлів (за точним системним таймером), щоб гру можна було тестувати одразу!
    """
    __slots__ = (
        "file_path",
        "playing",
        "paused",
        "looped",
        "_volume",
        "pitch",
        "length_ms",
        "_start_perf_ms",
        "_paused_pos_ms",
        "_sound_obj",
        "_channel",
    )

    def __init__(self, file_path: str = "", looped: bool = False, volume: float = 1.0) -> None:
        self.file_path: str = file_path
        self.playing: bool = False
        self.paused: bool = False
        self.looped: bool = looped
        self._volume: float = float(volume)
        self.pitch: float = 1.0
        self.length_ms: float = 120_000.0  # Default 2 min fallback
        self._start_perf_ms: float = 0.0
        self._paused_pos_ms: float = 0.0
        self._sound_obj = None
        self._channel = None

        if HAS_PYGAME and file_path and os.path.exists(file_path):
            try:
                if pygame.mixer.get_init():
                    self._sound_obj = pygame.mixer.Sound(file_path)
                    self._sound_obj.set_volume(self._volume)
                    self.length_ms = self._sound_obj.get_length() * 1000.0
            except Exception:
                self._sound_obj = None

    @property
    def volume(self) -> float:
        return self._volume

    @volume.setter
    def volume(self, val: float) -> None:
        self._volume = max(0.0, min(1.0, float(val)))
        if self._sound_obj is not None:
            try:
                self._sound_obj.set_volume(self._volume)
            except Exception:
                pass
        if self._channel is not None:
            try:
                self._channel.set_volume(self._volume)
            except Exception:
                pass

    @property
    def time(self) -> float:
        """🇬🇧 Current playback position in milliseconds. / 🇺🇦 Поточна позиція треку в мілісекундах."""
        if not self.playing:
            return self._paused_pos_ms
        if self.paused:
            return self._paused_pos_ms
        now_ms = time.perf_counter() * 1000.0
        elapsed = (now_ms - self._start_perf_ms) * self.pitch
        if self.looped and self.length_ms > 0:
            return elapsed % self.length_ms
        return min(elapsed, self.length_ms)

    @time.setter
    def time(self, pos_ms: float) -> None:
        pos_ms = max(0.0, float(pos_ms))
        self._paused_pos_ms = pos_ms
        self._start_perf_ms = (time.perf_counter() * 1000.0) - (pos_ms / max(0.01, self.pitch))

    def play(self, start_ms: float = 0.0) -> None:
        self.playing = True
        self.paused = False
        self.time = start_ms
        if self._sound_obj is not None:
            try:
                loops = -1 if self.looped else 0
                self._channel = self._sound_obj.play(loops=loops)
                if self._channel is not None:
                    self._channel.set_volume(self._volume)
            except Exception:
                pass

    def pause(self) -> None:
        if self.playing and not self.paused:
            self._paused_pos_ms = self.time
            self.paused = True
            if self._channel is not None:
                try:
                    self._channel.pause()
                except Exception:
                    pass

    def resume(self) -> None:
        if self.playing and self.paused:
            self.paused = False
            self.time = self._paused_pos_ms
            if self._channel is not None:
                try:
                    self._channel.unpause()
                except Exception:
                    pass

    def stop(self) -> None:
        self.playing = False
        self.paused = False
        self._paused_pos_ms = 0.0
        if self._channel is not None:
            try:
                self._channel.stop()
            except Exception:
                pass


class VoicesGroup:
    """
    🇬🇧 Synchronizes player (`Voices-bf.ogg`) and opponent (`Voices-dad.ogg`) vocal tracks
       (`source/funkin/audio/VoicesGroup.hx`).
       Mutes ONLY Boyfriend's voice when missing a note while Dad keeps singing!
    🇺🇦 Керує вокальними доріжками гравця (`Voices-bf.ogg`) та опонента (`Voices-dad.ogg`).
       При промаху вимикає тільки голос Бойфренда, а опонент продовжує співати!
    """
    __slots__ = (
        "legacyVoiceSystem",
        "playerVoices",
        "opponentVoices",
        "_playerVolume",
        "_opponentVolume",
        "playerVoicesOffset",
        "opponentVoicesOffset",
    )

    def __init__(self) -> None:
        self.legacyVoiceSystem: bool = False
        self.playerVoices: List[FunkinSound] = []
        self.opponentVoices: List[FunkinSound] = []
        self._playerVolume: float = 1.0
        self._opponentVolume: float = 1.0
        self.playerVoicesOffset: float = 0.0
        self.opponentVoicesOffset: float = 0.0

    def addPlayerVoice(self, sound: FunkinSound) -> None:
        sound.volume = self._playerVolume
        self.playerVoices.append(sound)

    def addOpponentVoice(self, sound: FunkinSound) -> None:
        sound.volume = self._opponentVolume
        self.opponentVoices.append(sound)

    @property
    def playerVolume(self) -> float:
        return self._playerVolume

    @playerVolume.setter
    def playerVolume(self, volume: float) -> None:
        self._playerVolume = max(0.0, min(1.0, float(volume)))
        for v in self.playerVoices:
            v.volume = self._playerVolume

    @property
    def opponentVolume(self) -> float:
        return self._opponentVolume

    @opponentVolume.setter
    def opponentVolume(self, volume: float) -> None:
        self._opponentVolume = max(0.0, min(1.0, float(volume)))
        for v in self.opponentVoices:
            v.volume = self._opponentVolume

    def play(self, start_ms: float = 0.0) -> None:
        for v in self.playerVoices:
            v.play(max(0.0, start_ms - self.playerVoicesOffset))
        for v in self.opponentVoices:
            v.play(max(0.0, start_ms - self.opponentVoicesOffset))

    def pause(self) -> None:
        for v in self.playerVoices + self.opponentVoices:
            v.pause()

    def resume(self) -> None:
        for v in self.playerVoices + self.opponentVoices:
            v.resume()

    def stop(self) -> None:
        for v in self.playerVoices + self.opponentVoices:
            v.stop()

    def sync_to_instrumental(self, inst_time_ms: float, max_drift_ms: float = 25.0) -> None:
        """
        🇬🇧 Re-synchronizes vocal tracks if they drift more than `25 ms` from `Inst.ogg`.
        🇺🇦 Автоматично підрівнює голоси під `Inst.ogg`, якщо виник розсинхрон понад `25 мс`.
        """
        for v in self.playerVoices:
            target = inst_time_ms - self.playerVoicesOffset
            if abs(v.time - target) > max_drift_ms:
                v.time = target
        for v in self.opponentVoices:
            target = inst_time_ms - self.opponentVoicesOffset
            if abs(v.time - target) > max_drift_ms:
                v.time = target
