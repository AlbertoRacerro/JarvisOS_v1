# Starting The Local UI

JarvisOS is still a local developer build. The `.cmd` files in the repository root are convenience launchers for Windows File Explorer.

## One-Click Start

Double-click:

```text
Start-JarvisOS.cmd
```

This opens the backend and frontend in separate command windows:

- backend: `http://localhost:8000`
- frontend: `http://localhost:5173`

The frontend launcher opens the browser to:

```text
http://localhost:5173
```

after a short delay.

## Start Services Separately

To start only the backend, double-click:

```text
Start-JarvisOS-Backend.cmd
```

To start only the frontend, double-click:

```text
Start-JarvisOS-Frontend.cmd
```

These wrappers call the existing PowerShell scripts in `scripts/`.

## Prerequisites

Backend:

- Python 3.11 or newer.

Frontend:

- Node.js LTS.
- npm, installed with Node.js.

If Node.js or npm is missing, the launcher prints a clear message and stops. Install Node.js LTS from the official site:

```text
https://nodejs.org/
```

After installing Node.js, reopen the launcher from File Explorer or open a fresh terminal so PATH changes are visible.

The launchers do not download installers, run installers, or modify system PATH.

## Initialize The Database

Backend startup initializes the SQLite database automatically. To initialize it manually without starting the server, run:

```powershell
.\scripts\init-database.ps1
```

The default runtime data root remains:

```text
C:\JarvisOS
```

The repository folder and runtime data root are separate concepts.
