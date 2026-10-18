"""
================================================================================
PyFunkin Engine (FNF Lite) — UI States & SubStates (`pyfunkin/states.py`)
================================================================================
🇬🇧 EN: Clean, memory-optimized (`__slots__`) Python port of:
       - `source/funkin/ui/MusicBeatState.hx` (Base BPM-synced state with mobile controls)
       - `source/funkin/ui/title/TitleState.hx` (Bopping `Engine_Logo.png` & introText!)
       - `source/funkin/ui/mainmenu/MainMenuState.hx` (`Story Mode`, `Freeplay`, `Mods`, `Options`)
       - `source/funkin/ui/freeplay/FreeplayState.hx` & `StoryMenuState.hx`
       - `source/funkin/play/PauseSubState.hx`, `GameOverSubState.hx` & `ResultState.hx`
🇺🇦 UA: Усі ігрові екрани та меню гри:
       - На титульному екрані (`TitleState`) пульсує наш офіційний логотип `Engine_Logo.png`!
       - Підтримує як клавіатуру (`Up/Down/Enter/Esc`), так і свайпи/тачі на телефоні!
================================================================================
"""

from __future__ import annotations
import os
import random
from typing import Callable, List, Optional, Tuple
from .core import Conductor, Constants
from .scoring import Scoring, ScoringRank, Tallies
from .save import LevelData, Save


class MusicBeatState:
    """
    🇬🇧 Base state class that connects to `Conductor` and receives `stepHit`, `beatHit`, `measureHit`
       (`source/funkin/ui/MusicBeatState.hx`).
    🇺🇦 Базовий клас для всіх екранів гри, підключений до ритму `Conductor` (`stepHit`, `beatHit`, `measureHit`).
    """
    __slots__ = ("name", "conductor", "substate", "next_state_request")

    def __init__(self, name: str = "MusicBeatState") -> None:
        self.name: str = name
        self.conductor: Conductor = Conductor.get_instance()
        self.substate: Optional["MusicBeatState"] = None
        self.next_state_request: Optional["MusicBeatState"] = None

        self.conductor.onStepHit.add(self.stepHit)
        self.conductor.onBeatHit.add(self.beatHit)
        self.conductor.onMeasureHit.add(self.measureHit)

    def destroy(self) -> None:
        self.conductor.onStepHit.remove(self.stepHit)
        self.conductor.onBeatHit.remove(self.beatHit)
        self.conductor.onMeasureHit.remove(self.measureHit)

    def stepHit(self) -> None:
        pass

    def beatHit(self) -> None:
        pass

    def measureHit(self) -> None:
        pass

    def update(self, dt_sec: float) -> None:
        if self.substate is not None:
            self.substate.update(dt_sec)


class TitleState(MusicBeatState):
    """
    🇬🇧 Opening title screen (`source/funkin/ui/title/TitleState.hx`).
       Displays wacky `introText.txt` lines on beats 1..15, flashes on beat 16, and bops
       the official `assets/branding/Engine_Logo.png`!
    🇺🇦 Титульний екран гри: показує кумедні фрази під біти `freakyMenu.ogg` (102 BPM),
       робить спалах на 16-му біті та пульсує офіційним логотипом `Engine_Logo.png`!
    """
    __slots__ = (
        "logo_path",
        "logo_scale",
        "skipped_intro",
        "title_text_lines",
        "wacky_pair",
        "gf_dance_left",
        "confirm_pressed",
    )

    DEFAULT_WACKY_QUOTES: Tuple[Tuple[str, str], ...] = (
        ("PYFUNKIN ENGINE", "ARMV7 32 BIT READY"),
        ("NO MORE 477MB MP3", "PURE OFFLINE POWER"),
        ("HAXE MEETS PYTHON", "ZERO COMPILE TIME"),
        ("MADE BY", "PYFUNKINDEV"),
    )

    def __init__(self) -> None:
        super().__init__(name="TitleState")
        self.logo_path: str = os.path.join(
            os.path.dirname(__file__), "assets", "branding", "Engine_Logo.png"
        )
        self.logo_scale: float = 1.0
        self.skipped_intro: bool = False
        self.title_text_lines: List[str] = []
        self.wacky_pair: Tuple[str, str] = random.choice(self.DEFAULT_WACKY_QUOTES)
        self.gf_dance_left: bool = False
        self.confirm_pressed: bool = False

        # Title music (`freakyMenu.ogg`) runs at 102 BPM
        self.conductor.forceBPM(102.0)

    def beatHit(self) -> None:
        # Bop logo and alternate GF dance on every beat!
        self.logo_scale = 1.08
        self.gf_dance_left = not self.gf_dance_left

        if self.skipped_intro:
            return

        b = self.conductor.currentBeat
        if b == 1:
            self.title_text_lines = ["THE FUNKIN CREW INC", "AND PYFUNKINDEV"]
        elif b == 3:
            self.title_text_lines.append("PRESENT")
        elif b == 4:
            self.title_text_lines = []
        elif b == 5:
            self.title_text_lines = ["POWERED BY", "PYTHON & SDL2"]
        elif b == 7:
            self.title_text_lines.append("PYFUNKIN ENGINE")
        elif b == 8:
            self.title_text_lines = []
        elif b == 9:
            self.title_text_lines = [self.wacky_pair[0]]
        elif b == 11:
            self.title_text_lines.append(self.wacky_pair[1])
        elif b == 12:
            self.title_text_lines = []
        elif b == 13:
            self.title_text_lines = ["FRIDAY"]
        elif b == 14:
            self.title_text_lines.append("NIGHT")
        elif b == 15:
            self.title_text_lines.append("FUNKIN' LITE")
        elif b >= 16:
            self.skip_intro()

    def skip_intro(self) -> None:
        self.skipped_intro = True
        self.title_text_lines = ["PRESS ENTER OR TAP TO BEGIN"]

    def press_enter_or_tap(self) -> None:
        if not self.skipped_intro:
            self.skip_intro()
        elif not self.confirm_pressed:
            self.confirm_pressed = True
            self.next_state_request = MainMenuState()

    def update(self, dt_sec: float) -> None:
        super().update(dt_sec)
        self.logo_scale += (1.0 - self.logo_scale) * min(1.0, 9.0 * dt_sec)


class MainMenuState(MusicBeatState):
    """
    🇬🇧 Main menu with `story_mode`, `freeplay`, `mods`, and `options` (`MainMenuState.hx`).
    🇺🇦 Головне меню гри з пунктами: `Story Mode`, `Freeplay`, `Mods` та `Options`.
    """
    __slots__ = ("items", "selected_index")

    MENU_ITEMS: Tuple[str, ...] = ("story_mode", "freeplay", "mods", "options")

    def __init__(self) -> None:
        super().__init__(name="MainMenuState")
        self.items: List[str] = list(self.MENU_ITEMS)
        self.selected_index: int = 0

    def move_selection(self, delta: int) -> str:
        self.selected_index = (self.selected_index + delta) % len(self.items)
        return self.items[self.selected_index]

    def confirm_selection(self) -> str:
        chosen = self.items[self.selected_index]
        if chosen == "story_mode":
            self.next_state_request = StoryMenuState()
        elif chosen == "freeplay":
            self.next_state_request = FreeplayState()
        elif chosen == "options":
            self.next_state_request = OptionsState()
        return chosen


class StoryMenuState(MusicBeatState):
    """
    🇬🇧 Week selector & difficulty picker (`source/funkin/ui/story/StoryMenuState.hx`).
    🇺🇦 Меню вибору тижня (`Week 1..7`, `Weekend 1`) та складності (`Easy`, `Normal`, `Hard`).
    """
    __slots__ = ("levels", "selected_level_idx", "difficulties", "selected_diff_idx")

    def __init__(self, levels: Optional[List[LevelData]] = None) -> None:
        super().__init__(name="StoryMenuState")
        if levels:
            self.levels: List[LevelData] = levels
        else:
            self.levels = [
                LevelData("tutorial", name="TEACHING TIME", songs=["tutorial"]),
                LevelData("week1", name="DADDY DEAREST", songs=["bopeebo", "fresh", "dadbattle"]),
                LevelData("week2", name="SPOOKY MONTH", songs=["spookeez", "south", "monster"]),
                LevelData("week3", name="PICO", songs=["pico", "philly-nice", "blammed"]),
                LevelData("week4", name="MOMMY MUST MURDER", songs=["satin-panties", "high", "milf"]),
                LevelData("week5", name="RED SNOW", songs=["cocoa", "eggnog", "winter-horrorland"]),
                LevelData("week6", name="HATING SIMULATOR FT. MOAWLING", songs=["senpai", "roses", "thorns"]),
                LevelData("week7", name="TANKMAN FT. JOHNNYUTAH", songs=["ugh", "guns", "stress"]),
                LevelData("weekend1", name="DUE DEBTS", songs=["darnell", "lit-up", "2hot", "blazin"]),
            ]
        self.selected_level_idx: int = 0
        self.difficulties: List[str] = list(Constants.DEFAULT_DIFFICULTY_LIST)
        self.selected_diff_idx: int = 1  # 'normal'

    @property
    def current_level(self) -> LevelData:
        return self.levels[self.selected_level_idx]

    @property
    def current_difficulty(self) -> str:
        return self.difficulties[self.selected_diff_idx]


class FreeplayState(MusicBeatState):
    """
    🇬🇧 Freeplay song capsule list with saved highscore & rank badges (`FreeplayState.hx`).
    🇺🇦 Меню вільного вибору пісень (`Freeplay`) із відображенням рекордів та іконок рангу.
    """
    __slots__ = ("songs", "selected_song_idx", "difficulties", "selected_diff_idx")

    DEFAULT_SONGS: Tuple[str, ...] = (
        "tutorial",
        "bopeebo",
        "fresh",
        "dadbattle",
        "spookeez",
        "south",
        "pico",
        "philly-nice",
        "blammed",
        "satin-panties",
        "high",
        "milf",
        "senpai",
        "roses",
        "thorns",
        "ugh",
        "guns",
        "stress",
        "darnell",
        "lit-up",
        "2hot",
        "blazin",
    )

    def __init__(self, songs: Optional[List[str]] = None) -> None:
        super().__init__(name="FreeplayState")
        self.songs: List[str] = songs if songs else list(self.DEFAULT_SONGS)
        self.selected_song_idx: int = 0
        self.difficulties: List[str] = list(Constants.DEFAULT_DIFFICULTY_LIST_FULL)
        self.selected_diff_idx: int = 2  # 'hard'

    @property
    def current_song(self) -> str:
        return self.songs[self.selected_song_idx]

    @property
    def current_difficulty(self) -> str:
        return self.difficulties[self.selected_diff_idx]


class OptionsState(MusicBeatState):
    """
    🇬🇧 Options & Mobile Hitbox Configuration screen (`OptionsState.hx`).
    🇺🇦 Меню налаштувань (Downscroll, схема мобільних хітбоксів, 32-біт економія RAM, Botplay).
    """
    __slots__ = ("save",)

    def __init__(self) -> None:
        super().__init__(name="OptionsState")
        self.save: Save = Save.get_instance()


class PauseSubState(MusicBeatState):
    """
    🇬🇧 In-song pause menu (`Resume`, `Restart Song`, `Change Difficulty`, `Exit to Menu`)
       (`source/funkin/play/PauseSubState.hx`).
    🇺🇦 Меню паузи під час пісні (`Продовжити`, `Перезапустити`, `Змінити складність`, `Вийти в меню`).
    """
    __slots__ = ("items", "selected_index")

    PAUSE_ITEMS: Tuple[str, ...] = ("Resume", "Restart Song", "Change Difficulty", "Exit to Menu")

    def __init__(self) -> None:
        super().__init__(name="PauseSubState")
        self.items: List[str] = list(self.PAUSE_ITEMS)
        self.selected_index: int = 0


class GameOverSubState(MusicBeatState):
    """
    🇬🇧 Boyfriend blue-balled death screen (`source/funkin/play/GameOverSubState.hx`).
       Plays `firstDeath` -> `deathLoop` (at 100 BPM) -> `deathConfirm` when retrying!
    🇺🇦 Екран програшу Бойфренда: програє `firstDeath` -> `deathLoop` -> `deathConfirm` при повторі!
    """
    __slots__ = ("character_id", "current_anim", "is_retrying")

    def __init__(self, character_id: str = "bf") -> None:
        super().__init__(name="GameOverSubState")
        self.character_id: str = character_id
        self.current_anim: str = "firstDeath"
        self.is_retrying: bool = False
        self.conductor.forceBPM(100.0)

    def confirm_retry(self) -> None:
        self.is_retrying = True
        self.current_anim = "deathConfirm"


class ResultState(MusicBeatState):
    """
    🇬🇧 Post-song results screen calculating Rank (`PERFECT_GOLD` .. `SHIT`) and saving highscore
       (`source/funkin/play/ResultState.hx`).
    🇺🇦 Фінальний екран результатів: вираховує ранг за проходження та зберігає новий рекорд у `Save`!
    """
    __slots__ = ("song_id", "difficulty", "tallies", "rank", "is_new_highscore")

    def __init__(self, song_id: str, difficulty: str, tallies: Tallies) -> None:
        super().__init__(name="ResultState")
        self.song_id: str = song_id
        self.difficulty: str = difficulty
        self.tallies: Tallies = tallies
        self.rank: str = Scoring.calculateRank(tallies) or ScoringRank.SHIT
        self.is_new_highscore: bool = Save.get_instance().set_song_score(
            song_id=song_id,
            difficulty=difficulty,
            score=tallies.score,
            rank=self.rank,
            accuracy=tallies.accuracy,
            max_combo=tallies.maxCombo,
        )
        self.tallies.isNewHighscore = self.is_new_highscore
