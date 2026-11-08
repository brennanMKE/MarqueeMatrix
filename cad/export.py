"""Write fab/marquee_matrix.step and the laser cut files fab/cut/{face,carrier}.dxf|svg.

uv run --python 3.12 --with build123d cad/export.py
"""
import sys
from pathlib import Path

from build123d import Compound, ExportDXF, ExportSVG, export_step

sys.path.insert(0, str(Path(__file__).parent))
import marquee_matrix as m  # noqa: E402

out = Path(__file__).resolve().parent.parent / "fab"
(out / "cut").mkdir(parents=True, exist_ok=True)

children = []
for name, p in m.PARTS.items():
    p.label = name
    children.append(p)
export_step(Compound(children=children, label="marquee_matrix"), out / "marquee_matrix.step")

for name, sk in m.CUTS.items():
    for Exp, ext in ((ExportDXF, "dxf"), (ExportSVG, "svg")):
        e = Exp()
        e.add_layer("cut")
        e.add_shape(sk, layer="cut")
        e.write(out / "cut" / f"{name}.{ext}")
print(f"box {m.W:.0f} x {m.H:.0f} x {m.DEPTH:.0f} mm -> {out}")
