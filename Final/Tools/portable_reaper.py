"""Keep saved REAPER media and render paths relative to the delivered project."""

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
for project in (ROOT / "Audio_Edit").glob("*.rpp"):
    text = project.read_text(encoding="utf-8-sig")

    def relative_media(match):
        original = match.group(2).replace("\\", "/")
        if "/Assets/" in original:
            filename = original.rsplit("/", 1)[-1]
            if not (ROOT / "Assets" / filename).is_file():
                raise FileNotFoundError(filename)
            return match.group(1) + '"../Assets/' + filename + '"'
        return match.group(0)

    text = re.sub(r'(?m)^(\s*FILE\s+)"([^"]+)"', relative_media, text)
    if project.stem == "ChinjuForest_Mix":
        text = re.sub(r'(?m)^\s*RENDER_FILE\s+"[^"]+"', '  RENDER_FILE "../Preview/ChinjuForest_90s.wav"', text)
    project.write_text(text, encoding="utf-8")
    print(project.name)
