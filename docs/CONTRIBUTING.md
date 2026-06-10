# Contributing & Development

Welcome to the Antimatter ecosystem! Antimatter is a community‑driven, open‑source companion app +
VS Code extension for Google's AntiGravity IDE.

!!! note "Community project"
    Antimatter is **NOT** affiliated with, endorsed by, or supported by Google.

## Repository layout

Antimatter is a monorepo with two shippable sub‑projects plus the docs site:

```text
antimatter/
├── extension/   # VS Code / AntiGravity extension (TypeScript)  → see Extension reference
├── android/     # Companion Android app (Kotlin / Compose)       → see Android reference
├── docs/        # MkDocs Material documentation (this site)
└── mkdocs.yml   # Docs site configuration
```

- [VS Code Extension Reference](EXTENSION.md)
- [Android App Reference](ANDROID.md)
- [WebSocket Protocol Reference](PROTOCOL.md)

## Prerequisites

- **Node.js 22+**
- **Android Studio** (Koala or newer)
- **Google AntiGravity IDE**

## Setting up the VS Code extension

```bash
cd extension
npm install        # install dependencies
npm run watch      # start the esbuild watcher
```

Then press **`F5`** in VS Code to launch an Extension Development Host with the bridge loaded.

| Task | Command |
|------|---------|
| Type‑check / lint | `npm run lint` (`tsc --noEmit`) |
| Build bundle | `npm run build` |
| Package `.vsix` | `npm run package` |

## Setting up the Android app

1. Open the `android/` directory in Android Studio.
2. Let Gradle sync and download dependencies.
3. Build and run the `app` configuration on an emulator or device.
4. *(Optional)* For Crashlytics in debug builds, add a valid `google-services.json` to
   `android/app/`.

| Task | Command |
|------|---------|
| Lint | `./gradlew lintDebug` |
| Build debug APK | `./gradlew assembleDebug` |
| Install debug build | `./gradlew installDebug` |

## Working on the documentation

The docs are built with [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/):

```bash
pip install mkdocs-material
mkdocs serve          # live preview at http://127.0.0.1:8000
mkdocs build --strict # verify there are no broken links/nav before pushing
```

Pages live in `docs/` and the navigation is defined in `mkdocs.yml`. On merge to `main`, the
[Deploy Documentation](https://github.com/saifmukhtar/antimatter/blob/main/.github/workflows/pages.yml)
workflow publishes the site to <https://antimatter.saifmukhtar.dev>.

## Submitting pull requests

1. Fork the repo and create your branch from `main`.
2. Run formatting and linting:
    - Extension: `npm run lint`
    - Android: `./gradlew lintDebug`
3. Add tests for any code that should be tested.
4. Open the pull request.

## Code style

We enforce standard TypeScript formatting (ESLint / Prettier) and Kotlin formatting (Ktlint).
Please configure your IDE to respect these rules.

See also the [Code of Conduct](https://github.com/saifmukhtar/antimatter/blob/main/CODE_OF_CONDUCT.md).
