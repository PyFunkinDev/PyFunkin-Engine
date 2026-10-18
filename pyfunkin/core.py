"""
================================================================================
PyFunkin Engine (FNF Lite) — Core Timing & Song Data Module (`pyfunkin/core.py`)
================================================================================
🇬🇧 EN: Clean, memory-optimized (`__slots__`) Python port of the official Haxe source:
       - `source/funkin/util/Constants.hx`
       - `source/funkin/data/song/SongData.hx`
       - `source/funkin/Conductor.hx`
🇺🇦 UA: Чистий та оптимізований по пам'яті (`__slots__`) порт із офіційного Haxe-коду.
       Збережено оригінальні коментарі та жарти розробників FunkinCrew!
================================================================================
"""

from __future__ import annotations
import math
import time
from typing import Callable, Dict, List, Optional, Any


class Signal:
    """
    🇬🇧 Lightweight equivalent of `flixel.util.FlxSignal` for event dispatching.
    🇺🇦 Легкий аналог `FlxSignal` для підписки на події (`onStepHit`, `onBeatHit`, `onMeasureHit`).
    """
    __slots__ = ("_listeners",)

    def __init__(self) -> None:
        self._listeners: List[Callable[[], None]] = []

    def add(self, callback: Callable[[], None]) -> None:
        if callback not in self._listeners:
            self._listeners.append(callback)

    def remove(self, callback: Callable[[], None]) -> None:
        if callback in self._listeners:
            self._listeners.remove(callback)

    def dispatch(self) -> None:
        for callback in list(self._listeners):
            callback()


class Constants:
    """
    🇬🇧 A store of unchanging, globally relevant values (`source/funkin/util/Constants.hx`).
    🇺🇦 Глобальні константи гри: таймінги, здоров'я, оцінки, кольори та розширення файлів.
    """
    TITLE: str = "Friday Night Funkin' Lite (PyFunkin)"
    VERSION: str = "v0.8.1-py"

    # --- COLORS / КОЛЬОРИ ---
    COLOR_HEALTH_BAR_RED: int = 0xFFFF0000
    COLOR_HEALTH_BAR_GREEN: int = 0xFF66FF33
    COLOR_NOTES: List[int] = [
        0xFFFF22AA,  # left (0)  - Purple / Фіолетовий
        0xFF00EEFF,  # down (1)  - Cyan / Блакитний
        0xFF00CC00,  # up (2)    - Green / Зелений
        0xFFCC1111,  # right (3) - Red / Червоний
    ]

    # --- GAME DEFAULTS / СТАНДАРТНІ НАЛАШТУВАННЯ ---
    DEFAULT_DIFFICULTY: str = "normal"
    DEFAULT_DIFFICULTY_LIST: List[str] = ["easy", "normal", "hard"]
    DEFAULT_DIFFICULTY_LIST_ERECT: List[str] = ["erect", "nightmare"]
    DEFAULT_DIFFICULTY_LIST_FULL: List[str] = ["easy", "normal", "hard", "erect", "nightmare"]

    DEFAULT_CHARACTER: str = "bf"
    DEFAULT_HEALTH_ICON: str = "face"
    DEFAULT_STAGE: str = "mainStage"
    DEFAULT_SONG: str = "tutorial"
    DEFAULT_VARIATION: str = "default"
    DEFAULT_BPM: float = 100.0
    DEFAULT_SCROLLSPEED: float = 1.0
    DEFAULT_TIME_SIGNATURE_NUM: int = 4
    DEFAULT_TIME_SIGNATURE_DEN: int = 4

    # --- TIMING / ТАЙМІНГИ ---
    # 🇬🇧 A magic number used when calculating scroll speed and note distances.
    # 🇺🇦 Магічне число для розрахунку швидкості польоту стрілочок та відстані між ними.
    PIXELS_PER_MS: float = 0.45

    # 🇬🇧 The maximum interval within which a note can be hit, in milliseconds.
    # 🇺🇦 Максимальне вікно часу для влучання по ноті (в мілісекундах).
    HIT_WINDOW_MS: float = 160.0

    # 🇬🇧 Constant for the number of seconds in a minute ("sex per min" - FunkinCrew comment :D)
    # 🇺🇦 Кількість секунд у хвилині (з оригінальним жартом розробників у коментарі :D)
    SECS_PER_MIN: int = 60
    MS_PER_SEC: int = 1000
    STEPS_PER_BEAT: int = 4

    # 🇬🇧 All MP3 decoders introduce a playback delay of 528 samples (~12 ms at 44.1kHz).
    # 🇺🇦 Всі MP3-декодери додають затримку в 528 семплів (~12 мс), тому ми використовуємо OGG!
    MP3_DELAY_MS: float = 528 / 44100 * 1000.0

    # --- HEALTH VALUES / ЗДОРОВ'Я ---
    HEALTH_MAX: float = 2.0
    HEALTH_STARTING: float = 1.0
    HEALTH_MIN: float = 0.0
    HEALTH_KILLER_BONUS: float = 2.0 / 100.0 * HEALTH_MAX
    HEALTH_SICK_BONUS: float = 1.5 / 100.0 * HEALTH_MAX
    HEALTH_GOOD_BONUS: float = 0.75 / 100.0 * HEALTH_MAX
    HEALTH_BAD_BONUS: float = 0.0
    HEALTH_SHIT_BONUS: float = -1.0 / 100.0 * HEALTH_MAX
    HEALTH_HOLD_BONUS_PER_SECOND: float = 6.0 / 100.0 * HEALTH_MAX
    HEALTH_MISS_PENALTY: float = -4.0 / 100.0 * HEALTH_MAX
    HEALTH_GHOST_MISS_PENALTY: float = -4.0 / 100.0 * HEALTH_MAX
    HEALTH_MINE_PENALTY: float = -15.0 / 100.0 * HEALTH_MAX

    # --- FILE EXTENSIONS / РОЗШИРЕННЯ ФАЙЛІВ ---
    # 🇬🇧 FunkinCrew comment: - "I made a new file format" - "Actually new or just a renamed ZIP?"
    # 🇺🇦 Коментар розробників: - «Я створив новий формат» - «Реально новий чи просто перейменований ZIP?»
    EXT_CHART: str = "fnfc"
    EXT_STAGE: str = "fnfs"

    # 🇬🇧 Original Haxe: `#if web 'mp3' #else 'ogg' #end` (477 MB of .mp3 in repo are just for web!)
    # 🇺🇦 В оригіналі `.mp3` береться тільки для браузерів (`#if web`), а всюди інде — `.ogg`!
    EXT_SOUND: str = "ogg"
    EXT_VIDEO: str = "mp4"
    EXT_IMAGE: str = "png"   # + .webp support in PyFunkin Lite!
    EXT_DATA: str = "json"

    STRUMLINE_X_OFFSET: float = 48.0
    STRUMLINE_Y_OFFSET: float = 24.0
    PIXEL_ART_SCALE: float = 6.0


class SongTimeChange:
    """
    🇬🇧 Represents a BPM or time signature change at a specific timestamp (`SongData.hx`).
    🇺🇦 Описує зміну BPM або музичного розміру (напр. 4/4) у конкретний момент пісні.
    """
    __slots__ = ("timeStamp", "bpm", "timeSignatureNum", "timeSignatureDen", "beatTime", "beatTuplets")

    def __init__(
        self,
        timeStamp: float = 0.0,
        bpm: float = Constants.DEFAULT_BPM,
        timeSignatureNum: int = Constants.DEFAULT_TIME_SIGNATURE_NUM,
        timeSignatureDen: int = Constants.DEFAULT_TIME_SIGNATURE_DEN,
        beatTime: float = 0.0,
        beatTuplets: Optional[List[int]] = None,
    ) -> None:
        self.timeStamp: float = float(timeStamp)
        self.bpm: float = float(bpm)
        self.timeSignatureNum: int = int(timeSignatureNum)
        self.timeSignatureDen: int = int(timeSignatureDen)
        self.beatTime: float = float(beatTime)
        self.beatTuplets: List[int] = beatTuplets if beatTuplets is not None else [4, 4, 4, 4]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SongTimeChange":
        return cls(
            timeStamp=float(data.get("t", 0.0)),
            bpm=float(data.get("bpm", Constants.DEFAULT_BPM)),
            timeSignatureNum=int(data.get("n", Constants.DEFAULT_TIME_SIGNATURE_NUM)),
            timeSignatureDen=int(data.get("d", Constants.DEFAULT_TIME_SIGNATURE_DEN)),
            beatTime=float(data.get("b", 0.0)),
            beatTuplets=list(data.get("bt", [4, 4, 4, 4])),
        )


class SongNoteData:
    """
    🇬🇧 Single note entry from `song-chart.json`. Uses `__slots__` to save ~50% RAM on mobile!
    🇺🇦 Одна нота з чарту `song-chart.json`. Використовує `__slots__` для економії ~50% RAM на мобілках!
    """
    __slots__ = ("time", "data", "length", "kind")

    def __init__(self, time: float, data: int, length: float = 0.0, kind: Optional[str] = None) -> None:
        self.time: float = float(time)
        self.data: int = int(data)      # 0..3 = Player (BF), 4..7 = Opponent (Dad)
        self.length: float = float(length)
        self.kind: Optional[str] = kind

    @property
    def direction(self) -> int:
        """0 = LEFT, 1 = DOWN, 2 = UP, 3 = RIGHT"""
        return self.data % 4

    @property
    def is_player_note(self) -> bool:
        """True if note belongs to Boyfriend (0..3), False if Opponent (4..7)."""
        return (self.data // 4) == 0

    @property
    def direction_name(self) -> str:
        return ("LEFT ⬅️", "DOWN ⬇️", "UP ⬆️", "RIGHT ➡️")[self.direction]

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "SongNoteData":
        return cls(
            time=float(d["t"]),
            data=int(d["d"]),
            length=float(d.get("l", 0.0)),
            kind=d.get("k"),
        )


class SongEventData:
    """
    🇬🇧 Chart event (`FocusCamera`, `PlayAnimation`, `SetCameraBop`, etc.).
    🇺🇦 Подія чарту (поворот камери на персонажа, програвання анімації `hey`, зум тощо).
    """
    __slots__ = ("time", "eventKind", "value")

    def __init__(self, time: float, eventKind: str, value: Any = None) -> None:
        self.time: float = float(time)
        self.eventKind: str = str(eventKind)
        self.value: Any = value

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "SongEventData":
        return cls(time=float(d["t"]), eventKind=str(d["e"]), value=d.get("v"))


def round_decimal(val: float, precision: int) -> float:
    """
    🇬🇧 Equivalent to `FlxMath.roundDecimal(val, precision)`. Prevents 8 becoming 7.9999999.
    🇺🇦 Аналог `FlxMath.roundDecimal`: захищає від похибок плаваючої крапки (7.9999999 замість 8).
    """
    mult = 10 ** precision
    return math.floor(val * mult + 0.5) / mult


class Conductor:
    """
    🇬🇧 A core class which handles musical timing throughout the game, both in gameplay and menus.
       - 4/4 = 4 beats per measure = 16 steps per measure
       - 120 BPM = 2 onBeatHit per second = 8 onStepHit per second
    🇺🇦 Головний диригент гри: рахує музичний час, BPM, такти (measures), біти (beats) і кроки (steps).
       Викликає сигнали `onStepHit`, `onBeatHit` та `onMeasureHit` точно в такт музиці.
    """
    __slots__ = (
        "onMeasureHit",
        "onBeatHit",
        "onStepHit",
        "timeChanges",
        "currentTimeChange",
        "songPosition",
        "songPositionDelta",
        "prevTimestamp",
        "prevTime",
        "bpmOverride",
        "currentMeasure",
        "currentBeat",
        "currentStep",
        "currentMeasureTime",
        "currentBeatTime",
        "currentStepTime",
        "instrumentalOffset",
        "formatOffset",
        "globalOffset",
        "audioVisualOffset",
    )

    _instance: Optional["Conductor"] = None

    measureHit: Signal = Signal()
    beatHit: Signal = Signal()
    stepHit: Signal = Signal()

    @classmethod
    def get_instance(cls) -> "Conductor":
        if cls._instance is None:
            cls.set_instance(Conductor())
        return cls._instance  # type: ignore

    @classmethod
    def set_instance(cls, instance: Optional["Conductor"]) -> Optional["Conductor"]:
        if cls._instance is not None:
            cls._clear_singleton(cls._instance)
        cls._instance = instance
        if cls._instance is not None:
            cls._setup_singleton(cls._instance)
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        cls.set_instance(Conductor())

    @classmethod
    def _setup_singleton(cls, input_cond: "Conductor") -> None:
        input_cond.onMeasureHit.add(cls.measureHit.dispatch)
        input_cond.onBeatHit.add(cls.beatHit.dispatch)
        input_cond.onStepHit.add(cls.stepHit.dispatch)

    @classmethod
    def _clear_singleton(cls, input_cond: "Conductor") -> None:
        input_cond.onMeasureHit.remove(cls.measureHit.dispatch)
        input_cond.onBeatHit.remove(cls.beatHit.dispatch)
        input_cond.onStepHit.remove(cls.stepHit.dispatch)

    def __init__(self) -> None:
        self.onMeasureHit: Signal = Signal()
        self.onBeatHit: Signal = Signal()
        self.onStepHit: Signal = Signal()

        self.timeChanges: List[SongTimeChange] = []
        self.currentTimeChange: Optional[SongTimeChange] = None
        self.songPosition: float = 0.0
        self.songPositionDelta: float = 0.0
        self.prevTimestamp: float = 0.0
        self.prevTime: float = 0.0
        self.bpmOverride: Optional[float] = None

        self.currentMeasure: int = 0
        self.currentBeat: int = 0
        self.currentStep: int = 0

        self.currentMeasureTime: float = 0.0
        self.currentBeatTime: float = 0.0
        self.currentStepTime: float = 0.0

        self.instrumentalOffset: float = 0.0
        self.formatOffset: float = 0.0
        self.globalOffset: int = 0
        self.audioVisualOffset: int = 0

    @property
    def bpm(self) -> float:
        """🇬🇧 Current BPM at the active songPosition. / 🇺🇦 Поточний темп (BPM) пісні."""
        if self.bpmOverride is not None:
            return self.bpmOverride
        if self.currentTimeChange is None:
            return Constants.DEFAULT_BPM
        return self.currentTimeChange.bpm

    @property
    def startingBPM(self) -> float:
        if self.bpmOverride is not None:
            return self.bpmOverride
        if not self.timeChanges:
            return Constants.DEFAULT_BPM
        return self.timeChanges[0].bpm

    @property
    def timeSignatureNumerator(self) -> int:
        if self.currentTimeChange is None:
            return Constants.DEFAULT_TIME_SIGNATURE_NUM
        return self.currentTimeChange.timeSignatureNum

    @property
    def timeSignatureDenominator(self) -> int:
        if self.currentTimeChange is None:
            return Constants.DEFAULT_TIME_SIGNATURE_DEN
        return self.currentTimeChange.timeSignatureDen

    @property
    def beatLengthMs(self) -> float:
        """🇬🇧 Duration of a beat in ms. / 🇺🇦 Тривалість одного біта в мілісекундах."""
        return ((Constants.SECS_PER_MIN / self.bpm) * Constants.MS_PER_SEC) * (4.0 / self.timeSignatureDenominator)

    @property
    def stepLengthMs(self) -> float:
        """🇬🇧 Duration of a step (1/4 beat) in ms. / 🇺🇦 Тривалість одного кроку (1/4 біта) в мс."""
        return self.beatLengthMs / Constants.STEPS_PER_BEAT

    @property
    def measureLengthMs(self) -> float:
        """🇬🇧 Duration of a full measure in ms. / 🇺🇦 Тривалість цілого такту в мілісекундах."""
        return self.beatLengthMs * self.timeSignatureNumerator

    @property
    def beatsPerMeasure(self) -> float:
        return float(self.timeSignatureNumerator)

    @property
    def stepsPerMeasure(self) -> int:
        return int(self.timeSignatureNumerator * Constants.STEPS_PER_BEAT)

    @property
    def combinedOffset(self) -> float:
        return self.instrumentalOffset + self.formatOffset + self.globalOffset

    def forceBPM(self, bpm: Optional[float] = None) -> None:
        self.bpmOverride = bpm

    def mapTimeChanges(self, songTimeChanges: List[SongTimeChange]) -> None:
        """
        🇬🇧 Apply the `SongTimeChange` list from song metadata and precalculate beat times.
        🇺🇦 Завантажує таблицю змін темпу (BPM) з метаданих пісні та розраховує таймінги бітів.
        """
        self.timeChanges = []
        sorted_changes = sorted(songTimeChanges, key=lambda tc: tc.timeStamp)

        for songTimeChange in sorted_changes:
            if songTimeChange.timeStamp < 0.0:
                songTimeChange.timeStamp = 0.0

            if songTimeChange.timeStamp <= 0.0:
                songTimeChange.beatTime = 0.0
            else:
                songTimeChange.beatTime = 0.0
                if songTimeChange.timeStamp > 0.0 and len(self.timeChanges) > 0:
                    prev = self.timeChanges[-1]
                    songTimeChange.beatTime = round_decimal(
                        prev.beatTime + (
                            (songTimeChange.timeStamp - prev.timeStamp)
                            * prev.bpm / Constants.SECS_PER_MIN / Constants.MS_PER_SEC
                            * (prev.timeSignatureDen / 4.0)
                        ),
                        4
                    )
            self.timeChanges.append(songTimeChange)

        self.update(self.songPosition, applyOffsets=False)

    def getTimeInMeasures(self, ms: float) -> float:
        if not self.timeChanges:
            return ms / self.stepLengthMs / self.stepsPerMeasure

        resultMeasureTime: float = 0.0
        ms = max(0.0, ms)

        lastTimeChange = self.timeChanges[0]
        for i, timeChange in enumerate(self.timeChanges):
            if ms >= timeChange.timeStamp:
                if ms < timeChange.timeStamp or i == len(self.timeChanges) - 1:
                    lastTimeChange = timeChange
                    break
                currentStepLengthMs = (
                    ((Constants.SECS_PER_MIN / lastTimeChange.bpm) * Constants.MS_PER_SEC)
                    * (4.0 / lastTimeChange.timeSignatureDen)
                ) / Constants.STEPS_PER_BEAT
                currentStepsPerMeasure = lastTimeChange.timeSignatureNum * Constants.STEPS_PER_BEAT
                resultMeasureTime += (timeChange.timeStamp - lastTimeChange.timeStamp) / currentStepLengthMs / currentStepsPerMeasure
                lastTimeChange = timeChange

        remainingStepLengthMs = (
            ((Constants.SECS_PER_MIN / lastTimeChange.bpm) * Constants.MS_PER_SEC)
            * (4.0 / lastTimeChange.timeSignatureDen)
        ) / Constants.STEPS_PER_BEAT
        remainingStepsPerMeasure = lastTimeChange.timeSignatureNum * Constants.STEPS_PER_BEAT
        resultMeasureTime += (ms - lastTimeChange.timeStamp) / remainingStepLengthMs / remainingStepsPerMeasure
        return resultMeasureTime

    def getTimeInSteps(self, ms: float) -> float:
        """
        🇬🇧 Given a time in milliseconds, return a time in steps.
        🇺🇦 Переводить час у мілісекундах у точні кроки (steps).
        """
        if not self.timeChanges:
            return math.floor(ms / self.stepLengthMs)

        resultStep: float = 0.0
        ms = max(0.0, ms)
        lastTimeChange = self.timeChanges[0]
        for i, timeChange in enumerate(self.timeChanges):
            if ms >= timeChange.timeStamp:
                if ms < timeChange.timeStamp or i == len(self.timeChanges) - 1:
                    lastTimeChange = timeChange
                    break
                resultStep += (timeChange.beatTime - lastTimeChange.beatTime) * Constants.STEPS_PER_BEAT
                lastTimeChange = timeChange

        lastStepLengthMs = (
            ((Constants.SECS_PER_MIN / lastTimeChange.bpm) * Constants.MS_PER_SEC)
            * (4.0 / lastTimeChange.timeSignatureDen)
        ) / Constants.STEPS_PER_BEAT
        resultStep += (ms - lastTimeChange.timeStamp) / lastStepLengthMs
        return resultStep

    def getStepTimeInMs(self, stepTime: float) -> float:
        """
        🇬🇧 Given a time in steps and fractional steps, return a time in milliseconds.
        🇺🇦 Переводить номер кроку (step) назад у мілісекунди.
        """
        if not self.timeChanges:
            return stepTime * self.stepLengthMs

        resultMs: float = 0.0
        stepTime = max(0.0, stepTime)
        lastTimeChange = self.timeChanges[0]
        for i, timeChange in enumerate(self.timeChanges):
            if stepTime >= timeChange.beatTime * Constants.STEPS_PER_BEAT:
                if stepTime < (timeChange.beatTime * Constants.STEPS_PER_BEAT) or i == len(self.timeChanges) - 1:
                    lastTimeChange = timeChange
                    break
                resultMs += timeChange.timeStamp - lastTimeChange.timeStamp
                lastTimeChange = timeChange

        lastStepLengthMs = (
            ((Constants.SECS_PER_MIN / lastTimeChange.bpm) * Constants.MS_PER_SEC)
            * (4.0 / lastTimeChange.timeSignatureDen)
        ) / Constants.STEPS_PER_BEAT
        resultMs += (stepTime - lastTimeChange.beatTime * Constants.STEPS_PER_BEAT) * lastStepLengthMs
        return resultMs

    def update(self, songPos: float = 0.0, applyOffsets: bool = True, forceDispatch: bool = False) -> None:
        """
        🇬🇧 Update the conductor with the current song position in milliseconds.
           Fires `onStepHit`, `onBeatHit`, and `onMeasureHit` signals when crossing boundaries.
        🇺🇦 Оновлює стан диригента за поточною позицією музики (в мс).
           Викликає події нового кроку, біта або такту для анімацій та мод-скриптів.
        """
        if applyOffsets:
            songPos += self.combinedOffset

        oldMeasure = self.currentMeasure
        oldBeat = self.currentBeat
        oldStep = self.currentStep

        self.songPosition = songPos

        self.currentTimeChange = self.timeChanges[0] if self.timeChanges else None
        if self.songPosition > 0.0 and self.timeChanges:
            for tc in self.timeChanges:
                if self.songPosition >= tc.timeStamp:
                    self.currentTimeChange = tc
                else:
                    break

        if self.currentTimeChange is not None and self.songPosition > 0.0:
            self.currentStepTime = round_decimal(
                (self.currentTimeChange.beatTime * Constants.STEPS_PER_BEAT)
                + (self.songPosition - self.currentTimeChange.timeStamp) / self.stepLengthMs,
                6
            )
            self.currentBeatTime = self.currentStepTime / Constants.STEPS_PER_BEAT
            self.currentMeasureTime = self.getTimeInMeasures(self.songPosition)
            self.currentStep = math.floor(self.currentStepTime)
            self.currentBeat = math.floor(self.currentBeatTime)
            self.currentMeasure = math.floor(self.currentMeasureTime)
        else:
            self.currentStepTime = round_decimal(self.songPosition / self.stepLengthMs, 4)
            self.currentBeatTime = self.currentStepTime / Constants.STEPS_PER_BEAT
            self.currentMeasureTime = self.currentStepTime / self.stepsPerMeasure
            self.currentStep = math.floor(self.currentStepTime)
            self.currentBeat = math.floor(self.currentBeatTime)
            self.currentMeasure = math.floor(self.currentMeasureTime)

        # 🇬🇧 FlxSignals are really cool. / 🇺🇦 Сигнали викликають танці персонажів та події модів!
        if self.currentStep != oldStep or forceDispatch:
            self.onStepHit.dispatch()
        if self.currentBeat != oldBeat or forceDispatch:
            self.onBeatHit.dispatch()
        if self.currentMeasure != oldMeasure or forceDispatch:
            self.onMeasureHit.dispatch()

        if self.prevTime != self.songPosition:
            self.songPositionDelta = 0.0
            self.prevTime = self.songPosition
            self.prevTimestamp = float(int(time.time() * 1000))
