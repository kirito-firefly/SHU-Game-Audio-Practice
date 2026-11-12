"""Reproducible editing, WAV validation, and a REAPER-compatible audition session."""

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess

import numpy as np
import soundfile as sf


ROOT = Path(__file__).resolve().parents[1]
SAMPLE_RATE = 48000
FFMPEG = os.environ.get("FFMPEG", "ffmpeg")
ASSETS = ROOT / "Assets"
SELECTED = ROOT / "Sources" / "Selected"


def decode(path, filters):
    command = [FFMPEG, "-hide_banner", "-loglevel", "error", "-i", "pipe:0", "-af", filters, "-ar", str(SAMPLE_RATE), "-ac", "2", "-f", "f32le", "pipe:1"]
    result = subprocess.run(command, input=Path(path).read_bytes(), capture_output=True, check=True)
    return np.frombuffer(result.stdout, dtype="<f4").reshape(-1, 2).astype(np.float64)


def normalize(audio, peak_db=-7, rms_db=None):
    audio = audio - audio.mean(axis=0)
    peak = float(np.max(np.abs(audio)))
    if peak < 1e-7:
        raise ValueError("Source audio is silent")
    factor = 10 ** (peak_db / 20) / peak
    if rms_db is not None:
        rms = float(np.sqrt(np.mean(audio * audio)))
        factor = min(factor, 10 ** (rms_db / 20) / rms)
    return audio * factor


def crossfade_loop(audio, seconds=60, fade_seconds=.5):
    fade_length = round(fade_seconds * SAMPLE_RATE)
    target_length = round(seconds * SAMPLE_RATE)
    needed = target_length + fade_length
    angle = np.linspace(0, np.pi / 2, fade_length)[:, None]
    unit_seam = audio[-fade_length:] * np.cos(angle) + audio[:fade_length] * np.sin(angle)
    unit = np.concatenate([audio[fade_length:-fade_length], unit_seam])
    audio = np.tile(unit, (math.ceil(needed / len(unit)), 1))[:needed]
    seam = audio[-fade_length:] * np.cos(angle) + audio[:fade_length] * np.sin(angle)
    return np.concatenate([audio[fade_length:-fade_length], seam])


def fade_oneshot(audio, fade_out=.25):
    audio = audio.copy()
    attack = min(round(.008 * SAMPLE_RATE), len(audio))
    release = min(round(fade_out * SAMPLE_RATE), len(audio))
    audio[:attack] *= np.linspace(0, 1, attack)[:, None]
    audio[-release:] *= np.linspace(1, 0, release)[:, None]
    return audio


def save(name, audio, source, processing, loop=False):
    ASSETS.mkdir(exist_ok=True)
    path = ASSETS / (name + ".wav")
    sf.write(path, audio, SAMPLE_RATE, subtype="PCM_24")
    return {"asset": path.name, "source": source, "processing": processing, "loop": loop}


def select_birds(recording):
    block = round(.1 * SAMPLE_RATE)
    samples = recording[:len(recording) // block * block]
    energy = np.sqrt(np.mean(samples.reshape(-1, block, 2) ** 2, axis=(1, 2)))
    candidates = np.argsort(energy)[::-1]
    starts = []
    for candidate in candidates:
        start = max(0, candidate * block - SAMPLE_RATE)
        if start + 4 * SAMPLE_RATE > len(recording):
            continue
        if all(abs(start - chosen) > 12 * SAMPLE_RATE for chosen in starts):
            starts.append(start)
        if len(starts) == 3:
            return sorted(starts)
    raise ValueError("Could not select three separated bird passages")


def build(downloads):
    SELECTED.mkdir(parents=True, exist_ok=True)
    decisions = []
    nature = {
        "AMB_Waterfall_Loop": (downloads / "park_ambience_river.wav", "highpass=f=90,lowpass=f=2500", -26),
        "AMB_Insects_Loop": (ROOT / "Sources" / "crickets_1.mp3", "highpass=f=1800,lowpass=f=9500", -31),
        "AMB_WindLeaves_Loop": (ROOT / "Sources" / "AI" / "wind_soft_take01.wav", "highpass=f=45,lowpass=f=1100", -33),
    }
    for name, (source, filters, rms) in nature.items():
        audio = decode(source, filters)
        if name == "AMB_Waterfall_Loop":
            audio = audio[30 * SAMPLE_RATE:100 * SAMPLE_RATE]
        if name == "AMB_WindLeaves_Loop":
            first = audio[SAMPLE_RATE:round(5.5 * SAMPLE_RATE)]
            second = audio[round(18.5 * SAMPLE_RATE):round(23.5 * SAMPLE_RATE)]
            overlap = SAMPLE_RATE // 4
            angle = np.linspace(0, np.pi / 2, overlap)[:, None]
            join = first[-overlap:] * np.cos(angle) + second[:overlap] * np.sin(angle)
            audio = np.concatenate([first[:-overlap], join, second[overlap:]])
        selected = SELECTED / (name + "_source.wav")
        sf.write(selected, audio, SAMPLE_RATE, subtype="PCM_24")
        loop = normalize(crossfade_loop(audio), rms_db=rms)
        decisions.append(save(name, loop, str(selected.relative_to(ROOT)), {"filters": filters, "loop_seconds": 60, "seam_crossfade_seconds": .5, "rms_ceiling_dbfs": rms}, True))
        if name == "AMB_WindLeaves_Loop":
            decisions[-1]["processing"]["source_keep_ranges_seconds"] = [[1, 5.5], [18.5, 23.5]]
            decisions[-1]["processing"]["join_crossfade_seconds"] = .25
    bird_recording = decode(downloads / "park_ambience_birds.wav", "highpass=f=1600,lowpass=f=7500")
    for index, start in enumerate(select_birds(bird_recording), 1):
        excerpt = bird_recording[start:start + 4 * SAMPLE_RATE]
        source = SELECTED / f"bird_excerpt_{index:02d}.wav"
        sf.write(source, excerpt, SAMPLE_RATE, subtype="PCM_24")
        audio = fade_oneshot(normalize(excerpt, peak_db=-10), .12)
        decisions.append(save(f"SFX_Bird_{index:02d}", audio, str(source.relative_to(ROOT)), {"source_start_seconds": start / SAMPLE_RATE, "duration_seconds": 4, "filters": "highpass 1600 Hz, lowpass 7500 Hz", "peak_ceiling_dbfs": -10}))
    for category, duration, filters, release in [("Rustle", 4, "highpass=f=120,lowpass=f=10500", .18), ("Bell", 10, "highpass=f=150,lowpass=f=11000", 1.0)]:
        for index in range(1, 4):
            source = ROOT / "Sources" / "AI" / f"{category.lower()}_take{index:02d}.wav"
            audio = decode(source, filters)[:round(duration * SAMPLE_RATE)]
            audio = fade_oneshot(normalize(audio, peak_db=-9), release)
            decisions.append(save(f"SFX_{category}_{index:02d}", audio, str(source.relative_to(ROOT)), {"duration_seconds": len(audio) / SAMPLE_RATE, "filters": filters, "release_seconds": release, "peak_ceiling_dbfs": -9}))
    (ROOT / "Audio_Edit" / "edit_decisions.json").write_text(json.dumps(decisions, ensure_ascii=False, indent=2), encoding="utf-8")
    write_reaper(decisions)
    validate()
    mix_preview()


def write_reaper(decisions):
    lines = ['<REAPER_PROJECT 0.1 7.85 1', '  SAMPLERATE 48000', '  TEMPO 60', '  TIMELOCKMODE 1']
    position = 0.0
    for index, decision in enumerate(decisions):
        name = Path(decision["asset"]).stem
        info = sf.info(ASSETS / decision["asset"])
        lines.extend(['  <TRACK', f'    NAME "{name}"', '    VOLPAN 1 0 1 -1', '    <ITEM', f'      POSITION {position:.9f}', f'      LENGTH {info.duration:.9f}', '      VOLPAN 1 0 1 -1', '      SOFFS 0', f'      NAME "{decision["asset"]}"', '      <SOURCE WAVE', f'        FILE "../Assets/{decision["asset"]}"', '      >', '    >', '  >'])
        position += info.duration + 1
    lines.append('>')
    (ROOT / "Audio_Edit" / "ChinjuForest_Assets.rpp").write_text("\n".join(lines) + "\n", encoding="utf-8")


def validate():
    results = []
    for path in sorted(ASSETS.glob("*.wav")):
        audio, rate = sf.read(path, always_2d=True)
        info = sf.info(path)
        loop = path.stem.startswith("AMB_")
        peak = float(np.max(np.abs(audio)))
        rms = float(np.sqrt(np.mean(audio * audio)))
        expected_length = 60 if loop else (10 if "Bell" in path.stem else 4)
        passed = rate == SAMPLE_RATE and info.channels == 2 and info.subtype == "PCM_24" and abs(info.duration - expected_length) < .001 and 1e-6 < rms and peak < .95
        result = {"file": path.name, "sample_rate": rate, "channels": info.channels, "subtype": info.subtype, "duration_seconds": info.duration, "peak_dbfs": 20 * math.log10(max(peak, 1e-15)), "rms_dbfs": 20 * math.log10(max(rms, 1e-15)), "clipped_samples": int(np.sum(np.abs(audio) >= .999)), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "passed": passed}
        if loop:
            result["seam_step_dbfs"] = 20 * math.log10(max(float(np.max(np.abs(audio[-1] - audio[0]))), 1e-15))
        results.append(result)
    report = {"asset_count": len(results), "passed": len(results) == 12 and all(item["passed"] for item in results), "assets": results}
    (ROOT / "Evidence" / "asset_validation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["passed"]:
        raise ValueError("Audio asset validation failed")


def mix_preview():
    total = 90 * SAMPLE_RATE
    mix = np.zeros((total, 2), dtype=np.float64)
    for name, gain in [("AMB_WindLeaves_Loop", -.5), ("AMB_Insects_Loop", -3), ("AMB_Waterfall_Loop", -7)]:
        audio, _ = sf.read(ASSETS / (name + ".wav"), always_2d=True)
        mix += np.tile(audio, (2, 1))[:total] * 10 ** (gain / 20)
    cues = [(9, "Bird", 1, -12, -.55), (24, "Rustle", 1, -9, .5), (31, "Bird", 2, -15, .65), (45, "Bell", 1, -18, -.25), (56, "Rustle", 2, -12, -.7), (67, "Bird", 3, -16, .2), (78, "Rustle", 3, -12, .6)]
    for second, category, index, gain, pan in cues:
        audio, _ = sf.read(ASSETS / f"SFX_{category}_{index:02d}.wav", always_2d=True)
        mono = audio.mean(axis=1)
        angle = (pan + 1) * np.pi / 4
        stereo = mono[:, None] * np.array([math.cos(angle), math.sin(angle)]) * 10 ** (gain / 20)
        offset = round(second * SAMPLE_RATE)
        mix[offset:offset + len(stereo)] += stereo
    mix[:2 * SAMPLE_RATE] *= np.linspace(0, 1, 2 * SAMPLE_RATE)[:, None]
    mix[-3 * SAMPLE_RATE:] *= np.linspace(1, 0, 3 * SAMPLE_RATE)[:, None]
    preview = ROOT / "Preview"
    preview.mkdir(exist_ok=True)
    sf.write(preview / "ChinjuForest_Numpy_90s.wav", mix, SAMPLE_RATE, subtype="PCM_24")
    (preview / "cue_sheet.json").write_text(json.dumps(cues, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["build", "validate"])
    parser.add_argument("--downloads", type=Path)
    args = parser.parse_args()
    if args.command == "build":
        if args.downloads is None:
            parser.error("--downloads is required for build")
        build(args.downloads)
    else:
        validate()
