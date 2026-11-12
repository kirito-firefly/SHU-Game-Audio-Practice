"""Build and inspect the course project through the official Wwise HTTP API."""

import json
from pathlib import Path
import urllib.error
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
ENDPOINT = "http://127.0.0.1:8090/waapi"
PARENT = "\\Containers\\Default Work Unit"
MASTER = PARENT + "\\ChinjuForest"
LAYERS = {
    "WindLeaves": {"files": ["AMB_WindLeaves_Loop"], "volume": -.5},
    "Waterfall": {"files": ["AMB_Waterfall_Loop"], "volume": -7, "distance": 160},
    "Insects": {"files": ["AMB_Insects_Loop"], "volume": -3},
    "Birds": {"files": [f"SFX_Bird_{i:02d}" for i in range(1, 4)], "volume": -12, "distance": 60, "delay": [12, 25], "initial": [8, 15]},
    "Rustles": {"files": [f"SFX_Rustle_{i:02d}" for i in range(1, 4)], "volume": -9, "distance": 15, "delay": [18, 35], "initial": [15, 25]},
    "Bells": {"files": [f"SFX_Bell_{i:02d}" for i in range(1, 4)], "volume": -10, "distance": 120, "delay": [45, 80], "initial": [30, 50]},
}


def call(uri, args=None, options=None):
    payload = json.dumps({"uri": uri, "args": args or {}, "options": options or {}}).encode()
    request = urllib.request.Request(ENDPOINT, payload, {"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        raise RuntimeError(error.read().decode()) from error


def create(parent, name, kind, properties=None):
    args = {"parent": parent, "name": name, "type": kind, "onNameConflict": "merge"}
    args.update({"@" + key: value for key, value in (properties or {}).items()})
    return call("ak.wwise.core.object.create", args)["id"]


def set_property(obj, name, value):
    return call("ak.wwise.core.object.setProperty", {"object": obj, "property": name, "value": value})


def random_range(obj, name, bounds):
    middle = sum(bounds) / 2
    set_property(obj, name, middle)
    call("ak.wwise.core.object.setRandomizer", {"object": obj, "property": name, "enabled": True, "min": bounds[0] - middle, "max": bounds[1] - middle})


def event(name, target, action_type):
    event_id = create("\\Events\\Default Work Unit", name, "Event")
    existing = call("ak.wwise.core.object.get", {"from": {"id": [event_id]}, "transform": [{"select": ["children"]}]}, {"return": ["id", "type"]})["return"]
    if existing:
        action = existing[0]["id"]
        for duplicate in existing[1:]:
            call("ak.wwise.core.object.delete", {"object": duplicate["id"]})
        set_property(action, "ActionType", action_type)
    else:
        action = create(event_id, "", "Action", {"ActionType": action_type})
    call("ak.wwise.core.object.setReference", {"object": action, "reference": "Target", "value": target})
    return event_id


def build():
    create(PARENT, "ChinjuForest", "BlendContainer", {"Volume": 0})
    summary = {"wwise": call("ak.wwise.core.getInfo")["version"], "layers": {}}
    for name, settings in LAYERS.items():
        layer = create(MASTER, name, "BlendContainer" if len(settings["files"]) == 1 else "RandomSequenceContainer", {"Volume": settings["volume"]})
        if "delay" in settings:
            for prop, value in {"RandomOrSequence": 1, "NormalOrShuffle": 0, "RandomAvoidRepeating": True, "RandomAvoidRepeatingCount": 1, "PlayMechanismStepOrContinuous": 0, "PlayMechanismLoop": True, "PlayMechanismInfiniteOrNumberOfLoops": 1, "PlayMechanismSpecialTransitions": True, "PlayMechanismSpecialTransitionsType": 1}.items():
                set_property(layer, prop, value)
            random_range(layer, "PlayMechanismSpecialTransitionsValue", settings["delay"])
            random_range(layer, "InitialDelay", settings["initial"])
        for file_name in settings["files"]:
            sound_id = create(layer, file_name, "Sound")
            if "delay" not in settings:
                set_property(sound_id, "IsLoopingEnabled", True)
                set_property(sound_id, "IsLoopingInfinite", True)
        if "distance" in settings:
            distance = settings["distance"]
            attenuation = create("\\Attenuations\\Default Work Unit", "ATT_" + name, "Attenuation")
            set_property(attenuation, "RadiusMax", distance)
            points = [{"x": distance * fraction, "y": volume, "shape": "Linear"} for fraction, volume in [(0, 0), (.1, -3), (.5, -18), (1, -60)]]
            call("ak.wwise.core.object.setAttenuationCurve", {"object": attenuation, "curveType": "VolumeDryUsage", "use": "Custom", "points": points})
            for prop, value in {"OverridePositioning": True, "ListenerRelativeRouting": True, "3DSpatialization": 1, "3DPosition": 0, "EnableAttenuation": True}.items():
                set_property(layer, prop, value)
            call("ak.wwise.core.object.setReference", {"object": layer, "reference": "Attenuation", "value": attenuation})
        event("Play_" + name, layer, 1)
        summary["layers"][name] = {"id": layer, **settings}
    event("Play_ChinjuForest", MASTER, 1)
    event("Stop_ChinjuForest", MASTER, 2)
    summary["soundcaster"] = create("\\Soundcaster Sessions\\Default Work Unit", "ChinjuForest_Test", "SoundcasterSession")
    call("ak.wwise.core.project.save")
    (ROOT / "Evidence" / "project_configuration.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def import_audio():
    repair_sources()
    imports = []
    for name, settings in LAYERS.items():
        for file_name in settings["files"]:
            path = ROOT / "Assets" / (file_name + ".wav")
            if not path.is_file():
                raise FileNotFoundError(path)
            imports.append({"audioFile": str(path), "objectPath": MASTER + "\\" + name + "\\<Sound SFX>" + file_name + "\\<AudioFileSource>Source"})
    result = call("ak.wwise.core.audio.import", {"importOperation": "useExisting", "default": {"importLanguage": "SFX"}, "imports": imports})
    call("ak.wwise.core.project.save")
    (ROOT / "Evidence" / "audio_import.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


def repair_sources():
    repaired = []
    for name, settings in LAYERS.items():
        for file_name in settings["files"]:
            sound = MASTER + "\\" + name + "\\" + file_name
            children = call("ak.wwise.core.object.get", {"from": {"path": [sound]}, "transform": [{"select": ["children"]}]}, {"return": ["id", "name", "type"]})["return"]
            sources = [child for child in children if child["type"] == "AudioFileSource"]
            if not sources:
                continue
            source = sources[0]["id"]
            call("ak.wwise.core.sound.setActiveSource", {"sound": sound, "source": source})
            for duplicate in sources[1:]:
                call("ak.wwise.core.object.delete", {"object": duplicate["id"]})
            call("ak.wwise.core.object.setName", {"object": source, "value": "Source"})
            repaired.append({"sound": file_name, "source_count": 1, "duplicates_removed": len(sources) - 1})
    call("ak.wwise.core.project.save")
    (ROOT / "Evidence" / "source_consistency.json").write_text(json.dumps(repaired, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    import sys
    {"build": build, "import": import_audio, "repair": repair_sources}[sys.argv[1]]()
