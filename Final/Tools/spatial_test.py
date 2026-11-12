"""Measure live engine attenuation through official WAAPI voice contributions."""

import json
import time

from wwise_project import ROOT, MASTER, LAYERS, call


def position(game_object, x, z):
    call("ak.soundengine.setPosition", {
        "gameObject": game_object,
        "position": {
            "position": {"x": x, "y": 0, "z": z},
            "orientationFront": {"x": 0, "y": 0, "z": 1},
            "orientationTop": {"x": 0, "y": 1, "z": 0},
        },
    })


def run():
    call("ak.wwise.core.profiler.enableProfilerData", {"dataTypes": [{"dataType": "voices"}, {"dataType": "voiceInspector"}]})
    listener, emitter = 1000, 1001
    for game_object, name in [(listener, "Chinju_Listener"), (emitter, "Chinju_Emitter")]:
        call("ak.soundengine.registerGameObj", {"gameObject": game_object, "name": name})
    call("ak.soundengine.setListeners", {"emitter": emitter, "listeners": [listener]})
    position(listener, 0, 0)
    rows = []
    try:
        for name in ["Waterfall", "Birds", "Rustles", "Bells"]:
            settings = LAYERS[name]
            sound = MASTER + "\\" + name + "\\" + settings["files"][0]
            transport = call("ak.wwise.core.transport.create", {"object": sound, "gameObject": emitter})["transport"]
            for fraction in [0, .1, .5, 1]:
                position(emitter, 0, fraction * settings["distance"])
                call("ak.wwise.core.transport.executeAction", {"transport": transport, "action": "play"})
                time.sleep(.5)
                voices = call("ak.wwise.core.profiler.getVoices", {"time": "capture"}, {"return": ["pipelineID", "objectName", "gameObjectID", "isVirtual"]})["return"]
                matching = [voice for voice in voices if voice["gameObjectID"] == emitter]
                contributions = [call("ak.wwise.core.profiler.getVoiceContributions", {"voicePipelineID": voice["pipelineID"], "time": "capture"}) for voice in matching]
                if not contributions:
                    raise RuntimeError(f"No live voice captured for {name} at {fraction}")
                rows.append({"layer": name, "distance_m": fraction * settings["distance"], "voices": matching, "contributions": contributions})
                call("ak.wwise.core.transport.executeAction", {"transport": transport, "action": "stop"})
                time.sleep(.15)
            call("ak.wwise.core.transport.destroy", {"transport": transport})
    finally:
        call("ak.soundengine.stopAll", {"gameObject": emitter})
        for game_object in [emitter, listener]:
            call("ak.soundengine.unregisterGameObj", {"gameObject": game_object})
    (ROOT / "Evidence" / "spatial_test.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    run()
