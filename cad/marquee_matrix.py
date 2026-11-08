"""MarqueeMatrix: a 5 x 7 grid of 120 V G40 marquee bulbs in a shallow wood box.

Coordinates: X right, Y up, Z out of the face. Z = 0 is the front of the face panel; the box
goes back to Z = -DEPTH. The grid is centred on X = Y = 0.

Stack-up (front to back):
  face panel   6 mm   acrylic, 35 socket holes; the socket mouths sit flush with its front
  gap         19 mm   the socket bodies; 19 mm (3/4") square cleats on the side walls fill it
  carrier      6 mm   acrylic; socket flanges screw to its front (M3); wires exit through it; screwed to the cleats
  bay                 SSR boards + ESP32-C3 + controller on the back panel, mains in via a cable gland in the bottom wall
  back panel   6 mm   ply, removable, screwed to the back edges of the walls

Build outputs:  uv run --python 3.12 --with build123d cad/export.py
  -> fab/marquee_matrix.step and fab/cut/{face,carrier}.dxf|svg
"""
from build123d import (Align, Box, Circle, Compound, Cylinder, Pos,
                       Rectangle, Sketch, Sphere)

# ---------------- grid ----------------
COLS, ROWS = 5, 7
PITCH = 60.0
EDGE = 48.0            # outer bulb centre to panel edge: wall 12 + cleat 19 + socket radius 12 + 5 clear

# ---------------- E12 socket (same as MakeSign; measure yours) ----------------
socket_od = 24.0
socket_h = 25.0
flange_len, flange_w, flange_t = 50.0, 14.0, 4.0
flange_hole_c = 38.0
face_hole_d = socket_od + 0.6
wire_hole_d = 8.0
screw_hole_d = 3.4     # M3 clearance
BULB_GLOBE_D = 40.0
BULB_GLOBE_Z = 23.0    # globe centre in front of the socket mouth

# ---------------- box ----------------
FACE_T = 6.0           # 6 mm (1/4") black cast acrylic (xTool P2)
CARRIER_T = 6.0        # 6 mm (1/4") cast acrylic (xTool P2)
BACK_T = 6.0           # 6 mm (1/4") ply
WALL_T = 12.0          # 1/2" hardwood or ply frame
CLEAT = socket_h - FACE_T   # 19 mm = 3/4" square stock; sets the socket depth exactly
DEPTH = 110.0          # overall, face front to back panel rear
CARRIER_CLEAR = 0.5    # each side, carrier to wall
CARRIER_SCREWS = 3     # per side, into the cleats
GLAND_D = 12.5         # PG7 cable gland in the bottom wall

# ---------------- electronics (placeholder envelopes; check against your parts) ----------------
SSR_BOARD = (103.0, 55.0, 25.0)   # 8-channel G3MB-202P module, approx
SSR_BOARDS = 5                     # 40 channels for 35 bulbs
CTRL_BOARD = (90.0, 55.0, 20.0)    # ESP32-C3 SuperMini + 5 x 74HCT595 on perfboard
PSU_5V = (34.0, 20.0, 15.0)        # HLK-PM01 style 120 V -> 5 V module
TERMINAL = (60.0, 20.0, 20.0)      # mains terminal block (L / N / PE)
BOARD_STANDOFF = 6.0

# ---------------- derived ----------------
W = (COLS - 1) * PITCH + 2 * EDGE          # 336
H = (ROWS - 1) * PITCH + 2 * EDGE          # 456
IN_W, IN_H = W - 2 * WALL_T, H - 2 * WALL_T
Z_FACE_BACK = -FACE_T
Z_CARRIER_FRONT = -socket_h                 # socket base sits on the carrier
Z_CARRIER_BACK = Z_CARRIER_FRONT - CARRIER_T
Z_BACK_FRONT = -DEPTH + BACK_T


def bulb_xy(i: int) -> tuple[float, float]:
    """Bulb index i = row * COLS + col, row 0 at the top (matches font5x7.bulbs_on)."""
    r, c = divmod(i, COLS)
    return (c - (COLS - 1) / 2) * PITCH, ((ROWS - 1) / 2 - r) * PITCH


BULBS = [bulb_xy(i) for i in range(COLS * ROWS)]
CARRIER_W, CARRIER_H = IN_W - 2 * CARRIER_CLEAR, IN_H - 2 * CARRIER_CLEAR


def carrier_screw_xy() -> list[tuple[float, float]]:
    x = IN_W / 2 - CLEAT / 2
    ys = [((CARRIER_SCREWS - 1) / 2 - k) * (IN_H - 60) / (CARRIER_SCREWS - 1) for k in range(CARRIER_SCREWS)]
    return [(s * x, y) for s in (-1, 1) for y in ys]


# ---------------- 2D cut profiles ----------------
def face_sketch() -> Sketch:
    sk = Rectangle(W, H)
    for x, y in BULBS:
        sk -= Pos(x, y) * Circle(face_hole_d / 2)
    return sk


def carrier_sketch() -> Sketch:
    sk = Rectangle(CARRIER_W, CARRIER_H)
    for x, y in BULBS:
        sk -= Pos(x, y) * Circle(wire_hole_d / 2)
        for s in (-1, 1):
            sk -= Pos(x, y + s * flange_hole_c / 2) * Circle(screw_hole_d / 2)   # flanges run along Y
    for x, y in carrier_screw_xy():
        sk -= Pos(x, y) * Circle(screw_hole_d / 2 + 0.5)   # #6 / M4 wood screw clearance
    return sk


def back_sketch() -> Sketch:
    return Rectangle(W, H)


# ---------------- 3D ----------------
def plate(sk: Sketch, t: float, z_front: float):
    from build123d import extrude
    return Pos(0, 0, z_front - t) * extrude(sk, t)


def socket_and_bulb(x: float, y: float):
    base = Pos(x, y, Z_CARRIER_FRONT)
    sock = base * (Pos(0, 0, flange_t / 2) * Box(flange_w, flange_len, flange_t)   # flange along Y, clear of the side cleats
                   + Cylinder(socket_od / 2, socket_h, align=(Align.CENTER, Align.CENTER, Align.MIN))
                   - Pos(0, 0, 6) * Cylinder(6.2, socket_h, align=(Align.CENTER, Align.CENTER, Align.MIN)))
    bulb = (Pos(x, y, 0) * Cylinder(6.0, 12.0, align=(Align.CENTER, Align.CENTER, Align.MAX))
            + Pos(x, y, BULB_GLOBE_Z) * Sphere(BULB_GLOBE_D / 2)
            + Pos(x, y, 0) * Cylinder(6.0, BULB_GLOBE_Z, align=(Align.CENTER, Align.CENTER, Align.MIN)))
    return sock, bulb


def walls():
    zc = (Z_FACE_BACK + Z_BACK_FRONT) / 2
    d = Z_FACE_BACK - Z_BACK_FRONT
    sides = [Pos(s * (W - WALL_T) / 2, 0, zc) * Box(WALL_T, H, d) for s in (-1, 1)]
    tb = [Pos(0, s * (H - WALL_T) / 2, zc) * Box(IN_W, WALL_T, d) for s in (-1, 1)]
    bottom = tb[0] - Pos(0, -(H - WALL_T) / 2, Z_BACK_FRONT + 30) * Cylinder(
        GLAND_D / 2, WALL_T * 2, rotation=(90, 0, 0))
    return sides[0], sides[1], tb[1], bottom


def cleats():
    zc = Z_FACE_BACK - CLEAT / 2
    return [Pos(s * (IN_W - CLEAT) / 2, 0, zc) * Box(CLEAT, IN_H, CLEAT) for s in (-1, 1)]


def electronics() -> dict:
    """Envelopes on the inside of the back panel: 5 SSR boards + controller in a 2 x 3 grid,
    5 V supply and mains terminal block below."""
    z0 = Z_BACK_FRONT + BOARD_STANDOFF
    gx = (IN_W - 2 * SSR_BOARD[0]) / 3
    xs = [-(gx + SSR_BOARD[0]) / 2, (gx + SSR_BOARD[0]) / 2]
    ys = [IN_H / 2 - 25 - SSR_BOARD[1] / 2 - k * (SSR_BOARD[1] + 25) for k in range(3)]
    out = {}
    slots = [(x, y) for y in ys for x in xs]
    for k, (x, y) in enumerate(slots[:SSR_BOARDS]):
        out[f"ssr_{k}"] = Pos(x, y, z0) * Box(*SSR_BOARD, align=(Align.CENTER, Align.CENTER, Align.MIN))
    x, y = slots[SSR_BOARDS]
    out["controller"] = Pos(x, y, z0) * Box(*CTRL_BOARD, align=(Align.CENTER, Align.CENTER, Align.MIN))
    yb = -IN_H / 2 + 40
    out["psu_5v"] = Pos(xs[1], yb, z0) * Box(*PSU_5V, align=(Align.CENTER, Align.CENTER, Align.MIN))
    out["mains_terminal"] = Pos(xs[0], yb, z0) * Box(*TERMINAL, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return out


def build() -> dict:
    parts = {
        "face": plate(face_sketch(), FACE_T, 0.0),
        "carrier": plate(carrier_sketch(), CARRIER_T, Z_CARRIER_FRONT),
        "back": plate(back_sketch(), BACK_T, Z_BACK_FRONT),
    }
    l, r, top, bottom = walls()
    parts.update(wall_left=l, wall_right=r, wall_top=top, wall_bottom=bottom)
    cl, cr = cleats()
    parts.update(cleat_left=cl, cleat_right=cr)
    socks, bulbs = zip(*(socket_and_bulb(x, y) for x, y in BULBS))
    parts["sockets"] = Compound(children=list(socks))
    parts["bulbs"] = Compound(children=list(bulbs))
    parts.update(electronics())
    return parts


PARTS = build()
CUTS = {"face": face_sketch(), "carrier": carrier_sketch()}   # laser-cut acrylic

def check() -> list[str]:
    """Pairwise interference between the solid parts (should be empty)."""
    names = [n for n in PARTS if n != "bulbs"]
    bad = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            v = (PARTS[a] & PARTS[b]).volume
            if v > 1e-3:
                bad.append(f"{a} x {b}: {v:.1f} mm3")
    return bad


try:  # build123d-mcp session: register everything for measure/render/export
    for name, p in PARTS.items():
        show(p, name)  # noqa: F821
    for name, s in CUTS.items():
        show(s, f"cut_{name}")  # noqa: F821
except NameError:
    pass
