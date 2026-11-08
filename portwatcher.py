#!/usr/bin/env python3
"""PortWatcher: live view of active network sockets (GTK3, reads `ss`)."""
import re
import subprocess
from pathlib import Path

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, GLib, Gtk  # noqa: E402

COLORS = {"LISTEN": "#5eead4", "ESTAB": "#86efac", "TIME-WAIT": "#fcd34d",
          "CLOSE-WAIT": "#fda4af", "UNCONN": "#94a3b8"}
LISTENING = ("LISTEN", "UNCONN")
# store columns
PORT, PROTO, STATE, PROC, LOCAL, REMOTE, COLOR, PID = range(8)

CSS = b"""
window, .background { background: #0f1117; }
headerbar { background: #151821; border: none; border-bottom: 1px solid #232838; box-shadow: none; color: #e6e9f2; }
headerbar .title { font-weight: 700; letter-spacing: 0.5px; }
headerbar .subtitle { color: #7d869c; }
entry { background: #1b1f2b; color: #e6e9f2; border: 1px solid #2a3040; border-radius: 8px; min-width: 260px; }
combobox button, checkbutton { color: #c9cfdf; }
treeview.view { background: #0f1117; color: #d7dbe8; font-size: 13px; }
treeview.view:selected { background: #26304d; color: #ffffff; }
treeview.view header button { background: #151821; color: #7d869c; border: none; border-radius: 0;
  border-bottom: 1px solid #232838; padding: 9px 10px; font-weight: 700; font-size: 11px; }
scrollbar slider { background: #2a3040; border-radius: 6px; }
"""


def split_addr(s):
    host, _, port = s.rpartition(":")
    return host.strip("[]").split("%")[0] or "*", port


def parse(line):
    """One `ss -H -tunap` line -> (key, row) or None."""
    f = line.split(None, 6)
    if len(f) < 6:
        return None
    proto, state, _, _, local, peer = f[:6]
    lh, lp = split_addr(local)
    rh, rp = split_addr(peer)
    # ponytail: only the first process of a shared socket is shown
    m = re.search(r'\("([^"]+)",pid=(\d+)', f[6]) if len(f) > 6 else None
    name, pid = (m[1], int(m[2])) if m else ("—", 0)
    remote = "—" if rp in ("*", "0") else (f"[{rh}]" if ":" in rh else rh) + ":" + rp
    if ":" in lh:
        proto += "6"
    row = [int(lp) if lp.isdigit() else 0, proto.upper(), state, name, lh, remote,
           COLORS.get(state, "#cbd5e1"), pid]
    return (proto, local, peer, pid), row


def scan():
    out = subprocess.run(["ss", "-H", "-tunap"], capture_output=True, text=True, timeout=5).stdout
    return [r for r in map(parse, out.splitlines()) if r]


class Win(Gtk.Window):
    def __init__(self):
        super().__init__(title="PortWatcher")
        self.set_default_size(1100, 640)
        self.iters = {}

        hb = Gtk.HeaderBar(show_close_button=True, title="PortWatcher")
        self.set_titlebar(hb)
        self.search = Gtk.SearchEntry(placeholder_text="Filter by port, process, IP…")
        self.proto = Gtk.ComboBoxText()
        for p in ("All", "TCP", "UDP"):
            self.proto.append_text(p)
        self.proto.set_active(0)
        self.listen = Gtk.CheckButton(label="Listening only")
        hb.pack_end(self.search)
        hb.pack_start(self.proto)
        hb.pack_start(self.listen)

        self.store = Gtk.ListStore(int, str, str, str, str, str, str, int)
        self.filter = self.store.filter_new()
        self.filter.set_visible_func(self.visible)
        self.sort = Gtk.TreeModelSort(model=self.filter)
        self.sort.set_sort_column_id(PORT, Gtk.SortType.ASCENDING)
        tree = Gtk.TreeView(model=self.sort)

        for title, col, mono in (("PORT", PORT, True), ("PROTOCOL", PROTO, False),
                                 ("STATE", STATE, False), ("PROCESS", PROC, False),
                                 ("PID", PID, True), ("LOCAL ADDRESS", LOCAL, True),
                                 ("REMOTE ADDRESS", REMOTE, True)):
            r = Gtk.CellRendererText(xpad=10, ypad=7)
            if mono:
                r.set_property("family", "monospace")
            c = Gtk.TreeViewColumn(title, r)
            if col in (PORT, PID):  # ints: show 0 as a dash
                c.set_cell_data_func(r, lambda _c, cell, m, it, k: cell.set_property(
                    "text", str(m[it][k]) if m[it][k] else "—"), col)
            else:
                c.add_attribute(r, "text", col)
            if col == STATE:
                c.add_attribute(r, "foreground", COLOR)
            c.set_sort_column_id(col)
            c.set_resizable(True)
            c.set_expand(col in (PROC, REMOTE))
            tree.append_column(c)

        sw = Gtk.ScrolledWindow()
        sw.add(tree)
        self.add(sw)

        self.search.connect("search-changed", lambda *_: self.filter.refilter())
        self.proto.connect("changed", lambda *_: self.filter.refilter())
        self.listen.connect("toggled", lambda *_: self.filter.refilter())
        self.hb = hb
        self.refresh()
        GLib.timeout_add_seconds(2, self.refresh)

    def visible(self, model, it, _):
        r = model[it]
        p = self.proto.get_active_text()
        if p != "All" and not r[PROTO].startswith(p):
            return False
        if self.listen.get_active() and r[STATE] not in LISTENING:
            return False
        q = self.search.get_text().lower()
        return not q or q in " ".join(str(r[i]) for i in (PORT, PROTO, STATE, PROC, PID, LOCAL, REMOTE)).lower()

    def refresh(self):
        try:
            rows = scan()
        except (OSError, subprocess.SubprocessError):
            return True
        seen = {k for k, _ in rows}
        for k, row in rows:  # update in place so selection/scroll survive
            if k in self.iters:
                self.store.set_value(self.iters[k], STATE, row[STATE])
                self.store.set_value(self.iters[k], COLOR, row[COLOR])
            else:
                self.iters[k] = self.store.append(row)
        for k in set(self.iters) - seen:
            self.store.remove(self.iters.pop(k))
        n = sum(1 for _, r in rows if r[STATE] in LISTENING)
        self.hb.set_subtitle(f"{n} listening · {len(rows)} sockets")
        return True


def main():
    GLib.set_prgname("portwatcher")  # matches portwatcher.desktop so the dock shows our icon
    GLib.set_application_name("PortWatcher")
    icon = Path(__file__).resolve().parent / "assets" / "portwatcher.png"
    if icon.exists():
        Gtk.Window.set_default_icon_from_file(str(icon))
    Gtk.Settings.get_default().set_property("gtk-application-prefer-dark-theme", True)
    prov = Gtk.CssProvider()
    prov.load_from_data(CSS)
    Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), prov,
                                             Gtk.STYLE_PROVIDER_PRIORITY_USER)
    w = Win()
    w.connect("destroy", Gtk.main_quit)
    w.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()
