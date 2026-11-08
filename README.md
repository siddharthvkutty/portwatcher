<p align="center">
  <img src="assets/doc-pic.png" alt="PortWatcher" width="360">
</p>

<h1 align="center">PortWatcher</h1>

<p align="center">
  A clean desktop app for Linux that shows every active port on your machine,<br>
  which process owns it, and where it's talking to.
</p>

---

## Features

- **Live table of all sockets**, refreshed every 2 seconds, with your selection and scroll position kept
- **Port, protocol** (TCP / UDP / TCP6 / UDP6), **state**, **process name + PID**, **local and remote addresses**
- **Colour-coded states**: `LISTEN`, `ESTAB`, `TIME-WAIT`, `CLOSE-WAIT`, `UNCONN`
- **Filter** by text (port, process, IP...), by protocol, or show listening sockets only
- **Sort** by any column
- Dark theme, native GTK window, shows up in your app launcher

## Install

Download `installer.sh` from the [latest release](https://github.com/siddharthvkutty/portwatcher/releases/latest), then run it:

```bash
bash installer.sh
```

The installer works per-user and only asks for `sudo` if system packages are missing. It will:

1. Install dependencies (git, `ss`, Python GTK3 bindings) via `apt`, `dnf`, `pacman` or `zypper`
2. Clone this repo to `~/.local/share/portwatcher`
3. Add a `portwatcher` command to `~/.local/bin`
4. Add a **PortWatcher** entry and icon to your applications menu

Re-running the installer updates to the latest version.

## Uninstall

```bash
bash installer.sh --uninstall
```

## Run from source

```bash
git clone https://github.com/siddharthvkutty/portwatcher.git
cd portwatcher
python3 portwatcher.py
```

Requires Python 3, GTK 3 with PyGObject, and `ss` (from iproute2).

## Notes

- Without root, Linux only reveals the process for **your own** sockets. Other users' sockets show `—` for process and PID. Launch with `sudo portwatcher` to see everything.
- Under the hood it just parses `ss -tunap`, so what you see matches the command line.

## License

[MIT](LICENSE)
