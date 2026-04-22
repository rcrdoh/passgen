import threading
from passgencli._vendor import PySimpleGUI as sg

from passgencli.passgen import ImprovedMentalSeedGenerator
from passgencli.passgen_ui import open_window, modal_new_service, confirm_delete

gen = ImprovedMentalSeedGenerator()

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

def main():
    selected = None
    window, hint = open_window(gen.hints, selected)

    while True:
        event, values = window.read(timeout=300)

        if event in (sg.WIN_CLOSED, "Exit"):
            break

        # ── Sidebar: select service ───────────────────────────────────────
        if isinstance(event, str) and event.startswith("SVC_"):
            selected = event[4:]
            window.close()
            window, hint = open_window(gen.hints, selected)
            continue

        # ── New service ───────────────────────────────────────────────────
        if event == "NEW_SVC":
            result = modal_new_service(list(gen.hints.keys()))
            if result:
                name = result.pop("name")
                #gen.hints[name] = result
                #gen._save_hints()
                gen._save_hints(name, result)
                gen.hints[name] = result
                selected = name
                window.close()
                window, hint = open_window(gen.hints, selected)
            continue

        # ── Delete service ────────────────────────────────────────────────
        if event == "DEL_SVC":
            if not selected:
                sg.popup_quick_message("Select a service first.",
                                        background_color=PANEL, text_color=DANGER,
                                        font=FONT_SM, no_titlebar=True, auto_close_duration=2)
                continue
            if confirm_delete(selected):
                #del gen.hints[selected]
                #gen._save_hints()
                gen._delete_hints(selected)
                del gen.hints[selected]
                selected = None
                window.close()
                window, hint = open_window(gen.hints, selected)
            continue

        # ── Generate password ─────────────────────────────────────────────
        if event == "GENERATE" and hint:
            n_seeds = len(hint["seed_indices"])
            seeds   = [values.get(f"SEED_{i}", "").strip() for i in range(n_seeds)]

            if any(s == "" for s in seeds):
                window["STATUS"].update("⚠  Please fill in all seed fields.", text_color=WARNING)
                continue

            window["STATUS"].update("⏳  Generating…", text_color=MUTED)
            window["OUT_PW"].update("")
            window.refresh()

            def run_gen():
                try:
                    pw = gen.generate_password(
                        seeds,
                        hint["reference"],
                        hint["hash_method"],
                        hint.get("iterations") or 10000,
                    )
                    window["OUT_PW"].update(pw)
                    window["STATUS"].update("✓  Password ready. Copy it above.", text_color=SUCCESS)
                except Exception as e:
                    window["STATUS"].update(f"Error: {e}", text_color=DANGER)

            threading.Thread(target=run_gen, daemon=True).start()
            continue

        # ── Copy password ─────────────────────────────────────────────────
        if event == "COPY_PW":
            pw = values.get("OUT_PW", "").strip()
            if not pw:
                window["STATUS"].update("Nothing to copy yet.", text_color=WARNING)
                continue
            sg.clipboard_set(pw)
            window["STATUS"].update("✓  Copied to clipboard! Clears in 30s.", text_color=SUCCESS)

            def clear_clip():
                import time
                time.sleep(30)
                try:
                    if sg.clipboard_get() == pw:
                        sg.clipboard_set("")
                except Exception:
                    pass
            threading.Thread(target=clear_clip, daemon=True).start()

        if event == "COPY_PREV":
            pw = values.get("OUT_PREV", "").strip()
            if not pw:
                window["STATUS"].update("Nothing to copy yet.", text_color=WARNING)
                continue
            sg.clipboard_set(pw)
            window["STATUS"].update("✓  Copied to clipboard! Clears in 30s.", text_color=SUCCESS)

            def clear_clip():
                import time
                time.sleep(30)
                try:
                    if sg.clipboard_get() == pw:
                        sg.clipboard_set("")
                except Exception:
                    pass
            threading.Thread(target=clear_clip, daemon=True).start()

    window.close()

if __name__ == "__main__":
    main()
