"""
================================================================================
PyFunkin Engine (FNF Lite) — Scoring, Judgements & Highscore (`pyfunkin/scoring.py`)
================================================================================
🇬🇧 EN: Clean, memory-optimized (`__slots__`) Python port of:
       - `source/funkin/play/scoring/Scoring.hx` (PBOT1, WEEK7, LEGACY scoring systems)
       - `source/funkin/Highscore.hx` (Tallies, Combo, Accuracy & Rank calculation)
🇺🇦 UA: Точна конвертація системи оцінювання нот та підрахунку очок і рангів:
       - Підтримка систем PBOT1 (сигмоїдна крива точності до мс!), WEEK7 та LEGACY.
       - Розрахунок суджень (`killer`, `sick`, `good`, `bad`, `shit`, `miss`) та рангів
         (`PERFECT_GOLD`, `PERFECT`, `EXCELLENT`, `GREAT`, `GOOD`, `SHIT`).
================================================================================
"""

from __future__ import annotations
import math
from typing import Optional
from .core import Constants


class ScoringSystem:
    """
    🇬🇧 Which system to use when scoring and judging notes (`Scoring.hx`).
    🇺🇦 Система оцінювання влучань по нотах.
    """
    # 🇬🇧 Used in Week 6 and older (step function). / 🇺🇦 Класична система (до 6 тижня).
    LEGACY: str = "LEGACY"
    # 🇬🇧 Used in Week 7 (tighter windows). / 🇺🇦 Система 7 тижня з вужчими таймінгами.
    WEEK7: str = "WEEK7"
    # 🇬🇧 Points Based On Timing v1 (sigmoid curve based on exact ms offset!).
    # 🇺🇦 Сучасна система PBOT1: очки залежать від кожної мілісекунди за сигмоїдною формулою!
    PBOT1: str = "PBOT1"


class ScoringRank:
    """
    🇬🇧 Song completion rank (`ScoringRank` in `Scoring.hx`).
    🇺🇦 Фінальний ранг за проходження пісні (від `SHIT` до золотого `PERFECT_GOLD`).
    """
    PERFECT_GOLD: str = "PERFECT_GOLD"
    PERFECT: str = "PERFECT"
    EXCELLENT: str = "EXCELLENT"
    GREAT: str = "GREAT"
    GOOD: str = "GOOD"
    SHIT: str = "SHIT"

    _VALUES = {
        "SHIT": 0,
        "GOOD": 1,
        "GREAT": 2,
        "EXCELLENT": 3,
        "PERFECT": 4,
        "PERFECT_GOLD": 5,
    }

    @classmethod
    def get_value(cls, rank: Optional[str]) -> int:
        if rank is None:
            return -1
        return cls._VALUES.get(rank, -1)

    @classmethod
    def is_better(cls, rank_a: Optional[str], rank_b: Optional[str]) -> bool:
        """🇬🇧 True if `rank_a > rank_b`. / 🇺🇦 Перевіряє, чи новий ранг вищий за попередній рекорд."""
        return cls.get_value(rank_a) > cls.get_value(rank_b)

    @classmethod
    def get_freeplay_color(cls, rank: str) -> int:
        """🇬🇧 Color of the rank icon in Freeplay (`Scoring.hx`). / 🇺🇦 Колір іконки рангу у Freeplay."""
        return {
            cls.SHIT: 0xFF6044FF,
            cls.GOOD: 0xFFEF8764,
            cls.GREAT: 0xFFEAF6FF,
            cls.EXCELLENT: 0xFFFDCB42,
            cls.PERFECT: 0xFFFF58B4,
            cls.PERFECT_GOLD: 0xFFFFB619,
        }.get(rank, 0xFF6044FF)

    @classmethod
    def get_music_delay(cls, rank: str) -> float:
        """🇬🇧 Result screen music delay in seconds (`Scoring.hx`). / 🇺🇦 Затримка музики на екрані результатів."""
        if rank in (cls.PERFECT_GOLD, cls.PERFECT):
            return 95.0 / 24.0
        if rank == cls.EXCELLENT:
            return 0.0
        if rank == cls.GREAT:
            return 5.0 / 24.0
        if rank == cls.GOOD:
            return 3.0 / 24.0
        return 2.0 / 24.0


class Tallies:
    """
    🇬🇧 Tracks notes hit, judgements, combo, and score for a song or level (`Highscore.hx`).
    🇺🇦 Лічильник статистики пісні або цілого тижня (комбо, очки, кількість Sick/Good/Bad/Shit/Miss).
    """
    __slots__ = (
        "combo",
        "missed",
        "shit",
        "bad",
        "good",
        "sick",
        "killer",
        "totalNotes",
        "totalNotesHit",
        "maxCombo",
        "score",
        "isNewHighscore",
    )

    def __init__(self, totalNotes: int = 0) -> None:
        self.combo: int = 0
        self.missed: int = 0
        self.shit: int = 0
        self.bad: int = 0
        self.good: int = 0
        self.sick: int = 0
        self.killer: int = 0
        self.totalNotes: int = totalNotes
        self.totalNotesHit: int = 0
        self.maxCombo: int = 0
        self.score: int = 0
        self.isNewHighscore: bool = False

    def record_hit(self, ms_timing: float, system: str = ScoringSystem.PBOT1) -> str:
        """
        🇬🇧 Process a note hit at `ms_timing` offset, update score/combo/tallies, and return judgement.
        🇺🇦 Обробляє влучання по ноті з похибкою `ms_timing` мс, оновлює комбо та очки.
        """
        judgement = Scoring.judgeNote(ms_timing, system)
        if judgement == "miss":
            self.record_miss(system)
            return "miss"

        pts = Scoring.scoreNote(ms_timing, system)
        self.score += pts
        self.totalNotesHit += 1

        if judgement == "sick":
            self.sick += 1
            self.combo += 1
        elif judgement == "good":
            self.good += 1
            self.combo += 1
        elif judgement == "bad":
            self.bad += 1
            if Constants.JUDGEMENT_BAD_COMBO_BREAK if hasattr(Constants, "JUDGEMENT_BAD_COMBO_BREAK") else True:
                self.combo = 0
        elif judgement == "shit":
            self.shit += 1
            self.combo = 0

        if self.combo > self.maxCombo:
            self.maxCombo = self.combo

        return judgement

    def record_miss(self, system: str = ScoringSystem.PBOT1) -> None:
        """🇬🇧 Record a missed note. / 🇺🇦 Записує пропуск ноти (Miss) та скидає комбо."""
        self.missed += 1
        self.combo = 0
        self.score += Scoring.getMissScore(system)

    @property
    def accuracy(self) -> float:
        """🇬🇧 Completion percentage (0.0 to 1.0). / 🇺🇦 Точність виконання пісні (від 0.0 до 1.0)."""
        return Scoring.tallyCompletion(self)


class Scoring:
    """
    🇬🇧 Static class holding all note scoring, judgement, and rank formulas (`Scoring.hx`).
    🇺🇦 Всі математичні формули оцінювання нот та розрахунку фінального рангу.
    """
    # --- PBOT1 CONSTANTS ---
    PBOT1_MAX_SCORE: int = 500
    PBOT1_SCORING_OFFSET: float = 54.99
    PBOT1_SCORING_SLOPE: float = 0.080
    PBOT1_MIN_SCORE: float = 9.0
    PBOT1_MISS_SCORE: int = -100

    PBOT1_PERFECT_THRESHOLD: float = 5.0     # <= 5ms -> always 500 pts!
    PBOT1_MISS_THRESHOLD: float = 160.0      # 160ms hit window
    PBOT1_KILLER_THRESHOLD: float = 12.5     # ~7.5% of hit window
    PBOT1_SICK_THRESHOLD: float = 45.0       # ~25% of hit window
    PBOT1_GOOD_THRESHOLD: float = 90.0       # ~55% of hit window
    PBOT1_BAD_THRESHOLD: float = 135.0       # ~85% of hit window
    PBOT1_SHIT_THRESHOLD: float = 160.0      # 100% of hit window

    # --- LEGACY & WEEK7 CONSTANTS ---
    LEGACY_HIT_WINDOW: float = (10.0 / 60.0) * 1000.0  # 166.67 ms (10 frames at 60 FPS)
    LEGACY_SICK_THRESHOLD: float = 0.2
    LEGACY_GOOD_THRESHOLD: float = 0.75
    LEGACY_BAD_THRESHOLD: float = 0.9
    LEGACY_SHIT_THRESHOLD: float = 1.0

    LEGACY_SICK_SCORE: int = 350
    LEGACY_GOOD_SCORE: int = 200
    LEGACY_BAD_SCORE: int = 100
    LEGACY_SHIT_SCORE: int = 50
    LEGACY_MISS_SCORE: int = -10

    WEEK7_HIT_WINDOW: float = LEGACY_HIT_WINDOW
    WEEK7_SICK_THRESHOLD: float = 0.2
    WEEK7_GOOD_THRESHOLD: float = 0.55
    WEEK7_BAD_THRESHOLD: float = 0.8
    WEEK7_MISS_SCORE: int = -10

    @classmethod
    def scoreNote(cls, msTiming: float, scoringSystem: str = ScoringSystem.PBOT1) -> int:
        """
        🇬🇧 Determine the score a note receives under a given scoring system (`Scoring.hx`).
        🇺🇦 Визначає кількість очок за влучання з різницею часу `msTiming` мс.
        """
        if scoringSystem == ScoringSystem.LEGACY:
            return cls._scoreNoteLEGACY(msTiming)
        if scoringSystem == ScoringSystem.WEEK7:
            return cls._scoreNoteWEEK7(msTiming)
        return cls._scoreNotePBOT1(msTiming)

    @classmethod
    def judgeNote(cls, msTiming: float, scoringSystem: str = ScoringSystem.PBOT1) -> str:
        """
        🇬🇧 Determine the judgement (`sick`, `good`, `bad`, `shit`, `miss`) for `msTiming`.
        🇺🇦 Визначає оцінку влучання (`sick`, `good`, `bad`, `shit`, `miss`) за похибкою в мс.
        """
        if scoringSystem == ScoringSystem.LEGACY:
            return cls._judgeNoteLEGACY(msTiming)
        if scoringSystem == ScoringSystem.WEEK7:
            return cls._judgeNoteWEEK7(msTiming)
        return cls._judgeNotePBOT1(msTiming)

    @classmethod
    def getMissScore(cls, scoringSystem: str = ScoringSystem.PBOT1) -> int:
        if scoringSystem in (ScoringSystem.LEGACY, ScoringSystem.WEEK7):
            return cls.LEGACY_MISS_SCORE
        return cls.PBOT1_MISS_SCORE

    @classmethod
    def _scoreNotePBOT1(cls, msTiming: float) -> int:
        absTiming = abs(msTiming)
        if absTiming > cls.PBOT1_MISS_THRESHOLD:
            return cls.PBOT1_MISS_SCORE
        if absTiming < cls.PBOT1_PERFECT_THRESHOLD:
            return cls.PBOT1_MAX_SCORE
        # 🇬🇧 Fancy sigmoid equation from Scoring.hx!
        # 🇺🇦 Фірмова сигмоїдна формула очок з офіційного Scoring.hx!
        factor = 1.0 - (1.0 / (1.0 + math.exp(-cls.PBOT1_SCORING_SLOPE * (absTiming - cls.PBOT1_SCORING_OFFSET))))
        return int(cls.PBOT1_MAX_SCORE * factor + cls.PBOT1_MIN_SCORE)

    @classmethod
    def _judgeNotePBOT1(cls, msTiming: float) -> str:
        absTiming = abs(msTiming)
        if absTiming <= cls.PBOT1_SICK_THRESHOLD:
            return "sick"
        if absTiming <= cls.PBOT1_GOOD_THRESHOLD:
            return "good"
        if absTiming <= cls.PBOT1_BAD_THRESHOLD:
            return "bad"
        if absTiming <= cls.PBOT1_SHIT_THRESHOLD:
            return "shit"
        return "miss"

    @classmethod
    def _scoreNoteLEGACY(cls, msTiming: float) -> int:
        absTiming = abs(msTiming)
        w = cls.LEGACY_HIT_WINDOW
        if absTiming < w * cls.LEGACY_SICK_THRESHOLD:
            return cls.LEGACY_SICK_SCORE
        if absTiming < w * cls.LEGACY_GOOD_THRESHOLD:
            return cls.LEGACY_GOOD_SCORE
        if absTiming < w * cls.LEGACY_BAD_THRESHOLD:
            return cls.LEGACY_BAD_SCORE
        if absTiming < w * cls.LEGACY_SHIT_THRESHOLD:
            return cls.LEGACY_SHIT_SCORE
        return 0

    @classmethod
    def _judgeNoteLEGACY(cls, msTiming: float) -> str:
        absTiming = abs(msTiming)
        w = cls.LEGACY_HIT_WINDOW
        if absTiming <= w * cls.LEGACY_SICK_THRESHOLD:
            return "sick"
        if absTiming <= w * cls.LEGACY_GOOD_THRESHOLD:
            return "good"
        if absTiming <= w * cls.LEGACY_BAD_THRESHOLD:
            return "bad"
        if absTiming <= w * cls.LEGACY_SHIT_THRESHOLD:
            return "shit"
        return "miss"

    @classmethod
    def _scoreNoteWEEK7(cls, msTiming: float) -> int:
        absTiming = abs(msTiming)
        w = cls.WEEK7_HIT_WINDOW
        if absTiming < w * cls.WEEK7_SICK_THRESHOLD:
            return cls.LEGACY_SICK_SCORE
        if absTiming < w * cls.WEEK7_GOOD_THRESHOLD:
            return cls.LEGACY_GOOD_SCORE
        if absTiming < w * cls.WEEK7_BAD_THRESHOLD:
            return cls.LEGACY_BAD_SCORE
        if absTiming < w:
            return cls.LEGACY_SHIT_SCORE
        return 0

    @classmethod
    def _judgeNoteWEEK7(cls, msTiming: float) -> str:
        absTiming = abs(msTiming)
        w = cls.WEEK7_HIT_WINDOW
        if absTiming <= w * cls.WEEK7_SICK_THRESHOLD:
            return "sick"
        if absTiming <= w * cls.WEEK7_GOOD_THRESHOLD:
            return "good"
        if absTiming <= w * cls.WEEK7_BAD_THRESHOLD:
            return "bad"
        if absTiming <= w:
            return "shit"
        return "miss"

    @classmethod
    def tallyCompletion(cls, tallies: Optional[Tallies]) -> float:
        """
        🇬🇧 "Top secret funkin crew patented algorithm": (sick + good - missed) / totalNotes clamped to [0, 1].
        🇺🇦 «Секретний запатентований алгоритм FunkinCrew»: (sick + good - missed) / totalNotes у межах [0, 1].
        """
        if tallies is None or tallies.totalNotes <= 0:
            return 0.0
        val = (tallies.sick + tallies.good - tallies.missed) / float(tallies.totalNotes)
        return max(0.0, min(1.0, val))

    @classmethod
    def calculateRank(cls, tallies: Optional[Tallies]) -> Optional[str]:
        """
        🇬🇧 Calculate final song rank (`PERFECT_GOLD`, `PERFECT`, `EXCELLENT`, `GREAT`, `GOOD`, `SHIT`).
        🇺🇦 Визначає фінальний ранг проходження пісні за статистикою `Tallies`.
        """
        if tallies is None or tallies.totalNotes <= 0:
            return None

        # 🇬🇧 Perfect (Gold) is a Sick Full Clear! / 🇺🇦 Золотий Ідеал — коли 100% нот вибиті на Sick!
        if tallies.sick == tallies.totalNotes:
            return ScoringRank.PERFECT_GOLD

        completion = cls.tallyCompletion(tallies)
        if completion >= 1.00:
            return ScoringRank.PERFECT
        if completion >= 0.90:
            return ScoringRank.EXCELLENT
        if completion >= 0.80:
            return ScoringRank.GREAT
        if completion >= 0.60:
            return ScoringRank.GOOD
        return ScoringRank.SHIT

    @classmethod
    def getHealthDelta(cls, judgement: str) -> float:
        """
        🇬🇧 Returns health change for a given judgement (`Constants.hx`).
        🇺🇦 Повертає зміну здоров'я Бойфренда для отриманої оцінки.
        """
        return {
            "killer": Constants.HEALTH_KILLER_BONUS,
            "sick": Constants.HEALTH_SICK_BONUS,
            "good": Constants.HEALTH_GOOD_BONUS,
            "bad": Constants.HEALTH_BAD_BONUS,
            "shit": Constants.HEALTH_SHIT_BONUS,
            "miss": Constants.HEALTH_MISS_PENALTY,
        }.get(judgement, 0.0)


class Highscore:
    """
    🇬🇧 Tracks score and combo tallies for the current song and story level (`Highscore.hx`).
    🇺🇦 Зберігає статистику поточної пісні (`tallies`) та всього тижня Story Mode (`talliesLevel`).
    """
    tallies: Tallies = Tallies()
    talliesLevel: Tallies = Tallies()

    @staticmethod
    def combineTallies(newTally: Tallies, baseTally: Tallies) -> Tallies:
        combined = Tallies(totalNotes=newTally.totalNotes + baseTally.totalNotes)
        combined.missed = newTally.missed + baseTally.missed
        combined.shit = newTally.shit + baseTally.shit
        combined.bad = newTally.bad + baseTally.bad
        combined.good = newTally.good + baseTally.good
        combined.sick = newTally.sick + baseTally.sick
        combined.killer = newTally.killer + baseTally.killer
        combined.totalNotesHit = newTally.totalNotesHit + baseTally.totalNotesHit
        combined.score = newTally.score + baseTally.score
        combined.combo = newTally.combo
        combined.maxCombo = max(newTally.maxCombo, baseTally.maxCombo)
        return combined
