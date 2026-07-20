from pathlib import Path

path = Path("docs/specs/STATUS.md")
text = path.read_text(encoding="utf-8")
old = "| 048 | in_review | [#150](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/150) | BLUEREV-PROCESS-1: biomass, nutrients, gas, harvest, and energy/cost KPIs |"
new = "| 048 | merged | [#150](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/150) | BLUEREV-PROCESS-1: biomass, nutrients, gas, harvest, and energy/cost KPIs |"
if text.count(old) != 1:
    raise SystemExit(f"expected one 048 in_review row, found {text.count(old)}")
if new in text:
    raise SystemExit("048 merged row already present")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
