# Fusion environment editor

## Working rule grid (draft, edited together)

This file is the current requirements record. It contains only instructions
given for this project and deliberately does **not** decide unresolved behaviour.
Its rules become non-negotiable only after explicit agreement.

## Current stage: find only

The first task is a read-only discovery action.

| Rule | Requirement |
|---|---|
| Tool | Create one standalone Python script in this repository. |
| Fusion discovery | Find `FusionLauncher.exe` for every locally installed Fusion version. |
| Active build | If a running Fusion application process (including `Fusion360.exe`) can be tied to one discovered deployment, identify that build and report the executable's Windows File/Product version. Do not guess from the newest version or the first filename match. |
| PhotoBooth discovery | Find the `PhotoBooth.xml` belonging to the active Fusion build. Exclude the similarly named Autodesk Inventor and Inventor Interoperability files. |
| Ambiguity | When the active build/file cannot be established from evidence, report all candidates and the reason instead of selecting one. |
| Side effects | This stage reads and reports only. It does not change XML, create backups, start Fusion, stop Fusion, or deploy anything. |

### Run the discovery action

```powershell
py fusion_environment_editor.py
```

The command reports the candidate paths in a concise form. For the complete,
machine-readable evidence report:

```powershell
py fusion_environment_editor.py --json
```

Both commands are read-only. The optional `--webdeploy-root` argument exists
only for a test/diagnostic copy of the bounded webdeploy directory; it does not
permit writes.

When the normal command cannot prove a running Fusion application belongs to
one discovered deployment, it displays a small Task Manager fallback dialog.
Choosing **Yes** asks for the exact copied `Fusion360.exe` path; choosing
**No**, Cancel, or retry cancellation selects nothing and performs no action.
The GUI path is not shown for `--json`, which remains unattended and
machine-readable.

## Working-model settings GUI

Run the GUI against the copied repository source:

```powershell
py photobooth_settings_gui.py
```

Its first dialog asks: **“Do you want to check or just test the current
functions?”** A base check uses the read-only finder and compares hashes; test
mode uses the repository copy directly. In both modes the interface displays
the large **CURRENT FILE IS NOT CHECKED AS CORRECT BASE** watermark.

The GUI creates [config/settings_catalog.json](config/settings_catalog.json):

- a one-to-one JSON tree of every element, text value, and attribute from
  [photoboothxml/PhotoBooth.xml](photoboothxml/PhotoBooth.xml);
- its current raw and working values, front-end labels/explanations, and
  fine-tuning histories;
- the source hash and unverified-base status.

It writes only JSON working profiles. It **does not write any PhotoBooth XML**.
The future **Accept and implement** button is intentionally informational until
the validated-copy transaction workflow has been agreed and implemented.

The known copied reference was taken from:

```text
C:\Users\johan\AppData\Local\Autodesk\webdeploy\pre-production\
a40f190f24413dd1bb4f1434f056c1379a3b5224\
Neutron\Server\Scene\Resources\Environments\PhotoBooth\PhotoBooth.xml
```

It is evidence for investigation, not proof that this is the currently active
file on every future Fusion installation.

## Later requested capabilities (not yet implementation rules)

These are the ideas to turn into explicit, testable rules after discovery works.

| ID | Requested capability | Decision still needed |
|---|---|---|
| C | Show all possible XML settings and their active values in a GUI. | Define which XML attributes count as an editable setting and how unsupported values appear. |
| D | Change a setting from first principles and make the result visible when it is checked. | Establish the actual Fusion reload/override behaviour on the selected build. |
| E | Accept a Fusion screenshot to validate a setting until a later Fusion version requires rediscovery of `PhotoBooth.xml`. | Define screenshot-to-setting evidence and revalidation rules. |
| F | Undo changes and preserve an `original_timestamp` XML copy. | Define backup location, retention, and exact restore confirmation. |
| G | For colour settings, present nearby settings as rectangles and give the chosen one a thick stroke. | Define the set of nearby settings and whether the preview is only illustrative. |
| H | Save settings as XML or JSON, while saving the actual XML into the Fusion workspace. | Define the profile format and the precise verified workspace target. |
| I | Include a “Fusion overrides” state for settings that do not visually take effect. | Define how a user records and revisits that finding. |
| J | Support multiple named saves such as “full contrast”, “better for render”, and “soft tone”. | Define profile names, contents, portability, and baseline compatibility. |

## Settings-grid draft

The requested grid, labels/explanations, and two-cube scalable preview are
captured for review in [docs/SETTINGS_GRID_DRAFT.md](docs/SETTINGS_GRID_DRAFT.md).
It is not implementation authorisation; its proposed groups remain pending
confirmation.

The draft OGS/RRT context, observed lighting values, and the signed
`ShadowColor` limitation are recorded in
[docs/RRT_OGS_LIGHTING_NOTES.md](docs/RRT_OGS_LIGHTING_NOTES.md).

## Explicitly not assumed

- No palette, colour values, profile names, Fusion refresh mechanism, or
  `PhotoBooth.xml` target is invented by the tool.
- A screenshot, XML write, or UI preview is not itself proof that Fusion uses a
  setting.
- No Autodesk installation file is changed until the active target and write
  rules are agreed.
