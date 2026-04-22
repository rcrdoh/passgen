"""
passgen_ui.py — GUI front-end for ImprovedMentalSeedGenerator (passgen.py)
Place this file in the same directory as passgen.py and run it directly.
"""

from passgencli._vendor import PySimpleGUI as sg
#from passgen import ImprovedMentalSeedGenerator

# ─── Theme ────────────────────────────────────────────────────────────────────

sg.theme("DarkGrey13")

BG          = "#1A1A2E"
PANEL       = "#252538"
CARD        = "#2E2E48"
ACCENT      = "#00BFA5"
ACCENT_DIM  = "#00796B"
TEXT        = "#E8E8F8"
MUTED       = "#6B6B88"
DANGER      = "#EF5350"
SUCCESS     = "#66BB6A"
WARNING     = "#FFA726"

FONT        = ("Consolas", 11)
FONT_SM     = ("Consolas", 9)
FONT_LG     = ("Consolas", 14, "bold")
FONT_TITLE  = ("Consolas", 20, "bold")
FONT_MONO   = ("Courier New", 12)

sg.set_options(
    font=FONT,
    background_color=BG,
    text_color=TEXT,
    input_elements_background_color=CARD,
    input_text_color=TEXT,
    button_color=(BG, ACCENT),
    border_width=0,
)

#gen = ImprovedMentalSeedGenerator()

# ─── Reusable widget helpers ──────────────────────────────────────────────────

def lbl(text, color=None, font=None, pad=((0, 0), (6, 2)), bg=PANEL):
    return sg.Text(text, text_color=color or MUTED, font=font or FONT_SM,
                   background_color=bg, pad=pad)

def btn(label, key, color=None, size=(12, 1), pad=(4, 4), disabled=False):
    return sg.Button(label, key=key, size=size, pad=pad, disabled=disabled,
                     button_color=color or (BG, ACCENT), border_width=0, font=FONT_SM)

def sep(pad=((0, 0), (8, 8))):
    return sg.HorizontalSeparator(color=CARD, pad=pad)

def tag(text, color=ACCENT):
    return sg.Text(f" {text} ", font=FONT_SM, text_color=BG,
                   background_color=color, pad=((0, 4), 2))

# ─── Sidebar: saved services ──────────────────────────────────────────────────

def sidebar_rows(hints: dict, selected: str | None) -> list[list]:
    if not hints:
        return [[sg.Text("No saved services yet.", font=FONT_SM,
                          text_color=MUTED, background_color=BG, pad=(8, 4))]]
    rows = []
    for name in sorted(hints):
        h    = hints[name]
        bg   = ACCENT_DIM if name == selected else BG
        rows.append([
            sg.Button(
                f"  {name}",
                key=f"SVC_{name}",
                button_color=(TEXT, bg),
                font=FONT,
                size=(24, 1),
                border_width=0,
                pad=(0, 1),
            )
        ])
    return rows

def build_sidebar(hints, selected):
    return sg.Column(
        [
            [sg.Text("🔐 PASSGEN", font=FONT_TITLE, text_color=ACCENT,
                      background_color=BG, pad=((10, 0), (14, 6)))],
            [sg.Text("SAVED SERVICES", font=FONT_SM, text_color=MUTED,
                      background_color=BG, pad=((10, 0), (4, 4)))],
            [sg.Column(
                sidebar_rows(hints, selected),
                background_color=BG,
                scrollable=True, vertical_scroll_only=True,
                size=(196, 320), pad=(0, 0),
            )],
            [sep()],
            [btn("＋  New Service", "NEW_SVC", size=(20, 1), pad=((10, 0), 4))],
            [btn("🗑  Delete",      "DEL_SVC", size=(20, 1),
                  color=(BG, DANGER), pad=((10, 0), 4))],
            [sep()],
            [sg.Text("Seeds are NEVER stored.", font=FONT_SM,
                      text_color=MUTED, background_color=BG, pad=((10, 0), (4, 2)))],
            [sg.Text("Only hints are saved.",   font=FONT_SM,
                      text_color=MUTED, background_color=BG, pad=((10, 0), (0, 10)))],
        ],
        background_color=BG,
        size=(210, 540),
        pad=(0, 0),
        vertical_alignment="top",
    )

# ─── Right panel: service detail + generate ──────────────────────────────────

def build_detail(hint: dict | None, service: str | None):
    """Right-hand panel. If hint is None, show the empty state."""
    if hint is None:
        return sg.Column(
            [[sg.Text("Select a service or create one.",
                       font=("Consolas", 12), text_color=MUTED,
                       background_color=PANEL, justification="center",
                       expand_x=True, pad=(0, 220))]],
            background_color=PANEL, expand_x=True, expand_y=True, pad=(0, 0),
        )

    method      = hint.get("hash_method", "pbkdf2")
    iterations  = hint.get("iterations") or 10000
    seed_idxs   = hint.get("seed_indices", [])
    reference   = hint.get("reference", "")
    prev_flag   = False if hint.get("prev", "") == "" else True
    n_seeds     = len(seed_idxs)

    METHOD_COLORS = {"simple": WARNING, "hmac": ACCENT, "pbkdf2": SUCCESS}
    method_color  = METHOD_COLORS.get(method, MUTED)

    # Seed input rows
    seed_rows = []
    for i, idx in enumerate(seed_idxs):
        seed_rows.append([
            lbl(f"SEED  #{idx}", pad=((16, 0), (6, 2))),
        ])
        seed_rows.append([
            sg.InputText("", key=f"SEED_{i}", size=(42, 1), font=FONT_MONO,
                          password_char="•", pad=((16, 8), (0, 6))),
        ])

    layout = [
        # ── Header ────────────────────────────────────────────────────────
        [sg.Text(service, font=FONT_LG, text_color=ACCENT,
                  background_color=PANEL, pad=((16, 0), (14, 2)))],
        [sg.Text("", background_color=PANEL, pad=((16, 0), 0), expand_x=True),
         tag(method.upper(), method_color),
         tag(f"SEEDS: {seed_idxs}"),
         tag(f"REF: {reference}"),
         tag(f"PREV: {prev_flag}")],
        [sg.Text("", background_color=PANEL, pad=((0, 16), 0))],
        [sep()],

        # ── Previous Passwords ───────────────────────────────────────────────────
        
        *(
            [
                [lbl("PREVIOUS PASSWORD AVAILABLE", color=TEXT, pad=((16, 0), (8, 4)))],
                [
                sg.InputText(hint.get('prev', ''), key="OUT_PREV", size=(42, 1), font=FONT_MONO,
                             readonly=True, pad=((16, 8), (0, 6)),
                             background_color=CARD, text_color=MUTED),
                btn("Copy", "COPY_PREV", size=(6, 1))
                ]
            ] 
            if prev_flag else []
        ),

        # ── Seed inputs ───────────────────────────────────────────────────
        [lbl("ENTER YOUR SEEDS  (never stored, never logged)",
              color=TEXT, pad=((16, 0), (8, 4)))],
        *seed_rows,

        [sep()],

        # ── Generate button + output ──────────────────────────────────────
        [sg.Text("", background_color=PANEL, expand_x=True),
         btn("⚡  Generate Password", "GENERATE", size=(22, 1), pad=((0, 16), 6))],
        [lbl("GENERATED PASSWORD", pad=((16, 0), (10, 2)))],
        [sg.InputText("", key="OUT_PW", size=(42, 1), font=FONT_MONO,
                       readonly=True, pad=((16, 8), (0, 6)),
                       background_color=CARD, text_color=ACCENT),
         btn("Copy", "COPY_PW", size=(6, 1))],

        [sg.Text("", key="STATUS", font=FONT_SM, text_color=SUCCESS,
                  background_color=PANEL, pad=((16, 0), (2, 14)), size=(50, 1))],
    ]

    return sg.Column(layout, background_color=PANEL,
                     expand_x=True, expand_y=True, pad=(0, 0))

# ─── Full window layout ───────────────────────────────────────────────────────

def build_layout(hints, selected, hint):
    return [[
        build_sidebar(hints, selected),
        sg.VerticalSeparator(color=ACCENT_DIM, pad=(0, 0)),
        build_detail(hint, selected),
    ]]

def open_window(hints, selected):
    hint   = hints.get(selected) if selected else None
    layout = build_layout(hints, selected, hint)
    win    = sg.Window(
        "PassGen UI",
        layout,
        size=(780, 540),
        background_color=BG,
        finalize=True,
        resizable=False,
    )
    return win, hint

# ─── Modal: new service ───────────────────────────────────────────────────────

def modal_new_service(existing_names: list[str]) -> dict | None:
    """Collect hint params for a brand-new service. Returns hint dict or None."""
    layout = [
        [sg.Text("New Service", font=FONT_LG, text_color=ACCENT,
                  background_color=PANEL, pad=(14, 12))],
        [sep()],

        [lbl("SERVICE NAME", pad=((14, 0), (6, 2)))],
        [sg.Input("", key="svc_name", size=(34, 1), pad=((14, 8), (0, 8)))],

        [lbl("REFERENCE  (e.g. github2024)", pad=((14, 0), (6, 2)))],
        [sg.Input("", key="svc_ref", size=(34, 1), pad=((14, 8), (0, 8)))],

        [lbl("SEED INDICES  (comma-separated, e.g. 1,3,5)", pad=((14, 0), (6, 2)))],
        [sg.Input("", key="svc_seeds", size=(34, 1), pad=((14, 8), (0, 8)))],

        [lbl("HASH METHOD", pad=((14, 0), (6, 2)))],
        [sg.Radio("Simple  (SHA-256)",        "METHOD", key="m_simple",
                   background_color=PANEL, text_color=TEXT, font=FONT_SM,
                   pad=((14, 0), 2)),
         sg.Radio("HMAC-SHA-256",             "METHOD", key="m_hmac",
                   background_color=PANEL, text_color=TEXT, font=FONT_SM,
                   pad=((14, 0), 2)),
         sg.Radio("PBKDF2  (recommended)",    "METHOD", key="m_pbkdf2",
                   default=True, background_color=PANEL, text_color=TEXT,
                   font=FONT_SM, pad=((14, 0), 2))],

        [lbl("PBKDF2 ITERATIONS", pad=((14, 0), (8, 2)))],
        [sg.Input("10000", key="svc_iter", size=(12, 1), pad=((14, 8), (0, 10)))],

        [sep()],
        [sg.Text("", background_color=PANEL, expand_x=True),
         btn("Save", "m_SAVE", size=(8, 1)),
         btn("Cancel", "m_CANCEL", color=(TEXT, MUTED), size=(8, 1)),
         sg.Text("", background_color=PANEL, pad=((0, 12), 0))],
        [sg.Text("", key="m_err", font=FONT_SM, text_color=DANGER,
                  background_color=PANEL, pad=((14, 0), (2, 8)), size=(40, 1))],
    ]

    win = sg.Window("New Service", layout, modal=True, background_color=PANEL,
                    finalize=True, keep_on_top=True)
    while True:
        ev, vals = win.read()
        if ev in (sg.WIN_CLOSED, "m_CANCEL"):
            win.close(); return None

        if ev == "m_SAVE":
            name = vals["svc_name"].strip()
            ref  = vals["svc_ref"].strip()
            raw_seeds = vals["svc_seeds"].strip()

            if not name:
                win["m_err"].update("Service name is required."); continue
            if name in existing_names:
                win["m_err"].update("A service with that name already exists."); continue
            if not ref:
                win["m_err"].update("Reference is required."); continue
            if not raw_seeds:
                win["m_err"].update("Seed indices are required."); continue

            try:
                idxs = [int(x.strip()) for x in raw_seeds.split(",")]
            except ValueError:
                win["m_err"].update("Seed indices must be numbers (e.g. 1,3,5)"); continue

            method = ("simple" if vals["m_simple"] else
                      "hmac"   if vals["m_hmac"]   else "pbkdf2")
            try:
                iters = int(vals["svc_iter"]) if method == "pbkdf2" else None
            except ValueError:
                win["m_err"].update("Iterations must be a number."); continue

            win.close()
            return {
                "name":         name,
                "reference":    ref,
                "seed_indices": idxs,
                "hash_method":  method,
                "iterations":   iters,
            }

# ─── Modal: confirm delete ────────────────────────────────────────────────────

def confirm_delete(name: str) -> bool:
    layout = [
        [sg.Text(f'Delete "{name}"?', font=("Consolas", 12),
                  text_color=DANGER, background_color=PANEL, pad=(16, 14))],
        [sg.Text("The hint will be removed. Seeds are unaffected.",
                  text_color=MUTED, background_color=PANEL, font=FONT_SM,
                  pad=((16, 0), (0, 14)))],
        [sg.Text("", background_color=PANEL, expand_x=True),
         btn("Delete", "YES", color=(BG, DANGER), size=(8, 1)),
         btn("Cancel", "NO",  color=(TEXT, MUTED), size=(8, 1)),
         sg.Text("", background_color=PANEL, pad=((0, 12), 0))],
    ]
    win = sg.Window("Confirm", layout, modal=True, background_color=PANEL,
                    finalize=True, keep_on_top=True)
    ev, _ = win.read()
    win.close()
    return ev == "YES"
