---
name: electron-desktop
description: Electron desktop apps with secure main, preload and renderer processes
triggers: [electron, desktop, ipc, preload, tray, renderer, bundler, "main process", "desktop app"]
---
- Keep three areas apart: `main/` for the app lifecycle and native APIs, `preload/` for the bridge, `renderer/` for the UI.
- Enable `contextIsolation`, disable `nodeIntegration`, and expose only narrow functions with `contextBridge`.
- Validate every IPC message in the main process. Name channels by feature, for example `files:read`.
- Run long tasks in the main process or a utility process and report progress through IPC events.
- Package with electron-builder and keep the app version in one place.
