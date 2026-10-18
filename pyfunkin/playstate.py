"""
================================================================================
PyFunkin Engine (FNF Lite) — PlayState & Strumline Controller (`pyfunkin/playstate.py`)
================================================================================
🇬🇧 EN: Clean, memory-optimized (`__slots__`) Python port of:
       - `source/funkin/play/PlayState.hx` (Song lifecycle, Health, Events, Bop, Input)
       - `source/funkin/play/notes/Strumline.hx` (Note scrolling formula & hit window)
🇺🇦 UA: Головна ігрова сцена бою (`PlayState`) та контролер стрілочок (`Strumline`):
       - Поєднує `Conductor`, `Scoring`, `Tallies`, `StageData`, `FunkinHitbox` та `HybridModHandler`.
       - Точна формула позиції нот на екрані (`0.45 * (note.time - songPosition) * scrollSpeed`).
================================================================================
"""

from __future__ import annotations
import json
from typing import Any, Dict, List, Optional
from .core import Conductor, Constants, SongEventData, SongNoteData, SongTimeChange
from .scoring import Highscore, Scoring, ScoringSystem, Tallies
from .paths import StageData
from .mobile import FunkinHitbox, FunkinHitboxControlSchemes, PreciseInputEvent, PreciseInputManager
from .modding import HybridModHandler, ScriptEvent, ScriptEventType


class Strumline:
    """
    🇬🇧 Manages a 4-key receptor lane (Player or Opponent) and calculates note Y positions
       (`source/funkin/play/notes/Strumline.hx`).
    🇺🇦 Керує 4 сірими стрілочками (Гравця або Опонента) та рахує координату Y кожної ноти.
    """
    __slots__ = ("is_player", "x", "y", "scroll_speed", "downscroll", "active_notes", "botplay")

    def __init__(
        self,
        is_player: bool = True,
        x: float = 740.0,
        y: float = Constants.STRUMLINE_Y_OFFSET,
        scroll_speed: float = 1.0,
        downscroll: bool = False,
        botplay: bool = False,
    ) -> None:
        self.is_player: bool = is_player
        self.x: float = x
        self.y: float = y
        self.scroll_speed: float = scroll_speed
        self.downscroll: bool = downscroll
        self.active_notes: List[SongNoteData] = []
        self.botplay: bool = botplay

    def calculate_note_y(self, note_time_ms: float, song_position_ms: float) -> float:
        """
        🇬🇧 Official FNF note scrolling formula (`Constants.PIXELS_PER_MS = 0.45`):
           `distance = (note_time - song_position) * 0.45 * scroll_speed`
        🇺🇦 Офіційна формула руху стрілочок у FNF (`0.45 пікселя на мілісекунду * scrollSpeed`).
        """
        offset_px = (note_time_ms - song_position_ms) * Constants.PIXELS_PER_MS * self.scroll_speed
        return (self.y - offset_px) if self.downscroll else (self.y + offset_px)


class PlayState:
    """
    🇬🇧 Main gameplay state coordinating music timing, notes, scoring, camera focus,
       mobile hitboxes, and mod script events (`source/funkin/play/PlayState.hx`).
    🇺🇦 Головний контролер гри: керує часом пісні, спавном і натисканням стрілочок,
       здоров'ям Бойфренда, фокусом камери, мобільними хітбоксами та скриптами модів!
    """
    __slots__ = (
        "song_id",
        "song_name",
        "difficulty",
        "scoring_system",
        "conductor",
        "player_strumline",
        "opponent_strumline",
        "pending_notes",
        "pending_events",
        "tallies",
        "health",
        "camera_focus_target",
        "camera_zoom",
        "stage",
        "hitbox",
        "input_manager",
        "mod_handler",
        "is_paused",
        "is_game_over",
    )

    instance: Optional["PlayState"] = None

    def __init__(
        self,
        song_id: str = "bopeebo",
        difficulty: str = Constants.DEFAULT_DIFFICULTY,
        mobile_scheme: str = FunkinHitboxControlSchemes.FOUR_LANES,
        downscroll: bool = False,
    ) -> None:
        PlayState.instance = self
        self.song_id: str = song_id
        self.song_name: str = song_id.capitalize()
        self.difficulty: str = difficulty
        self.scoring_system: str = ScoringSystem.PBOT1

        self.conductor: Conductor = Conductor.get_instance()
        self.conductor.reset()
        self.conductor = Conductor.get_instance()

        self.player_strumline: Strumline = Strumline(is_player=True, x=740.0, downscroll=downscroll)
        self.opponent_strumline: Strumline = Strumline(is_player=False, x=96.0, downscroll=downscroll, botplay=True)

        self.pending_notes: List[SongNoteData] = []
        self.pending_events: List[SongEventData] = []
        self.tallies: Tallies = Tallies()
        self.health: float = Constants.HEALTH_STARTING
        self.camera_focus_target: str = "dad"
        self.camera_zoom: float = 1.0
        self.stage: Optional[StageData] = None

        # Mobile Hitbox & Precise Input setup
        self.hitbox: FunkinHitbox = FunkinHitbox(scheme=mobile_scheme)
        self.input_manager: PreciseInputManager = PreciseInputManager.get_instance()
        self.input_manager.initializeHitbox(self.hitbox)
        self.input_manager.onInputPressed.append(self._on_precise_input_pressed)

        # Modding setup
        self.mod_handler: HybridModHandler = HybridModHandler(game_context=self)
        self.conductor.onStepHit.add(self._on_step_hit)
        self.conductor.onBeatHit.add(self._on_beat_hit)

        self.is_paused: bool = False
        self.is_game_over: bool = False

    def load_song_from_json(self, metadata_raw: str, chart_raw: str, stage_raw: Optional[str] = None) -> None:
        """
        🇬🇧 Loads V-Slice `song-metadata.json`, `song-chart.json`, and optional `stage.json`.
        🇺🇦 Завантажує пісню з офіційних JSON-файлів (`metadata.json`, `chart.json` та `stage.json`).
        """
        meta = json.loads(metadata_raw.lstrip("\ufeff").strip())
        chart = json.loads(chart_raw.lstrip("\ufeff").strip())

        self.song_name = str(meta.get("songName", self.song_id))
        tcs = [SongTimeChange.from_dict(tc) for tc in meta.get("timeChanges", [])]
        self.conductor.mapTimeChanges(tcs)

        # Scroll speed per difficulty
        scroll_map = chart.get("scrollSpeed", {})
        if isinstance(scroll_map, dict):
            spd = float(scroll_map.get(self.difficulty, scroll_map.get("default", 1.0)))
        else:
            spd = float(scroll_map)
        self.player_strumline.scroll_speed = spd
        self.opponent_strumline.scroll_speed = spd

        # Parse notes & sort by timestamp
        raw_notes = chart.get("notes", {}).get(self.difficulty, [])
        all_notes = sorted((SongNoteData.from_dict(n) for n in raw_notes), key=lambda n: n.time)
        self.pending_notes = all_notes

        player_note_count = sum(1 for n in all_notes if n.is_player_note)
        self.tallies = Tallies(totalNotes=player_note_count)
        Highscore.tallies = self.tallies

        # Parse chart events
        raw_events = chart.get("events", [])
        self.pending_events = sorted((SongEventData.from_dict(e) for e in raw_events), key=lambda e: e.time)

        if stage_raw:
            stage_id = meta.get("playData", {}).get("stage", Constants.DEFAULT_STAGE)
            self.stage = StageData.from_json(stage_id, stage_raw)
            self.camera_zoom = self.stage.cameraZoom

        self.mod_handler.dispatch_event(ScriptEvent(ScriptEventType.CREATE))

    def update(self, song_position_ms: float) -> None:
        """
        🇬🇧 Main per-frame update at `song_position_ms`:
           1) Updates `Conductor` (fires `onStepHit` / `onBeatHit`)
           2) Spawns notes within `2000 ms` lookahead window
           3) Auto-hits opponent notes & processes missed player notes past `-160 ms`
           4) Processes chart events (`FocusCamera`, `PlayAnimation`, etc.)
        🇺🇦 Головний цикл оновлення кадру на позиції `song_position_ms`.
        """
        if self.is_paused or self.is_game_over:
            return

        self.conductor.update(song_position_ms)

        # 1. Spawn incoming notes within 2000ms window
        spawn_horizon = song_position_ms + (2000.0 / max(0.1, self.player_strumline.scroll_speed))
        while self.pending_notes and self.pending_notes[0].time <= spawn_horizon:
            note = self.pending_notes.pop(0)
            if note.is_player_note:
                self.player_strumline.active_notes.append(note)
            else:
                self.opponent_strumline.active_notes.append(note)

        # 2. Auto-hit opponent notes at exact timestamp
        while self.opponent_strumline.active_notes and self.opponent_strumline.active_notes[0].time <= song_position_ms:
            opp_note = self.opponent_strumline.active_notes.pop(0)
            self.mod_handler.dispatch_event(
                ScriptEvent(ScriptEventType.NOTE_HIT, note=opp_note, is_player=False, judgement="sick")
            )

        # 3. Check player notes for Botplay or Misses (past HIT_WINDOW_MS = 160ms)
        if self.player_strumline.botplay:
            while self.player_strumline.active_notes and self.player_strumline.active_notes[0].time <= song_position_ms:
                p_note = self.player_strumline.active_notes.pop(0)
                self._register_player_hit(p_note, 0.0)
        else:
            while (
                self.player_strumline.active_notes
                and (song_position_ms - self.player_strumline.active_notes[0].time) > Constants.HIT_WINDOW_MS
            ):
                missed_note = self.player_strumline.active_notes.pop(0)
                self._register_player_miss(missed_note)

        # 4. Trigger chart events
        while self.pending_events and self.pending_events[0].time <= song_position_ms:
            ev = self.pending_events.pop(0)
            if ev.eventKind == "FocusCamera":
                target_id = ev.value.get("char", 0) if isinstance(ev.value, dict) else ev.value
                self.camera_focus_target = "bf" if target_id == 0 else ("dad" if target_id == 1 else "gf")

        self.mod_handler.dispatch_event(ScriptEvent(ScriptEventType.UPDATE, songPosition=song_position_ms))

    def press_direction(self, direction: int, input_song_pos_ms: Optional[float] = None) -> Optional[str]:
        """
        🇬🇧 Attempts to hit the closest matching player note in `direction` (`0..3`) within `160 ms`.
        🇺🇦 Намагається влучити по найближчій ноті напрямку `direction` (`0..3`) у вікні `160 мс`.
        """
        pos = input_song_pos_ms if input_song_pos_ms is not None else self.conductor.songPosition

        candidates = [
            n for n in self.player_strumline.active_notes
            if n.direction == direction and abs(n.time - pos) <= Constants.HIT_WINDOW_MS
        ]
        if not candidates:
            # Ghost miss penalty if no note is in window
            self.health = max(Constants.HEALTH_MIN, self.health + Constants.HEALTH_GHOST_MISS_PENALTY)
            return None

        target_note = min(candidates, key=lambda n: abs(n.time - pos))
        self.player_strumline.active_notes.remove(target_note)
        ms_offset = pos - target_note.time
        return self._register_player_hit(target_note, ms_offset)

    def _register_player_hit(self, note: SongNoteData, ms_offset: float) -> str:
        judgement = self.tallies.record_hit(ms_offset, self.scoring_system)
        self.health = min(Constants.HEALTH_MAX, max(Constants.HEALTH_MIN, self.health + Scoring.getHealthDelta(judgement)))
        self.mod_handler.dispatch_event(
            ScriptEvent(
                ScriptEventType.NOTE_HIT,
                cancelable=True,
                note=note,
                is_player=True,
                judgement=judgement,
                ms_offset=ms_offset,
            )
        )
        if self.health <= Constants.HEALTH_MIN:
            self.is_game_over = True
        return judgement

    def _register_player_miss(self, note: SongNoteData) -> None:
        self.tallies.record_miss(self.scoring_system)
        self.health = max(Constants.HEALTH_MIN, self.health + Constants.HEALTH_MISS_PENALTY)
        self.mod_handler.dispatch_event(ScriptEvent(ScriptEventType.NOTE_MISS, note=note, is_player=True))
        if self.health <= Constants.HEALTH_MIN:
            self.is_game_over = True

    def _on_precise_input_pressed(self, ev: PreciseInputEvent) -> None:
        if not self.is_paused and not self.is_game_over:
            self.press_direction(ev.noteDirection)

    def _on_step_hit(self) -> None:
        self.mod_handler.dispatch_event(
            ScriptEvent(ScriptEventType.SONG_STEP_HIT, cancelable=True, step=self.conductor.currentStep)
        )

    def _on_beat_hit(self) -> None:
        # Default camera bop every 4 beats (DEFAULT_ZOOM_RATE = 4)
        if self.conductor.currentBeat % 4 == 0:
            self.camera_zoom *= Constants.DEFAULT_BOP_INTENSITY if hasattr(Constants, "DEFAULT_BOP_INTENSITY") else 1.015
        self.mod_handler.dispatch_event(
            ScriptEvent(ScriptEventType.SONG_BEAT_HIT, cancelable=True, beat=self.conductor.currentBeat)
        )
