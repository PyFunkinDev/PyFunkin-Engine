<div align="center">

<img src="assets/branding/Engine_Logo.png" alt="PyFunkin Engine Logo" width="560" />

# 🎤 PyFunkin Engine (`FNF Lite`) 🐍

**A lightweight, cross-platform Friday Night Funkin' Engine written in Python — engineered for 32-bit (ARMv7) & 64-bit Android devices, PCs, and instant zero-compile modding.**

**Легкий, кросплатформений рушій для Friday Night Funkin' на Python — створений для 32-бітних (ARMv7) та 64-бітних Android-смартфонів, ПК та миттєвого модингу без компіляції.**

[![Developer](https://img.shields.io/badge/Developer-PyFunkinDev-007ACC?style=for-the-badge&logo=github)](https://github.com/PyFunkinDev)
[![Python](https://img.shields.io/badge/Python-3.9%2B-FFD43B?style=for-the-badge&logo=python&logoColor=blue)](https://www.python.org/)
[![Platforms](https://img.shields.io/badge/Platforms-ARMv7%20(32--bit)%20%7C%20ARM64%20%7C%20PC-33CC66?style=for-the-badge)](#)
[![Offline Size](https://img.shields.io/badge/100%25%20Offline%20Assets-~200%20MB-FF22AA?style=for-the-badge)](#)

</div>

---

## 🌍 Why PyFunkin Engine? / Чому саме PyFunkin Engine?

| Feature / Характеристика | Official FNF (Haxe / C++) | 🐍 **PyFunkin Engine (`FNF Lite`)** |
| :--- | :--- | :--- |
| **📱 Mobile CPU Support / Підтримка процесорів** | `ARM64` only (Android 9+) | **`ARMv7` (32-bit), `ARM64`, `x86`, PC, Pydroid 3, APK** |
| **💾 Full Offline Assets Size / Розмір ассетів офлайн** | `1,273 MB` (~1.3 GB) | **`~180–210 MB`** (No duplicate `.mp3`, `.webp` sprites, optimized `.ogg`) |
| **🧠 RAM Optimization / Споживання оперативки** | High VRAM (`OutOfMemory` on 2–3 GB devices) | **Ultra-low RAM (`__slots__`, lazy loading, 32-bit friendly)** |
| **⚡ Mod Compilation Time / Час компіляції модів** | 10–20 minutes (`lime build` C++) | **0.0 seconds (Instant run!)** |
| **🧩 Modding Languages / Мови для модингу** | Haxe / HScript (`.hx` / `.hxc`) | **Native Python (`.py`) + Lua (`.lua`) + V-Slice `.json`** |

---

## ✨ Key Architecture Highlights / Головні особливості архітектури

### 1. 🎵 Exact V-Slice Timing Core (`pyfunkin/core.py`)
* **🇬🇧 EN:** Direct 1-to-1 mathematical port of `Conductor.hx`, `Constants.hx`, and `SongData.hx` from `FunkinCrew/Funkin`. Handles variable BPM (`SongTimeChange`), time signatures (`4/4`, `3/4`, `7/8`), note hit windows (`160 ms`), and `onStepHit` / `onBeatHit` / `onMeasureHit` signals with zero drift.
* **🇺🇦 UA:** Точний математичний порт `Conductor.hx`, `Constants.hx` та `SongData.hx` з офіційного репозиторію. Підтримує зміну BPM посеред пісні (`SongTimeChange`), будь-які музичні розміри, вікно влучання `160 мс` та сигнали тактів/бітів/кроків з ідеальною точністю.

### 2. 🎨 Universal 3-in-1 Sprite Atlas Loader (`pyfunkin/atlas.py`)
* **🇬🇧 EN:** Supports all three official FNF character and stage animation formats out of the box:
  1. **Sparrow v2 Atlas (`.png` / `.webp` + `.xml`)** — Classic characters & community mods.
  2. **SpriteSheet Packer Atlas (`.png` / `.webp` + `.txt`)** — Pixel-art characters like `spirit.txt` (Week 6).
  3. **Adobe Animate Texture Atlas (`spritemap1.json` + `Animation.json`)** — Modern modular symbol animations (`abotSystem`, `bf`, `dad`, `gf`, `pico`).
* **🇺🇦 UA:** Підтримує всі три формати анімацій FNF з коробки: класичний Sparrow (`.xml`), текстовий Packer (`.txt`, як у Духа з 6-го тижня) та новий компактний Texture Atlas (`spritemap1.json` + `Animation.json`, як у `abotSystem` та оновлених персонажів).

### 3. 📉 Smart 100% Offline Asset Compression (`1.27 GB` ➡️ `~200 MB`)
* **🇬🇧 EN:** Our analysis of `FunkinCrew/Funkin.assets` (`2,435 files`, `1,273.38 MB`) revealed that **477.75 MB** (`413 files`) are duplicate `.mp3` files kept strictly for `#if web` (old browser compatibility). By stripping web-only `.mp3` duplicates, converting spritesheets to lossless/high-quality `.webp`, and optimizing `.ogg` audio streams, the entire game remains **100% offline** at a fraction of the size.
* **🇺🇦 UA:** Аналіз офіційного `Funkin.assets` показав, що **477.75 МБ** — це просто дублікати у форматі `.mp3`, які лежать там виключно для старих веббраузерів (`#if web`). Видалення дублікатів `.mp3`, переведення спрайтів у `.webp` та оптимізація `.ogg` дозволяють зберегти **100% офлайн-контенту** у ~6 разів меншому розмірі!

---

## 🗂️ Repository Structure / Структура проєкту

```text
pyfunkin/
├── assets/
│   └── branding/                  # Official PyFunkin Engine Logos & Icons by @PyFunkinDev
│       ├── Engine_Logo.png
│       ├── Engine_icon.png
│       ├── Engine_Icon_Black_Outline.png
│       └── Engine_icon_logo_outline.png
├── __init__.py                    # Package entry point & public API exports
├── core.py                        # Conductor, Constants, Signals, SongMetadata & Chart parser
├── atlas.py                       # CharacterData & 3-in-1 Atlas parsers (.xml, .txt, Animation.json)
├── scoring.py                     # PBOT1 / WEEK7 / LEGACY Scoring, Judgements, Tallies & Ranks
├── paths.py                       # Smart Asset Resolver (Mods -> Level -> Shared -> Preload, .webp/.png) & StageData
├── mobile.py                      # All 5 Mobile Hitbox Schemes & Nanosecond PreciseInputManager
├── modding.py                     # Hybrid Mod Loader (.py native scripts, .lua bridge, ScriptEvent)
├── save.py                        # Preferences (auto-downscroll on mobile, 32-bit RAM mode), Save & LevelData
├── audio.py                       # FunkinSound & VoicesGroup (split Voices-bf/dad.ogg sync & miss muting)
├── graphics.py                    # FunkinCamera, FunkinSprite, HealthIcon, JudgementPopup & Countdown
├── states.py                      # MusicBeatState, TitleState (bopping Engine_Logo.png), MainMenu, Freeplay, ResultState
├── playstate.py                   # Full PlayState & Strumline gameplay controller
├── main.py                        # Main entry point, FunkinMemory GC, FunkinDebugDisplay (FPS/RAM) & Self-Test
└── README.md                      # Bilingual Documentation (EN / UA)
```

---

## 👤 Author / Автор

Created with ❤️ by **[PyFunkinDev](https://github.com/PyFunkinDev)**  
*"Just a person. I wanted to make my own engine for FNF. Developer of PyFunkin Engine ☺️"*
