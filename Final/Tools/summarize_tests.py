"""Summarize observed engine playback and check spatial and render evidence."""
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import soundfile as sf

from wwise_project import ROOT, LAYERS

rows = [json.loads(line) for line in (ROOT / 'Evidence/full_scene_samples.jsonl').read_text().splitlines()]
onsets = {name: [] for settings in LAYERS.values() for name in settings['files']}
previous = set()
continuous = []
for row in rows:
    current = {voice['objectName'] for voice in row['voices']['return'] if not voice['isVirtual']}
    for name in current - previous:
        onsets[name].append(row['elapsed'])
    continuous.append(all(name in current for name in ['AMB_WindLeaves_Loop', 'AMB_Waterfall_Loop', 'AMB_Insects_Loop']))
    previous = current
intervals = {}
for layer in ['Birds', 'Rustles', 'Bells']:
    starts = sorted(time for name in LAYERS[layer]['files'] for time in onsets[name])
    duration = 10 if layer == 'Bells' else 4
    waits = [round(end - start - duration, 3) for start, end in zip(starts, starts[1:])]
    # Sampling started during active playback. Discard the first incomplete interval.
    measured = waits[1:]
    bounds = LAYERS[layer]['delay']
    intervals[layer] = {'observed_starts': starts, 'estimated_post_play_wait_seconds': measured, 'configured_bounds': bounds, 'within_sampling_tolerance': all(bounds[0] - .8 <= wait <= bounds[1] + .8 for wait in measured)}
spatial = json.loads((ROOT / 'Evidence/spatial_test.json').read_text())
spatial_summary = []
for layer in ['Waterfall', 'Birds', 'Rustles', 'Bells']:
    samples = [row for row in spatial if row['layer'] == layer]
    volumes = [row['contributions'][0]['return']['volume'] for row in samples]
    differences = [round(volume - volumes[0], 3) for volume in volumes]
    assert all(abs(actual - expected) < .02 for actual, expected in zip(differences, [0, -3, -18, -60]))
    spatial_summary.append({'layer': layer, 'distances_m': [row['distance_m'] for row in samples], 'engine_volume_db': volumes, 'attenuation_relative_db': differences, 'passed': True})
stop = json.loads((ROOT / 'Evidence/stop_test.json').read_text())
summary = {'sampled_seconds': rows[-1]['elapsed'] - rows[0]['elapsed'], 'sample_count': len(rows), 'all_loop_layers_nonvirtual_in_every_sample': all(continuous), 'all_twelve_assets_observed': all(onsets.values()), 'observed_onsets': onsets, 'random_waits': intervals, 'stop_event_passed': not stop['voices_after_stop']['return'] and stop['state']['state'] == 'stopped', 'spatial': spatial_summary, 'method': 'Live Wwise Authoring WAAPI profiler sampling, approximately 0.5 second cadence. Listening feedback on the REAPER mix recorded separately.'}
assert summary['sampled_seconds'] >= 600
assert summary['all_loop_layers_nonvirtual_in_every_sample'] and summary['all_twelve_assets_observed'] and summary['stop_event_passed']
assert all(item['within_sampling_tolerance'] for item in intervals.values())
(ROOT / 'Evidence/playback_summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
preview = ROOT / 'Preview/ChinjuForest_90s.wav'
audio, rate = sf.read(preview, always_2d=True)
info = sf.info(preview)
render = {'renderer': 'REAPER 7.85 native offline renderproject', 'duration_seconds': info.duration, 'sample_rate': rate, 'channels': info.channels, 'subtype': info.subtype, 'peak_dbfs': 20 * math.log10(float(np.abs(audio).max())), 'rms_dbfs': 20 * math.log10(float(np.sqrt(np.mean(audio * audio)))), 'clipped_samples': int(np.sum(np.abs(audio) >= .999)), 'sha256': hashlib.sha256(preview.read_bytes()).hexdigest(), 'listening_feedback': '2026-11-12 user accepted the mix direction and specified 哀怨轻柔'}
assert info.duration == 90 and rate == 48000 and info.channels == 2 and info.subtype == 'PCM_24' and render['clipped_samples'] == 0
(ROOT / 'Evidence/reaper_render.json').write_text(json.dumps(render, ensure_ascii=False, indent=2), encoding='utf-8')
for asset in (ROOT / 'Assets').glob('*.wav'):
    imported = ROOT / 'ChinjuForest_Ambience/Originals/SFX' / asset.name
    assert asset.read_bytes() == imported.read_bytes(), asset.name
print(json.dumps({'playback_seconds': summary['sampled_seconds'], 'random_waits': {name: [min(data['estimated_post_play_wait_seconds']),max(data['estimated_post_play_wait_seconds'])] for name,data in intervals.items()}, 'render': render},ensure_ascii=False,indent=2))
