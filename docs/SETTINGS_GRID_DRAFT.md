# Settings grid and viewport draft

## Status

This is a requirements draft, not an implementation specification yet.

- The **Find only** stage remains read-only and is complete.
- No settings grid, editable XML settings, profile, backup, or apply behaviour
  is authorised by this document.
- Change this draft directly, then confirm the parts that should become rules.

## Data-source rule

When a later edit/apply/check/confirm workflow exists:

- the settings grid must read from the validated copy produced by that
  confirmed workflow;
- the validated copy must identify its source `PhotoBooth.xml`, version, and
  hash;
- the grid must not silently return to an arbitrary deployment XML after a
  confirmed copy exists.

For this requirements draft only, the real data snapshot appended below is read
from the currently active, read-only discovered Fusion resource. This is an
explicit temporary exception until the validated-copy workflow is implemented.

## Goal

Present all recognisable visual settings from the selected `PhotoBooth.xml` in a
clear grid, with human-readable guidance and a context preview.

The in-scope settings are:

- colours;
- opacity / alpha;
- stroke or line width;
- related display properties that can be safely identified as visual.

Values that cannot be safely recognised as visual settings remain visible as
raw XML data, but are not treated as colours.

## Source identity and catalog

Every row retains its exact XML identity:

```text
/PhotoBooth[1]/SketchLineColor[1]/@ARGB
```

That identity is secondary detail, not the primary grid label. It prevents two
similarly named or repeated XML attributes from being confused.

The repository will contain one shared source catalog:

```text
config/settings_catalog.json
```

The catalog will:

- be keyed by exact XML identity;
- support differences or missing settings between Fusion versions;
- store the proposed human explanation;
- save a user-edited explanation immediately when it is changed;
- hold the visual-preview mapping for a setting once it is known.

## Grid

The grid is Excel-like, with rows grouped before their short XML labels.

For each row:

1. **Short XML label**
   - The XML element/attribute label that is short enough in its group.
   - Examples: `LineColorRGBA`, `HaloWidth`, `ARGB`.
   - The full indexed XML identity is available as secondary detail.

2. **Explanation**
   - An initial plain-language explanation proposed by the application.
   - You can edit this wording.
   - Your edit saves on the fly to `config/settings_catalog.json`.

3. **Colour**
   - A coloured cell / swatch, not an important colour-number display.
   - Clicking the swatch opens a colour picker.
   - A colour value is shown only when useful as secondary detail.

4. **Opacity**
   - A separate editable cell when the setting has alpha / opacity.
   - Not displayed for settings without an applicable alpha channel.

5. **Stroke or line width**
   - A separate editable cell when the XML property is a line/stroke width.
   - Not displayed for settings without an applicable width.

6. **Other visual property**
   - A clear, type-appropriate cell for recognised visual values that are not
     colour, opacity, or width.

## Viewport preview

The preview has a logical design size of **3140 × 2100**.

- It scales to the available application window.
- It preserves the 3140:2100 aspect ratio.
- It is not a fixed monitor-size requirement.
- It must not distort the preview geometry.

Both contexts appear at the same time:

- **Design-mode cube**
  - A cube represented by edges only.
  - Shows the environment/design context, including selection and highlight
    states where applicable.

- **Sketch-mode cube**
  - A cube represented by sketch geometry.
  - Shows sketch-line, constraint, dimension, and related sketch states where
    applicable.

When a row is selected:

- Apply that setting only to the matching semantic preview feature.
  - Example: a sketch-line setting affects sketch geometry.
  - Example: a selection setting affects selected design-mode edges.
  - Example: a grid/background setting affects the corresponding environment
    feature.
- Keep other preview features in their respective context.
- If a safe semantic mapping does not exist yet:
  - do not pretend the setting affects one of the cubes;
  - show a labelled callout for that selected setting;
  - emphasise the callout with a thick outline.

The preview is a design aid. It is not proof that Fusion itself renders or
honours a setting.

## Proposed groups — pending confirmation

The following group structure is a proposal only. It exists so the short XML
label in column 1 has useful context.

1. **Background and grids**
   - Backgrounds
   - Ground / layout grids
   - Grid transparency

2. **Sketch**
   - Sketch geometry
   - Constraints and inference
   - Dimensions and text
   - Construction and projected geometry

3. **Selection and highlighting**
   - Object selection
   - Component selection
   - Hover / highlight
   - Error highlighting

4. **Work geometry and manipulators**
   - Origin axes
   - Work planes and axes
   - Manipulator axes and planes

5. **Model, measurement, and joint previews**
   - Body and edge previews
   - Measure dimensions
   - Joint states

6. **Simulation**
   - Simulation preview colours
   - Progress / result display colours

7. **Lighting and render**
   - Environment lighting
   - Render preview backgrounds
   - Lighting colours that are normalised visual values

8. **Unclassified**
   - Visual values that need a human explanation or preview mapping before
     moving into a more specific group.

## Confirmed grid and image-frame interactions

### Visible hierarchy

- Omit the redundant `PhotoBooth` root. All identified visual settings are
  descendants of that root.
- Use a collapsible **Setting** tree with at most two visible levels beneath a
  group heading.
- Collapse intermediate XML containers that would otherwise create a third
  level.

Example:

```text
Lighting and render
  OGS Lighting / Light
    Color
    ShadowColor
```

- Show a short XML identity relative to the expanded tree branch.
- Keep the canonical indexed XML identity in a detail/tooltip view.
- Retain a visible, editable **Short label** column containing raw labels such
  as `ARGB`, `RGB`, `Color`, or `ShadowColor`.
- Do not display a generic recognised-type/colour column. Type remains internal
  metadata used for validation and rendering.
- Leave **Mode** blank until an actual Fusion validation establishes where a
  setting is visible.

### Metadata editing

- The editable source catalog is repository-tracked
  `config/settings_catalog.json`.
- Short label and explanation edits save immediately to that catalog.
- Every front-end catalog entry is keyed by exact XML identity. Editing text for
  one row changes only that row, even when other rows use the same raw label.
- Front-end catalog data is never written into `PhotoBooth.xml`.
- Group placement is fixed for now; the grid does not support moving rows or
  creating groups.
- Ctrl+Z undoes catalog/UI edits in the current application session only.
- Ctrl+Y and Ctrl+Shift+Z redo current-session edits.

### Working values

- Raw values remain visible in the grid.
- Normalised editable values can be changed in an in-memory working model and
  previewed immediately.
- This stage must not write a Fusion XML file or a validated-copy file.
- A raw numeric cell allows temporary/incomplete text while being edited.
- Enter, Tab, or leaving a raw numeric cell validates and commits its value.
- Invalid committed text restores the previous valid value.
- Signed lighting `Direction` vectors appear as advanced read-only rows.
- Signed `OGSLighting/Light/@ShadowColor` appears as advanced, read-only, and
  unverified until Fusion testing establishes its meaning.

### View cells and image frame

- A normal colour displays a swatch.
- Opacity displays a transparency sample.
- Stroke/line width displays a line sample.
- An unverified signed/special value displays a clearly marked unknown cell.
- Hovering a row previews it temporarily in the image frame.
- Clicking a row creates the persistent selected preview.
- When hover ends, the frame returns to the persistent selected preview.
- The selected semantic feature receives a fixed high-contrast thick outline
  plus a compact label/callout, independent of the setting's own colour.
- The logical 3140 × 2100 image frame scales to the available window without
  distorting its aspect ratio.

### Image-frame colour controls

For an editable normalised `RGB`, `ARGB`, or `RGBA` setting:

```text
Top:
  Darker | Lighter
  More red | Less red | More green | Less green | More blue | Less blue
  More opaque | Less opaque

Bottom-left:
  Previous | Next

Bottom-right:
  Cancel | Accept | Accept and implement
```

- `ARGB` has alpha first; `RGBA` has alpha last; `RGB` has no alpha.
- The RGB-adjustment buttons change only red, green, and blue and preserve
  alpha.
- Darker/Lighter first offer:
  - hue-preserving RGB scaling; or
  - fixed equal adjustment to all RGB channels.
- Darker/Lighter, More/Less red/green/blue, and More opaque/Less opaque offer
  5%, 10%, or 20% increments.
- More/Less red/green/blue change only their matching channel and remain within
  the normalised `0.0..1.0` range.
- More opaque/Less opaque change alpha only and are disabled for `RGB`.
- Previous/Next browse value history for the selected row; they do not navigate
  between settings.
- The image frame includes a one-column vertical history strip. Clicking an
  entry restores/previews that value.
- The history strip shows colour attempts as stacked swatches. Opacity and
  line-width attempts use compact visual samples; their raw values are
  available by tooltip.
- Cancel restores only the currently fine-tuned row to the value it had when
  that fine-tuning interaction began.
- Accept retains the current row value in the settings file and working preview
  without implementing it in Fusion XML.
- Accept and implement is a future explicit operation. It applies the entire
  active settings file only after a complete preview and transaction
  confirmation.
- After a verified implementation succeeds, keep the application open and show
  the transaction result.

### Fine-tuning history

- Every valid change to a row automatically becomes a history entry.
- History includes button adjustments and committed raw-value edits.
- Per-row histories persist across restarts in the active settings-file JSON.
- Global Ctrl+Z/redo is still current-session only.
- A later changed XML hash/version must offer an explicit compatibility choice;
  reuse, restart, trying a prior value, and applying a settings file are not
  allowed to happen silently.

### Settings files

```text
Settings file: [ soft-tone ▾ ]  [ Add new ]  [ Clone new ]
```

- The selected settings file saves working values and per-row histories
  immediately, including across application sessions.
- **Exit without applying** preserves the settings-file work; it does not write
  Fusion XML.
- **Accept and implement** remains a future explicit validated-copy/apply
  operation for the entire active settings file. On verified success, keep the
  application open and show the transaction result.
- **Add new** creates a fresh settings file populated from the
  `original_timestamp` XML baseline, with fresh histories.
- Do not show **Add new** before an `original_timestamp` XML baseline exists.
- **Clone new** may remain available before that baseline exists when a
  settings file is selected.
- **Clone new** copies the selected file's working values but starts fresh
  per-row histories.
- Add new and Clone new prompt for a display name, create a matching safe JSON
  filename such as `soft-tone.json`, and reject duplicates.

## Still to decide

- Confirm, remove, rename, reorder, or split the proposed groups.
- Decide whether visual settings that Fusion overrides should remain editable,
  become read-only, or receive a separate status workflow.
- Define the later relationship between grid edits, actual XML writes, backups,
  undo, named profiles, and Fusion validation screenshots.


## Real active PhotoBooth data

This is a read-only snapshot of the actual active Fusion PhotoBooth resource.

- Source: `C:\Users\johan\AppData\Local\Autodesk\webdeploy\pre-production\a40f190f24413dd1bb4f1434f056c1379a3b5224\Neutron\Server\Scene\Resources\Environments\PhotoBooth\PhotoBooth.xml`
- SHA-256: `79810da1933a75733383a55dd0a4791546a3a49f6ab1e8720f9718338366e4d5`
- Included visual candidates: **168**
- Inclusion rule: an attribute whose name identifies a colour/RGB channel, opacity, width, thickness, or size.
- Group and explanation are drafts for review; XML identity and current raw value are observed data.

### Background and grids

| Exact XML identity | Short label | Recognised type | Current raw value | Draft explanation |
|---|---|---|---|---|
| `/PhotoBooth[1]/Grid[1]/@ARGB` | `ARGB` | colour + opacity (ARGB) | `0.08 0.2 0.2 0.2` | Draft: controls argb for Grid. |
| `/PhotoBooth[1]/GridBackground[1]/@ARGB` | `ARGB` | colour + opacity (ARGB) | `0.1 0 0 0` | Draft: controls argb for Grid Background. |
| `/PhotoBooth[1]/LayoutGrid[1]/@ARGB` | `ARGB` | colour + opacity (ARGB) | `0.08 0.2 0.2 0.2` | Draft: controls argb for Layout Grid. |
| `/PhotoBooth[1]/Background[1]/@RGB` | `RGB` | colour (RGB) | `1.0 1.0 1.0` | Draft: controls rgb for Background. |

### Lighting and render

| Exact XML identity | Short label | Recognised type | Current raw value | Draft explanation |
|---|---|---|---|---|
| `/PhotoBooth[1]/OGSLighting[1]/Light[1]/@Color` | `Color` | colour (RGB) | `1 1 1` | Draft: controls color for Light. |
| `/PhotoBooth[1]/OGSLighting[1]/Light[1]/@ShadowColor` | `ShadowColor` | colour (RGB) | `-0.3 -0.3 -0.3` | Draft: controls shadow color for Light. |
| `/PhotoBooth[1]/RRTLighting[1]/@AmbientLightColor` | `AmbientLightColor` | colour (RGB) | `0.25 0.25 0.25` | Draft: controls ambient light color for RRTLighting. |
| `/PhotoBooth[1]/RRTLighting[1]/Light[1]/@Color` | `Color` | colour (RGB) | `1 1 1` | Draft: controls color for Light. |
| `/PhotoBooth[1]/RRTLighting[1]/Light[2]/@Color` | `Color` | colour (RGB) | `1 1 1` | Draft: controls color for Light. |
| `/PhotoBooth[1]/RRTLighting[1]/Light[3]/@Color` | `Color` | colour (RGB) | `1 1 1` | Draft: controls color for Light. |
| `/PhotoBooth[1]/RRTLighting[1]/Light[4]/@Color` | `Color` | colour (RGB) | `1 1 1` | Draft: controls color for Light. |
| `/PhotoBooth[1]/RRTBackground[1]/@RGB` | `RGB` | colour (RGB) | `.929 .929 .929` | Draft: controls rgb for RRTBackground. |

### Model, measurement, and joint previews

| Exact XML identity | Short label | Recognised type | Current raw value | Draft explanation |
|---|---|---|---|---|
| `/PhotoBooth[1]/DMBodyPreviewColor[1]/@ARGB` | `ARGB` | colour + opacity (ARGB) | `0.3 1 1 0` | Draft: controls argb for DMBody Preview Color. |
| `/PhotoBooth[1]/DMEdgePreviewColor[1]/@ARGB` | `ARGB` | colour + opacity (ARGB) | `1 0 0 0` | Draft: controls argb for DMEdge Preview Color. |
| `/PhotoBooth[1]/TBCutPreviewColor[1]/@ARGB` | `ARGB` | colour + opacity (ARGB) | `0.3 1 0 0` | Draft: controls argb for TBCut Preview Color. |
| `/PhotoBooth[1]/DMSculptCellColor[1]/@ARGB` | `ARGB` | colour + opacity (ARGB) | `0.05 0 1 0` | Draft: controls argb for DMSculpt Cell Color. |
| `/PhotoBooth[1]/DraftFacePreviewColor[1]/@ARGB` | `ARGB` | colour + opacity (ARGB) | `1 1 1 0` | Draft: controls argb for Draft Face Preview Color. |
| `/PhotoBooth[1]/JointBaseColor[1]/@ARGB` | `ARGB` | colour + opacity (ARGB) | `1 1 1 1` | Draft: controls argb for Joint Base Color. |
| `/PhotoBooth[1]/JointDOFColor[1]/@ARGB` | `ARGB` | colour + opacity (ARGB) | `1 0.5 0.8 0.8` | Draft: controls argb for Joint DOFColor. |
| `/PhotoBooth[1]/JointDOF2Color[1]/@ARGB` | `ARGB` | colour + opacity (ARGB) | `1 1 0.6 0.6` | Draft: controls argb for Joint DOF2 Color. |
| `/PhotoBooth[1]/JointDOF3Color[1]/@ARGB` | `ARGB` | colour + opacity (ARGB) | `1 0.6 1 0.6` | Draft: controls argb for Joint DOF3 Color. |
| `/PhotoBooth[1]/JointErrorColor[1]/@ARGB` | `ARGB` | colour + opacity (ARGB) | `1 0.8 0 0` | Draft: controls argb for Joint Error Color. |
| `/PhotoBooth[1]/DefaultMeasureTextColor[1]/@ARGB` | `ARGB` | colour + opacity (ARGB) | `1 0.2 0.2 0.2` | Draft: controls argb for Default Measure Text Color. |

### Selection and highlighting

| Exact XML identity | Short label | Recognised type | Current raw value | Draft explanation |
|---|---|---|---|---|
| `/PhotoBooth[1]/SelectEffectInfo[1]/@BaseColorRGBA` | `BaseColorRGBA` | colour + opacity (RGBA) | `0 0.4 1 0.5` | Draft: controls base color rgba for Select Effect Info. |
| `/PhotoBooth[1]/SelectEffectInfo[1]/@BackFaceColorRGBA` | `BackFaceColorRGBA` | colour + opacity (RGBA) | `0 0.4 1 0.15` | Draft: controls back face color rgba for Select Effect Info. |
| `/PhotoBooth[1]/SelectEffectInfo[1]/@HaloColorRGBA` | `HaloColorRGBA` | colour + opacity (RGBA) | `1 1 1 0.5` | Draft: controls halo color rgba for Select Effect Info. |
| `/PhotoBooth[1]/SelectEffectInfo[1]/@HiddenLineColorRGBA` | `HiddenLineColorRGBA` | colour + opacity (RGBA) | `0 0.5 1 0.5` | Draft: controls hidden line color rgba for Select Effect Info. |
| `/PhotoBooth[1]/SelectEffectInfo[1]/@LineColorRGBA` | `LineColorRGBA` | colour + opacity (RGBA) | `0 0.5 1 1` | Draft: controls line color rgba for Select Effect Info. |
| `/PhotoBooth[1]/SelectEffectInfo[1]/@GlowColorRGBA` | `GlowColorRGBA` | colour + opacity (RGBA) | `0.3, 0.47, 0.84, 0.33` | Draft: controls glow color rgba for Select Effect Info. |
| `/PhotoBooth[1]/SelectEffectInfo[1]/@HaloWidth` | `HaloWidth` | width / size | `2` | Draft: controls halo width for Select Effect Info. |
| `/PhotoBooth[1]/SelectEffectInfo[1]/@LinesWidth` | `LinesWidth` | width / size | `2` | Draft: controls lines width for Select Effect Info. |
| `/PhotoBooth[1]/ComponentSelectEffectInfo[1]/@BaseColorRGBA` | `BaseColorRGBA` | colour + opacity (RGBA) | `0.66 0.8 1.0 0.6` | Draft: controls base color rgba for Component Select Effect Info. |
| `/PhotoBooth[1]/ComponentSelectEffectInfo[1]/@BackFaceColorRGBA` | `BackFaceColorRGBA` | colour + opacity (RGBA) | `0.51 0.63 0.78 0.6` | Draft: controls back face color rgba for Component Select Effect Info. |
| `/PhotoBooth[1]/ComponentSelectEffectInfo[1]/@HaloColorRGBA` | `HaloColorRGBA` | colour + opacity (RGBA) | `0 0.16 0.5 0.5` | Draft: controls halo color rgba for Component Select Effect Info. |
| `/PhotoBooth[1]/ComponentSelectEffectInfo[1]/@HiddenLineColorRGBA` | `HiddenLineColorRGBA` | colour + opacity (RGBA) | `0 0.5 1 0.5` | Draft: controls hidden line color rgba for Component Select Effect Info. |
| `/PhotoBooth[1]/ComponentSelectEffectInfo[1]/@LineColorRGBA` | `LineColorRGBA` | colour + opacity (RGBA) | `0 0.5 1 1` | Draft: controls line color rgba for Component Select Effect Info. |
| `/PhotoBooth[1]/ComponentSelectEffectInfo[1]/@GlowColorRGBA` | `GlowColorRGBA` | colour + opacity (RGBA) | `0.3, 0.47, 0.84, 0.33` | Draft: controls glow color rgba for Component Select Effect Info. |
| `/PhotoBooth[1]/ComponentSelectEffectInfo[1]/@HaloWidth` | `HaloWidth` | width / size | `2` | Draft: controls halo width for Component Select Effect Info. |
| `/PhotoBooth[1]/ComponentSelectEffectInfo[1]/@LinesWidth` | `LinesWidth` | width / size | `2` | Draft: controls lines width for Component Select Effect Info. |
| `/PhotoBooth[1]/HighlightEffectInfo[1]/@BaseColorRGBA` | `BaseColorRGBA` | colour + opacity (RGBA) | `1 1 1 0.3` | Draft: controls base color rgba for Highlight Effect Info. |
| `/PhotoBooth[1]/HighlightEffectInfo[1]/@BackFaceColorRGBA` | `BackFaceColorRGBA` | colour + opacity (RGBA) | `0 0 0 0.15` | Draft: controls back face color rgba for Highlight Effect Info. |
| `/PhotoBooth[1]/HighlightEffectInfo[1]/@HaloColorRGBA` | `HaloColorRGBA` | colour + opacity (RGBA) | `1 1 1 0.5` | Draft: controls halo color rgba for Highlight Effect Info. |
| `/PhotoBooth[1]/HighlightEffectInfo[1]/@HiddenLineColorRGBA` | `HiddenLineColorRGBA` | colour + opacity (RGBA) | `0 0 0 0.2` | Draft: controls hidden line color rgba for Highlight Effect Info. |
| `/PhotoBooth[1]/HighlightEffectInfo[1]/@LineColorRGBA` | `LineColorRGBA` | colour + opacity (RGBA) | `0 0 0 1` | Draft: controls line color rgba for Highlight Effect Info. |
| `/PhotoBooth[1]/HighlightEffectInfo[1]/@GlowColorRGBA` | `GlowColorRGBA` | colour + opacity (RGBA) | `0.3, 0.47, 0.84, 0.33` | Draft: controls glow color rgba for Highlight Effect Info. |
| `/PhotoBooth[1]/HighlightEffectInfo[1]/@HaloWidth` | `HaloWidth` | width / size | `3` | Draft: controls halo width for Highlight Effect Info. |
| `/PhotoBooth[1]/HighlightEffectInfo[1]/@LinesWidth` | `LinesWidth` | width / size | `2` | Draft: controls lines width for Highlight Effect Info. |
| `/PhotoBooth[1]/MaterialPreviewSelectEffectInfo[1]/@BaseColorRGBA` | `BaseColorRGBA` | colour + opacity (RGBA) | `0 0 0 0` | Draft: controls base color rgba for Material Preview Select Effect Info. |
| `/PhotoBooth[1]/MaterialPreviewSelectEffectInfo[1]/@BackFaceColorRGBA` | `BackFaceColorRGBA` | colour + opacity (RGBA) | `0 0 0 0` | Draft: controls back face color rgba for Material Preview Select Effect Info. |
| `/PhotoBooth[1]/MaterialPreviewSelectEffectInfo[1]/@HaloColorRGBA` | `HaloColorRGBA` | colour + opacity (RGBA) | `0 0 1 0.8` | Draft: controls halo color rgba for Material Preview Select Effect Info. |
| `/PhotoBooth[1]/MaterialPreviewSelectEffectInfo[1]/@HiddenLineColorRGBA` | `HiddenLineColorRGBA` | colour + opacity (RGBA) | `0 0 0 0.2` | Draft: controls hidden line color rgba for Material Preview Select Effect Info. |
| `/PhotoBooth[1]/MaterialPreviewSelectEffectInfo[1]/@LineColorRGBA` | `LineColorRGBA` | colour + opacity (RGBA) | `0 0 0 1` | Draft: controls line color rgba for Material Preview Select Effect Info. |
| `/PhotoBooth[1]/MaterialPreviewSelectEffectInfo[1]/@GlowColorRGBA` | `GlowColorRGBA` | colour + opacity (RGBA) | `0.3, 0.47, 0.84, 0.33` | Draft: controls glow color rgba for Material Preview Select Effect Info. |
| `/PhotoBooth[1]/MaterialPreviewSelectEffectInfo[1]/@HaloWidth` | `HaloWidth` | width / size | `2` | Draft: controls halo width for Material Preview Select Effect Info. |
| `/PhotoBooth[1]/MaterialPreviewSelectEffectInfo[1]/@LinesWidth` | `LinesWidth` | width / size | `2` | Draft: controls lines width for Material Preview Select Effect Info. |
| `/PhotoBooth[1]/ErrorHighlightEffectInfo[1]/@BaseColorRGBA` | `BaseColorRGBA` | colour + opacity (RGBA) | `1 0.1 0.1 0.75` | Draft: controls base color rgba for Error Highlight Effect Info. |
| `/PhotoBooth[1]/ErrorHighlightEffectInfo[1]/@BackFaceColorRGBA` | `BackFaceColorRGBA` | colour + opacity (RGBA) | `1 0.1 0.1 0.75` | Draft: controls back face color rgba for Error Highlight Effect Info. |
| `/PhotoBooth[1]/ErrorHighlightEffectInfo[1]/@HaloColorRGBA` | `HaloColorRGBA` | colour + opacity (RGBA) | `1 1 1 0.5` | Draft: controls halo color rgba for Error Highlight Effect Info. |
| `/PhotoBooth[1]/ErrorHighlightEffectInfo[1]/@HiddenLineColorRGBA` | `HiddenLineColorRGBA` | colour + opacity (RGBA) | `1 0 0 0.5` | Draft: controls hidden line color rgba for Error Highlight Effect Info. |
| `/PhotoBooth[1]/ErrorHighlightEffectInfo[1]/@LineColorRGBA` | `LineColorRGBA` | colour + opacity (RGBA) | `1 0 0 1` | Draft: controls line color rgba for Error Highlight Effect Info. |
| `/PhotoBooth[1]/ErrorHighlightEffectInfo[1]/@GlowColorRGBA` | `GlowColorRGBA` | colour + opacity (RGBA) | `1, 0.3, 0.3, 0.33` | Draft: controls glow color rgba for Error Highlight Effect Info. |
| `/PhotoBooth[1]/ErrorHighlightEffectInfo[1]/@HaloWidth` | `HaloWidth` | width / size | `2` | Draft: controls halo width for Error Highlight Effect Info. |
| `/PhotoBooth[1]/ErrorHighlightEffectInfo[1]/@LinesWidth` | `LinesWidth` | width / size | `2` | Draft: controls lines width for Error Highlight Effect Info. |
| `/PhotoBooth[1]/PlaneSelectionManipulatorAxis[1]/@thickness` | `thickness` | width / size | `1.3` | Draft: controls thickness for Plane Selection Manipulator Axis. |
| `/PhotoBooth[1]/PlaneSelectionManipulatorAxis[1]/@XAxisColorARGB` | `XAxisColorARGB` | colour + opacity (ARGB) | `1.0 1 0 0` | Draft: controls xaxis color argb for Plane Selection Manipulator Axis. |
| `/PhotoBooth[1]/PlaneSelectionManipulatorAxis[1]/@YAxisColorARGB` | `YAxisColorARGB` | colour + opacity (ARGB) | `1.0 0 1 0` | Draft: controls yaxis color argb for Plane Selection Manipulator Axis. |
| `/PhotoBooth[1]/PlaneSelectionManipulatorAxis[1]/@ZAxisColorARGB` | `ZAxisColorARGB` | colour + opacity (ARGB) | `1.0 0 0 1` | Draft: controls zaxis color argb for Plane Selection Manipulator Axis. |
| `/PhotoBooth[1]/PlaneSelectionManipulatorPlane[1]/@DefaultColorARGB` | `DefaultColorARGB` | colour + opacity (ARGB) | `0.215 1 0.647 0` | Draft: controls default color argb for Plane Selection Manipulator Plane. |
| `/PhotoBooth[1]/PlaneSelectionManipulatorPlane[1]/@SelectColorARGB` | `SelectColorARGB` | colour + opacity (ARGB) | `0.5 0 0.47 1` | Draft: controls select color argb for Plane Selection Manipulator Plane. |
| `/PhotoBooth[1]/PlaneSelectionManipulatorPlane[1]/@HighLightColorARGB` | `HighLightColorARGB` | colour + opacity (ARGB) | `0.5 0.3 0.5 1` | Draft: controls high light color argb for Plane Selection Manipulator Plane. |
| `/PhotoBooth[1]/AdornerUnspecifiedColor[1]/@ARGB` | `ARGB` | colour + opacity (ARGB) | `1 1 0 1` | Draft: controls argb for Adorner Unspecified Color. |
| `/PhotoBooth[1]/AdornerSelectedColor[1]/@ARGB` | `ARGB` | colour + opacity (ARGB) | `0.5 0 0.47 1` | Draft: controls argb for Adorner Selected Color. |
| `/PhotoBooth[1]/AdornerHighlightedColor[1]/@ARGB` | `ARGB` | colour + opacity (ARGB) | `.5 0.3 .5 1` | Draft: controls argb for Adorner Highlighted Color. |
| `/PhotoBooth[1]/AdornerSelectedAndHighlightedColor[1]/@ARGB` | `ARGB` | colour + opacity (ARGB) | `.5 0 0.47 1` | Draft: controls argb for Adorner Selected And Highlighted Color. |
| `/PhotoBooth[1]/AdornerImplicitSelectionColor[1]/@ARGB` | `ARGB` | colour + opacity (ARGB) | `1 1 0 0` | Draft: controls argb for Adorner Implicit Selection Color. |
| `/PhotoBooth[1]/WorkPlaneAdornerColor[1]/@ARGB` | `ARGB` | colour + opacity (ARGB) | `0.85 0.9 0.9 0.9` | Draft: controls argb for Work Plane Adorner Color. |

### Simulation

| Exact XML identity | Short label | Recognised type | Current raw value | Draft explanation |
|---|---|---|---|---|
| `/PhotoBooth[1]/Simulation[1]/Previewer[1]/BarColor[1]/@ARGB` | `ARGB` | colour + opacity (ARGB) | `1 0.597 0.597 0.597` | Draft: controls argb for Bar Color. |
| `/PhotoBooth[1]/Simulation[1]/Previewer[1]/ProgressColor[1]/@ARGB` | `ARGB` | colour + opacity (ARGB) | `1 0.49 0.49 0.49` | Draft: controls argb for Progress Color. |

### Sketch

| Exact XML identity | Short label | Recognised type | Current raw value | Draft explanation |
|---|---|---|---|---|
| `/PhotoBooth[1]/SketchSelectEffectInfo[1]/@BaseColorRGBA` | `BaseColorRGBA` | colour + opacity (RGBA) | `0 0.4 1 0.5` | Draft: controls base color rgba for Sketch Select Effect Info. |
| `/PhotoBooth[1]/SketchSelectEffectInfo[1]/@BackFaceColorRGBA` | `BackFaceColorRGBA` | colour + opacity (RGBA) | `0 0.4 1 0.15` | Draft: controls back face color rgba for Sketch Select Effect Info. |
| `/PhotoBooth[1]/SketchSelectEffectInfo[1]/@HaloColorRGBA` | `HaloColorRGBA` | colour + opacity (RGBA) | `1 1 1 0.5` | Draft: controls halo color rgba for Sketch Select Effect Info. |
| `/PhotoBooth[1]/SketchSelectEffectInfo[1]/@HiddenLineColorRGBA` | `HiddenLineColorRGBA` | colour + opacity (RGBA) | `0 0.5 1 0.5` | Draft: controls hidden line color rgba for Sketch Select Effect Info. |
| `/PhotoBooth[1]/SketchSelectEffectInfo[1]/@LineColorRGBA` | `LineColorRGBA` | colour + opacity (RGBA) | `0.184 0.427 0.776 1` | Draft: controls line color rgba for Sketch Select Effect Info. |
| `/PhotoBooth[1]/SketchSelectEffectInfo[1]/@LineColor2RGBA` | `LineColor2RGBA` | colour + opacity (RGBA) | `1 0 0 1` | Draft: controls line color2 rgba for Sketch Select Effect Info. |
| `/PhotoBooth[1]/SketchSelectEffectInfo[1]/@GlowColorRGBA` | `GlowColorRGBA` | colour + opacity (RGBA) | `0.3, 0.47, 0.84, 0.33` | Draft: controls glow color rgba for Sketch Select Effect Info. |
| `/PhotoBooth[1]/SketchSelectEffectInfo[1]/@HaloWidth` | `HaloWidth` | width / size | `3` | Draft: controls halo width for Sketch Select Effect Info. |
| `/PhotoBooth[1]/SketchSelectEffectInfo[1]/@LinesWidth` | `LinesWidth` | width / size | `2` | Draft: controls lines width for Sketch Select Effect Info. |
| `/PhotoBooth[1]/SketchEntityColor[1]/@ARGB` | `ARGB` | colour + opacity (ARGB) | `1.0 0 0 0` | Draft: controls argb for Sketch Entity Color. |
| `/PhotoBooth[1]/SketchPredictedEntityColor[1]/@ARGB` | `ARGB` | colour + opacity (ARGB) | `1.0 0.35 0.16 0.71` | Draft: controls argb for Sketch Predicted Entity Color. |
| `/PhotoBooth[1]/SketchConstraintColor[1]/@ARGB` | `ARGB` | colour + opacity (ARGB) | `1.0 0.58 0.74 0.25` | Draft: controls argb for Sketch Constraint Color. |
| `/PhotoBooth[1]/SketchPredictedConstraintColor[1]/@ARGB` | `ARGB` | colour + opacity (ARGB) | `1.0 0.29 0.09 0.69` | Draft: controls argb for Sketch Predicted Constraint Color. |
| `/PhotoBooth[1]/SketchConflictingConstraintColor[1]/@ARGB` | `ARGB` | colour + opacity (ARGB) | `1.0 0.87 0.13 0.13` | Draft: controls argb for Sketch Conflicting Constraint Color. |
| `/PhotoBooth[1]/SketchConstraintHighlightedColor[1]/@ARGB` | `ARGB` | colour + opacity (ARGB) | `1.0 0.61 0.84 0.94` | Draft: controls argb for Sketch Constraint Highlighted Color. |
| `/PhotoBooth[1]/SketchConstraintSelectedColor[1]/@ARGB` | `ARGB` | colour + opacity (ARGB) | `1.0 0.02 0.59 0.84` | Draft: controls argb for Sketch Constraint Selected Color. |
| `/PhotoBooth[1]/SketchInferenceColor[1]/@ARGB` | `ARGB` | colour + opacity (ARGB) | `1.0 0 0.5 0.78` | Draft: controls argb for Sketch Inference Color. |
| `/PhotoBooth[1]/SketchInferenceMouseColor[1]/@ARGB` | `ARGB` | colour + opacity (ARGB) | `1.0 0.22 0.22 0.22` | Draft: controls argb for Sketch Inference Mouse Color. |
| `/PhotoBooth[1]/SketchProfileColor[1]/@ARGB` | `ARGB` | colour + opacity (ARGB) | `0.2 0.02 0.59 0.84` | Draft: controls argb for Sketch Profile Color. |
| `/PhotoBooth[1]/SketchLineColor[1]/@ARGB` | `ARGB` | colour + opacity (ARGB) | `1.0 0.02 0.59 0.84` | Draft: controls argb for Sketch Line Color. |
| `/PhotoBooth[1]/SketchFixedLineColor[1]/@ARGB` | `ARGB` | colour + opacity (ARGB) | `1.0 0.58 0.74 0.25` | Draft: controls argb for Sketch Fixed Line Color. |
| `/PhotoBooth[1]/SketchProjectedLineColor[1]/@ARGB` | `ARGB` | colour + opacity (ARGB) | `1.0 0.67 0.39 0.81` | Draft: controls argb for Sketch Projected Line Color. |
| `/PhotoBooth[1]/SketchCachedProjectedLineColor[1]/@ARGB` | `ARGB` | colour + opacity (ARGB) | `1.0 0.81 0.43 0.24` | Draft: controls argb for Sketch Cached Projected Line Color. |
| `/PhotoBooth[1]/SketchFullyConstrainedColor[1]/@ARGB` | `ARGB` | colour + opacity (ARGB) | `1.0 0 0 0` | Draft: controls argb for Sketch Fully Constrained Color. |
| `/PhotoBooth[1]/SketchHandlePointColor[1]/@ARGB` | `ARGB` | colour + opacity (ARGB) | `1.0 0.33 0.85 0.33` | Draft: controls argb for Sketch Handle Point Color. |
| `/PhotoBooth[1]/SketchInactiveHandleColor[1]/@ARGB` | `ARGB` | colour + opacity (ARGB) | `1.0 0.25 0.8 0.8` | Draft: controls argb for Sketch Inactive Handle Color. |
| `/PhotoBooth[1]/SketchActiveHandleColor[1]/@ARGB` | `ARGB` | colour + opacity (ARGB) | `1.0 0.25 0.8 0.8` | Draft: controls argb for Sketch Active Handle Color. |
| `/PhotoBooth[1]/TextBorderColor[1]/@ARGB` | `ARGB` | colour + opacity (ARGB) | `1.0 0.55 0.2 0.0` | Draft: controls argb for Text Border Color. |
| `/PhotoBooth[1]/SketchDimensionColor[1]/@ARGB` | `ARGB` | colour + opacity (ARGB) | `1.0 0 0 0` | Draft: controls argb for Sketch Dimension Color. |
| `/PhotoBooth[1]/SketchPredictedDimensionColor[1]/@ARGB` | `ARGB` | colour + opacity (ARGB) | `1.0 0.35 0.16 0.71` | Draft: controls argb for Sketch Predicted Dimension Color. |
| `/PhotoBooth[1]/SketchDrivenDimensionColor[1]/@ARGB` | `ARGB` | colour + opacity (ARGB) | `1.0 0.24 0.24 0.24` | Draft: controls argb for Sketch Driven Dimension Color. |
| `/PhotoBooth[1]/SketchDimensionInfoColor[1]/@ARGB` | `ARGB` | colour + opacity (ARGB) | `1.0 0.5 0.5 0.5` | Draft: controls argb for Sketch Dimension Info Color. |
| `/PhotoBooth[1]/SketchPreviewColor[1]/@ARGB` | `ARGB` | colour + opacity (ARGB) | `1.0 0.5 0.09 0.16` | Draft: controls argb for Sketch Preview Color. |
| `/PhotoBooth[1]/DimensionPreviewColor[1]/@ARGB` | `ARGB` | colour + opacity (ARGB) | `1 0.6 0.6 0.6` | Draft: controls argb for Dimension Preview Color. |
| `/PhotoBooth[1]/SketchConstructionColor[1]/@ARGB` | `ARGB` | colour + opacity (ARGB) | `1.0 0.55 0.2 0.0` | Draft: controls argb for Sketch Construction Color. |
| `/PhotoBooth[1]/JointDimensionColor[1]/@ARGB` | `ARGB` | colour + opacity (ARGB) | `1 0.5 0.5 0.5` | Draft: controls argb for Joint Dimension Color. |
| `/PhotoBooth[1]/MeasureDimensionColor[1]/@ARGB` | `ARGB` | colour + opacity (ARGB) | `1 0 0 0` | Draft: controls argb for Measure Dimension Color. |
| `/PhotoBooth[1]/MeasureDimensionHighlightColor[1]/@ARGB` | `ARGB` | colour + opacity (ARGB) | `1 0.8 0.8 0.8` | Draft: controls argb for Measure Dimension Highlight Color. |
| `/PhotoBooth[1]/InferenceDimensionColor[1]/@ARGB` | `ARGB` | colour + opacity (ARGB) | `1 0 0 0` | Draft: controls argb for Inference Dimension Color. |

### Unclassified

| Exact XML identity | Short label | Recognised type | Current raw value | Draft explanation |
|---|---|---|---|---|
| `/PhotoBooth[1]/ModelEdgeColor[1]/@ARGB` | `ARGB` | colour + opacity (ARGB) | `1 0 0 0 ` | Draft: controls argb for Model Edge Color. |
| `/PhotoBooth[1]/Simulation[1]/Previewer[1]/ProgressAnimationColor[1]/@ARGB` | `ARGB` | colour + opacity (ARGB) | `1 0.497 0.497 0.497` | Draft: controls argb for Progress Animation Color. |
| `/PhotoBooth[1]/Simulation[1]/Previewer[1]/ValueColor[1]/@ARGB` | `ARGB` | colour + opacity (ARGB) | `1 0.314 0.784 1` | Draft: controls argb for Value Color. |
| `/PhotoBooth[1]/ColorCycleTable[1]/ColorCycle[1]/@RGB` | `RGB` | colour (RGB) | `0.89 0.57 0.90` | Draft: controls rgb for Color Cycle. |
| `/PhotoBooth[1]/ColorCycleTable[1]/ColorCycle[2]/@RGB` | `RGB` | colour (RGB) | `1.00 0.85 0.48` | Draft: controls rgb for Color Cycle. |
| `/PhotoBooth[1]/ColorCycleTable[1]/ColorCycle[3]/@RGB` | `RGB` | colour (RGB) | `0.77 0.96 0.44` | Draft: controls rgb for Color Cycle. |
| `/PhotoBooth[1]/ColorCycleTable[1]/ColorCycle[4]/@RGB` | `RGB` | colour (RGB) | `0.36 0.55 0.93` | Draft: controls rgb for Color Cycle. |
| `/PhotoBooth[1]/ColorCycleTable[1]/ColorCycle[5]/@RGB` | `RGB` | colour (RGB) | `0.75 0.55 0.95` | Draft: controls rgb for Color Cycle. |
| `/PhotoBooth[1]/ColorCycleTable[1]/ColorCycle[6]/@RGB` | `RGB` | colour (RGB) | `1.00 0.72 0.43` | Draft: controls rgb for Color Cycle. |
| `/PhotoBooth[1]/ColorCycleTable[1]/ColorCycle[7]/@RGB` | `RGB` | colour (RGB) | `0.85 0.87 0.35` | Draft: controls rgb for Color Cycle. |
| `/PhotoBooth[1]/ColorCycleTable[1]/ColorCycle[8]/@RGB` | `RGB` | colour (RGB) | `0.33 0.85 0.97` | Draft: controls rgb for Color Cycle. |
| `/PhotoBooth[1]/ColorCycleTable[1]/ColorCycle[9]/@RGB` | `RGB` | colour (RGB) | `0.99 0.58 0.81` | Draft: controls rgb for Color Cycle. |
| `/PhotoBooth[1]/ColorCycleTable[1]/ColorCycle[10]/@RGB` | `RGB` | colour (RGB) | `0.91 0.81 0.39` | Draft: controls rgb for Color Cycle. |
| `/PhotoBooth[1]/ColorCycleTable[1]/ColorCycle[11]/@RGB` | `RGB` | colour (RGB) | `0.52 0.87 0.35` | Draft: controls rgb for Color Cycle. |
| `/PhotoBooth[1]/ColorCycleTable[1]/ColorCycle[12]/@RGB` | `RGB` | colour (RGB) | `0.28 0.33 0.84` | Draft: controls rgb for Color Cycle. |
| `/PhotoBooth[1]/ColorCycleTable[1]/ColorCycle[13]/@RGB` | `RGB` | colour (RGB) | `0.95 0.53 0.58` | Draft: controls rgb for Color Cycle. |
| `/PhotoBooth[1]/ColorCycleTable[1]/ColorCycle[14]/@RGB` | `RGB` | colour (RGB) | `1.00 0.95 0.41` | Draft: controls rgb for Color Cycle. |
| `/PhotoBooth[1]/ColorCycleTable[1]/ColorCycle[15]/@RGB` | `RGB` | colour (RGB) | `0.38 0.98 0.38` | Draft: controls rgb for Color Cycle. |
| `/PhotoBooth[1]/ColorCycleTable[1]/ColorCycle[16]/@RGB` | `RGB` | colour (RGB) | `0.42 0.31 0.97` | Draft: controls rgb for Color Cycle. |
| `/PhotoBooth[1]/ColorCycleTable[1]/ColorCycle[17]/@RGB` | `RGB` | colour (RGB) | `1.00 0.69 0.70` | Draft: controls rgb for Color Cycle. |
| `/PhotoBooth[1]/ColorCycleTable[1]/ColorCycle[18]/@RGB` | `RGB` | colour (RGB) | `0.39 0.87 0.89` | Draft: controls rgb for Color Cycle. |
| `/PhotoBooth[1]/ColorCycleTable[1]/ColorCycle[19]/@RGB` | `RGB` | colour (RGB) | `1.00 0.62 0.40` | Draft: controls rgb for Color Cycle. |
| `/PhotoBooth[1]/ColorCycleTable[1]/ColorCycle[20]/@RGB` | `RGB` | colour (RGB) | `1.00 0.39 0.45` | Draft: controls rgb for Color Cycle. |
| `/PhotoBooth[1]/ColorCycleTable[1]/ColorCycle[21]/@RGB` | `RGB` | colour (RGB) | `0.91 0.58 0.75` | Draft: controls rgb for Color Cycle. |
| `/PhotoBooth[1]/ColorCycleTable[1]/ColorCycle[22]/@RGB` | `RGB` | colour (RGB) | `0.42 0.99 0.87` | Draft: controls rgb for Color Cycle. |
| `/PhotoBooth[1]/ColorCycleTable[1]/ColorCycle[23]/@RGB` | `RGB` | colour (RGB) | `0.91 0.46 0.31` | Draft: controls rgb for Color Cycle. |
| `/PhotoBooth[1]/ColorCycleTable[1]/ColorCycle[24]/@RGB` | `RGB` | colour (RGB) | `0.91 0.31 0.65` | Draft: controls rgb for Color Cycle. |
| `/PhotoBooth[1]/ColorCycleTable[1]/ColorCycle[25]/@RGB` | `RGB` | colour (RGB) | `0.91 0.63 0.58` | Draft: controls rgb for Color Cycle. |
| `/PhotoBooth[1]/ColorCycleTable[1]/ColorCycle[26]/@RGB` | `RGB` | colour (RGB) | `0.38 0.62 0.89` | Draft: controls rgb for Color Cycle. |
| `/PhotoBooth[1]/ColorCycleTable[1]/ColorCycle[27]/@RGB` | `RGB` | colour (RGB) | `0.91 0.62 0.31` | Draft: controls rgb for Color Cycle. |
| `/PhotoBooth[1]/ColorCycleTable[1]/ColorCycle[28]/@RGB` | `RGB` | colour (RGB) | `0.91 0.36 0.31` | Draft: controls rgb for Color Cycle. |
| `/PhotoBooth[1]/ColorCycleTable[1]/ColorCycle[29]/@RGB` | `RGB` | colour (RGB) | `1.00 0.72 0.62` | Draft: controls rgb for Color Cycle. |
| `/PhotoBooth[1]/ColorCycleTable[1]/ColorCycle[30]/@RGB` | `RGB` | colour (RGB) | `0.47 0.84 0.98` | Draft: controls rgb for Color Cycle. |
| `/PhotoBooth[1]/ColorCycleTable[1]/ColorCycle[31]/@RGB` | `RGB` | colour (RGB) | `1.00 0.75 0.33` | Draft: controls rgb for Color Cycle. |
| `/PhotoBooth[1]/ColorCycleTable[1]/ColorCycle[32]/@RGB` | `RGB` | colour (RGB) | `1.00 0.48 0.32` | Draft: controls rgb for Color Cycle. |
| `/PhotoBooth[1]/SliceTable[1]/ColorCycle[1]/@RGB` | `RGB` | colour (RGB) | `0.2 0.2 0.2` | Draft: controls rgb for Color Cycle. |
| `/PhotoBooth[1]/SliceTable[1]/ColorCycle[2]/@RGB` | `RGB` | colour (RGB) | `0.26 0.26 0.26` | Draft: controls rgb for Color Cycle. |
| `/PhotoBooth[1]/SliceTable[1]/ColorCycle[3]/@RGB` | `RGB` | colour (RGB) | `0.32 0.32 0.32` | Draft: controls rgb for Color Cycle. |
| `/PhotoBooth[1]/SliceTable[1]/ColorCycle[4]/@RGB` | `RGB` | colour (RGB) | `0.38 0.38 0.38` | Draft: controls rgb for Color Cycle. |
| `/PhotoBooth[1]/SliceTable[1]/ColorCycle[5]/@RGB` | `RGB` | colour (RGB) | `0.44 0.44 0.44` | Draft: controls rgb for Color Cycle. |
| `/PhotoBooth[1]/SliceTable[1]/ColorCycle[6]/@RGB` | `RGB` | colour (RGB) | `0.5 0.5 0.5` | Draft: controls rgb for Color Cycle. |
| `/PhotoBooth[1]/SliceTable[1]/ColorCycle[7]/@RGB` | `RGB` | colour (RGB) | `0.56 0.56 0.56` | Draft: controls rgb for Color Cycle. |
| `/PhotoBooth[1]/SliceTable[1]/ColorCycle[8]/@RGB` | `RGB` | colour (RGB) | `0.62 0.62 0.62` | Draft: controls rgb for Color Cycle. |
| `/PhotoBooth[1]/SliceTable[1]/ColorCycle[9]/@RGB` | `RGB` | colour (RGB) | `0.68 0.68 0.68` | Draft: controls rgb for Color Cycle. |
| `/PhotoBooth[1]/SliceTable[1]/ColorCycle[10]/@RGB` | `RGB` | colour (RGB) | `0.74 0.74 0.74` | Draft: controls rgb for Color Cycle. |

### Work geometry and manipulators

| Exact XML identity | Short label | Recognised type | Current raw value | Draft explanation |
|---|---|---|---|---|
| `/PhotoBooth[1]/WorkAxisColor[1]/@ARGB` | `ARGB` | colour + opacity (ARGB) | `0.87 0 1 0.92` | Draft: controls argb for Work Axis Color. |
| `/PhotoBooth[1]/WorkPlaneColor[1]/@ARGB` | `ARGB` | colour + opacity (ARGB) | `0.3 1 0.647 0` | Draft: controls argb for Work Plane Color. |
| `/PhotoBooth[1]/WorkPlaneTextColor[1]/@ARGB` | `ARGB` | colour + opacity (ARGB) | `1 0.902 0.494 0.208` | Draft: controls argb for Work Plane Text Color. |
| `/PhotoBooth[1]/OriginXAxisColor[1]/@ARGB` | `ARGB` | colour + opacity (ARGB) | `1.0 1 0 0` | Draft: controls argb for Origin XAxis Color. |
| `/PhotoBooth[1]/OriginYAxisColor[1]/@ARGB` | `ARGB` | colour + opacity (ARGB) | `1.0 0 1 0` | Draft: controls argb for Origin YAxis Color. |
| `/PhotoBooth[1]/OriginZAxisColor[1]/@ARGB` | `ARGB` | colour + opacity (ARGB) | `1.0 0 0 1` | Draft: controls argb for Origin ZAxis Color. |
