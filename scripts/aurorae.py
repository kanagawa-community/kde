"""Aurorae window decoration: decoration.svg, one SVG per button, and the rc file.

Element names follow kwin's aurorae engine (/usr/share/kwin/aurorae/*.qml):
FrameSvg pieces "<prefix>-topleft" ... "-center", and button states
"active", "hover", "pressed" (also shown while toggled), "inactive", "deactivated".
"""

P = 12  # shadow padding
R = 8  # titlebar corner radius
T = 32  # titlebar height: TitleEdgeTop + TitleHeight + TitleEdgeBottom
M = P + R  # svg margin of side and bottom pieces; the part past the rc border sits under the window
SHADOW_ALPHA = 0.45

# button file -> (dot color role, glyph path in a 16x16 box)
BUTTONS = {
    "close": ("term.red", "M5.5 5.5 10.5 10.5M10.5 5.5 5.5 10.5"),
    "maximize": ("term.green", "M5 8H11M8 5V11"),
    "restore": ("term.green", "M5.5 5.5H10.5V10.5H5.5Z"),
    "minimize": ("term.yellow", "M5 8H11"),
    "alldesktops": ("term.blue", "M6.5 8A1.5 1.5 0 1 0 9.5 8 1.5 1.5 0 1 0 6.5 8Z"),
    "keepabove": ("term.blue", "M5.5 9.5 8 7 10.5 9.5"),
    "keepbelow": ("term.blue", "M5.5 6.5 8 9 10.5 6.5"),
    "shade": ("term.blue", "M5 6H11"),
    "help": ("term.blue", "M6.5 6.5A1.5 1.5 0 1 1 8.6 7.9C8.2 8.1 8 8.4 8 9M8 10.75V11"),
}


def hexify(rgb):
    return "#" + "".join(f"{int(c):02x}" for c in rgb.split(","))


def _rect(x, y, w, h, fill):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}"/>'


class _Sheet:
    """Collects gradients and pieces; every piece sits at the origin, kwin renders them by id."""

    def __init__(self, shadow):
        self.shadow, self.defs, self.parts, self.n = shadow, [], [], 0

    def _grad(self, tag, attrs, stops):
        self.n += 1
        gid = f"g{self.n}"
        s = "".join(
            f'<stop offset="{o}" stop-color="{self.shadow}" stop-opacity="{a:.3f}"/>' for o, a in stops
        )
        self.defs.append(f'<{tag} id="{gid}" gradientUnits="userSpaceOnUse" {attrs}>{s}</{tag}>')
        return f"url(#{gid})"

    def linear(self, x1, y1, x2, y2):
        """Shadow fading from (x1, y1), at the window edge, to nothing at (x2, y2)."""
        a = SHADOW_ALPHA
        return self._grad(
            "linearGradient", f'x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"', [(0, a), (0.4, a * 0.35), (1, 0)]
        )

    def radial(self, cx, cy, r0):
        a, k = SHADOW_ALPHA, r0 / (r0 + P)
        return self._grad(
            "radialGradient",
            f'cx="{cx}" cy="{cy}" r="{r0 + P}"',
            [(k, a), (k + (1 - k) * 0.4, a * 0.35), (1, 0)],
        )

    def piece(self, pid, w, h, *shapes):
        # The transparent rect pins the element's bounds to the full piece size.
        self.parts.append(f'<g id="{pid}">{_rect(0, 0, w, h, "none")}{"".join(shapes)}</g>')

    def frame(self, prefix, fill):
        s = self
        top_h, inner = P + T, M - P
        s.piece(f"{prefix}-center", 1, 1, _rect(0, 0, 1, 1, fill))
        s.piece(f"{prefix}-top", 1, top_h, _rect(0, 0, 1, P, s.linear(0, P, 0, 0)), _rect(0, P, 1, T, fill))
        s.piece(f"{prefix}-left", M, 1, _rect(0, 0, P, 1, s.linear(P, 0, 0, 0)), _rect(P, 0, inner, 1, fill))
        s.piece(f"{prefix}-right", M, 1, _rect(inner, 0, P, 1, s.linear(inner, 0, M, 0)), _rect(0, 0, inner, 1, fill))
        s.piece(
            f"{prefix}-bottom", 1, M, _rect(0, 0, 1, inner, fill), _rect(0, inner, 1, P, s.linear(0, inner, 0, M))
        )
        s.piece(
            f"{prefix}-topleft",
            M,
            top_h,
            _rect(0, 0, M, M, s.radial(M, M, R)),
            _rect(0, M, P, top_h - M, s.linear(P, 0, 0, 0)),
            f'<path d="M{P} {top_h}V{M}A{R} {R} 0 0 1 {M} {P}V{top_h}Z" fill="{fill}"/>',
        )
        s.piece(
            f"{prefix}-topright",
            M,
            top_h,
            _rect(0, 0, M, M, s.radial(0, M, R)),
            _rect(inner, M, P, top_h - M, s.linear(inner, 0, M, 0)),
            f'<path d="M0 {P}A{R} {R} 0 0 1 {inner} {M}V{top_h}H0Z" fill="{fill}"/>',
        )
        s.piece(
            f"{prefix}-bottomleft",
            M,
            M,
            _rect(P, 0, inner, inner, fill),
            _rect(0, 0, P, inner, s.linear(P, 0, 0, 0)),
            _rect(P, inner, inner, P, s.linear(0, inner, 0, M)),
            _rect(0, inner, P, P, s.radial(P, inner, 0)),
        )
        s.piece(
            f"{prefix}-bottomright",
            M,
            M,
            _rect(0, 0, inner, inner, fill),
            _rect(inner, 0, P, inner, s.linear(inner, 0, M, 0)),
            _rect(0, inner, inner, P, s.linear(0, inner, 0, M)),
            _rect(inner, inner, P, P, s.radial(inner, inner, 0)),
        )

    def svg(self):
        return (
            '<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64">\n'
            f"<defs>{''.join(self.defs)}</defs>\n" + "\n".join(self.parts) + "\n</svg>\n"
        )


def _button(dot, glyph, ink, inactive, disabled):
    def state(sid, color, with_glyph, dim=False):
        g = (
            f'<path d="{glyph}" fill="none" stroke="{ink}" stroke-width="1.5" '
            'stroke-linecap="round" stroke-linejoin="round"/>'
            if with_glyph
            else ""
        )
        shade = f'<circle cx="8" cy="8" r="7.5" fill="{ink}" fill-opacity="0.3"/>' if dim else ""
        return f'<g id="{sid}-center">{_rect(0, 0, 16, 16, "none")}<circle cx="8" cy="8" r="7.5" fill="{color}"/>{shade}{g}</g>'

    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16">\n'
        + "\n".join(
            [
                state("active", dot, False),
                state("hover", dot, True),
                state("pressed", dot, True, dim=True),
                state("inactive", inactive, False),
                state("deactivated", disabled, False),
            ]
        )
        + "\n</svg>\n"
    )


def files(theme_id, r):
    """Return {file name: text} for the theme folder `theme_id` (its rc must be named after it)."""
    h = {k: hexify(v) for k, v in r.items()}
    sheet = _Sheet(h["term.black"])
    # Same as the color scheme's Header and Header[Inactive], which Breeze uses for titlebars.
    sheet.frame("decoration", h["ui.bg"])
    sheet.frame("decoration-inactive", h["ui.bg_m3"])
    out = {"decoration.svg": sheet.svg()}
    for name, (role, glyph) in BUTTONS.items():
        out[f"{name}.svg"] = _button(h[role], glyph, h["ui.bg_m3"], h["ui.nontext"], h["ui.bg_p2"])
    out[f"{theme_id}rc"] = f"""[General]
ActiveTextColor={r['ui.fg']}
InactiveTextColor={r['ui.fg_dim']}
UseTextShadow=false
Shadow=true
TitleAlignment=Center
TitleVerticalAlignment=Center
Animation=150
LeftButtons=M
RightButtons=IAX

[Layout]
PaddingTop={P}
PaddingBottom={P}
PaddingLeft={P}
PaddingRight={P}
BorderLeft=2
BorderRight=2
BorderBottom=2
TitleEdgeTop=6
TitleEdgeBottom=6
TitleEdgeLeft=8
TitleEdgeRight=8
TitleEdgeTopMaximized=6
TitleEdgeBottomMaximized=6
TitleEdgeLeftMaximized=8
TitleEdgeRightMaximized=8
TitleHeight={T - 12}
TitleBorderLeft=8
TitleBorderRight=8
ButtonWidth=16
ButtonHeight=16
ButtonMarginTop=2
ButtonSpacing=6
ExplicitButtonSpacer=10
"""
    return out
