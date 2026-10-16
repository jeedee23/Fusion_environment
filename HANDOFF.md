# Fusion_environment - handoff for GitHub Copilot

**Owner:** Johan Degraeve  
**Prepared:** 14 October 2026  
**Repository name:** `Fusion_environment`  
**Status:** reconstruction brief with reference data; no recovered implementation.

## 1. The task

Rebuild the tool we wrote around 25-27 October 2024 to customize Autodesk Fusion's environment colours. Johan has checked all machines and backups and cannot find the old source or add-in. **Do not spend another session searching those backups.**

The present focus is the built-in **Photo Booth** environment, internal name `PhotoBooth`. Johan chose it because it was consistently available, rather than relying on a newly invented environment. Preserve that approach, but test availability on the actual installation rather than promising that every future Fusion build will contain an identical file.

The desired result is a maintainable local C++ add-in with an HTML colour-settings form, saved colour profiles and reversible application of changes. Concentrate on the design canvas, sketch geometry, dimensions, grids, selection/highlighting and other colour fields that the actual resource definition exposes. This is not a request to restyle Windows, replace the Fusion ribbon, change material appearances, or redesign the Render workspace.

No personal colour values have been recovered. Do not invent a "Johan dark theme" or present the uploaded white/blue/black values as his approved palette. Start with an unchanged import; make each subsequent colour choice explicit.

## 2. Evidence hierarchy

Keep four categories distinct:

1. **Current user instructions:** new repo, old implementation missing, Photo Booth chosen as the base.
2. **Recovered conversation notes:** useful original design constraints, but not executable source or proof that every feature worked.
3. **Supplied XML:** exact observed structures and values, with unknown original Windows path mapping.
4. **New proposals and current documentation:** implementation suggestions and API capabilities verified separately.

`docs/SOURCE_EVIDENCE.md` records provenance and path hints. `docs/OFFICIAL_REFERENCES.md` records the current primary documentation. Do not merge these into an invented story about which file the old application edited.

## 3. Recovered original design: retain, do not silently replace

The old runtime/add-in name was `customizeEnvironment`. It used C++, with an earlier Python experiment called `EnvironmentCustomizer`. The last recovered direction was the C++ add-in, not a request to return to Python.

The recorded deployment layout was:

```text
%APPDATA%\Autodesk\Autodesk Fusion 360\API\AddIns\customizeEnvironment\
    customizeEnvironment.cpp
    customizeEnvironment.dll
    Resources\
        environmentForm.html
        envpaths\
```

For the rebuild, keep the source in Git and deploy only the necessary runtime artifacts; source beside the DLL is historical layout, not a new requirement.

The recovered UI had toolbar tab `myTab`, **six environment panels, ten options per environment**, and Stop / Apply / Restart panels. The six internal environment names were:

```text
DarkSky
GreyRoom
PhotoBooth
TranquilityBlue
InfinityPool
RiverRubicon
```

Buttons called `showForm(env, option)`. The HTML palette was `Resources/environmentForm.html`, approximately 1000 x 800 and centred. Preserve that layout intent, with sizing constrained to the available display. Exact old option captions and the complete action semantics were not recovered. Do not pretend a new grouping is the original grouping.

Johan explicitly required resource paths to be derived from the add-in location through a helper called `getFusion360AddInPath()`, using `std::filesystem::path` components consistently. **That helper is project code to implement; it is not an Autodesk API.** Do not use the current working directory, a hardcoded username or a mixed-slash string concatenation scheme.

The original first-run rule was also explicit: `Resources/envpaths` must exist; otherwise report that the add-in is not installed correctly and show the absolute path. The installer creates it. An existing `firstrunok.txt` should be honoured silently, without repeated first-run searches or success dialogs. Without the marker, locate/copy the six required environment XMLs and create the marker only once the required cache is complete. See section 10 for preserving this without weakening file safety.

One previous implementation mistake was attempting an unsupported `CheckBoxGroupCommandInput`. Verify all SDK members; use the HTML form instead of inventing command-input classes.

## 4. What the five references actually establish

| Reference | Observed content | Permitted use now |
| --- | --- | --- |
| `PhotoBooth.xml` | `PhotoBooth` root; only `Simulation/Previewer` settings | Classification test; not a complete colour-template replacement |
| `PhotoBooth (1).xml` | Extensive `PhotoBooth` definition with background, grid, sketch, dimensions, effects, colour tables, lighting and resources | Offline parsing, field inventory and disposable-copy tests |
| `PhotoBooth (2).xml` | `Environments Version="2"` IBL manifest | Negative test for wrong resource/schema |
| `PhotoBooth (3).xml` | Byte-identical to `(2)` | Retain separate upload provenance; negative test |
| `PhotoBooth (4).xml` | Byte-identical to `(2)` | Retain separate upload provenance; negative test |

The extensive sample has **148 explicitly labelled RGB/ARGB/RGBA attributes**, inventoried in `references/colour_fields.json`. This is not evidence of 148 supported, user-visible controls in the installed Fusion version.

The sparse definition is not automatically corrupt. It could belong to a different resource layer or product variation; this is a hypothesis to investigate, not a conclusion. A `PhotoBooth` root or filename alone is insufficient to establish that the file is the active design-canvas colour definition.

**Never overwrite a sparse active file with the extensive uploaded sample to "repair" it.** Never use an Inventor file as a substitute. Preserve all references byte for byte and verify their hashes before working from them.

## 5. Stage 1 discovery: read-only and evidence-led

The initial diagnostic must identify the active Fusion executable, version/build, process ID where available, installation root, channel, installed C++ SDK and add-in registration/resource location. Record unavailable process information or permission restrictions instead of treating them as proof that Fusion is closed.

The only pasted path inside a Fusion installation tree was a versioned directory under:

```text
%LOCALAPPDATA%\Autodesk\webdeploy\pre-production\<deployment-id>\
    Neutron\Server\Scene\Resources\Environments\PhotoBooth\PhotoBooth.xml
```

Its existence does not prove that this is the currently launched build. The original full path is preserved in the evidence notes, not hardcoded in runtime logic.

Search bounded installation candidates discovered from process/launcher/install evidence. Production and pre-production may need separate examination. Do not recursively scan all drives, select the newest directory, or select the first matching filename. Allow an explicit target-root override and record its provenance.

Within the selected candidate root, find relevant PhotoBooth resources and inspect content. Multiple definitions may exist within one build: report every candidate, its relative path, schema classification, byte count, hash and relevant fields. If resource layering is suspected, investigate the installation's surrounding configuration/resources; do not guess which layer wins.

For each candidate, report `usable`, `incomplete`, `wrong schema`, `ambiguous`, or `not yet validated`, together with a reason. Canonicalize paths and detect reparse-point escapes. Treat all Inventor / Inventor Interoperability paths as outside the writable Fusion scope even when their filenames match.

Deliver a local discovery report, not modifications. A report of "target cannot yet be established" is valid; continue offline core/UI development while recording that integration is blocked.

## 6. Proposed rebuild architecture

The following decomposition is a new implementation proposal that preserves the recovered C++/HTML direction:

```text
src/core/               XML classification, field model, profiles, diff and transactions
src/addin/              Fusion lifecycle, toolbar, palette and SDK adapter
src/apply/              Small offline apply/restore executable using the same core
Resources/             environmentForm.html, local JavaScript/CSS
config/                Reviewed field/group mapping, not machine-specific paths
profiles/              Optional user-approved portable profiles
scripts/               Explicit developer setup/deploy commands
tests/                 Core, fake-install, transaction and UI tests
```

This is a proposed layout, not files already implemented in this package.

Use a small standards-compliant XML library and JSON library selected and pinned during implementation. Document why they were chosen and their licensing; do not fetch unpinned dependencies at add-in startup. Use a configurable C++ build, with the required standard/toolset matched to the installed SDK. Do not promise that an old absolute include path or the machine's newest Python version is relevant to compiling this add-in.

The core must compile and run its tests independently of Fusion. The Fusion adapter should be thin. Keep the HTML/JavaScript local and simple; no Electron, cloud service, CDN, telemetry or account system is needed.

A separate offline apply helper is the conservative proposed route because in-Fusion editing occurs while Fusion is running. The palette prepares a reviewed change plan; the eventual authorized install-file transaction occurs only after Fusion is closed normally. Do not launch an automatic watcher or kill/restart Fusion to work around this. Add a live route only if its safety and actual reload behaviour are demonstrated on the target build.

## 7. Colour field and profile contract

### Scope and identity

A field is an exact XML element selector plus an attribute, not merely a label such as "blue" or `name="Dark Pink"`. Repeated elements need unique identities. The supplied colour table contains two entries named `Dark Pink`; they must remain distinct.

The reference catalog uses indexed paths, for example:

```text
/PhotoBooth[1]/Background[1]/@RGB
/PhotoBooth[1]/SketchLineColor[1]/@ARGB
/PhotoBooth[1]/SketchSelectEffectInfo[1]/@LineColorRGBA
```

Indexes identify this snapshot, not a universal schema. On a different build, resolve and validate identities again; compare expected metadata/value and fail on missing or ambiguous matches. Do not silently create missing nodes or redirect a patch to a different ordinal after an update.

### Channel order and precision

Interpret the explicitly named encodings separately: `RGB` has red, green, blue; `ARGB` has alpha first; `RGBA` has alpha last. Accept the whitespace-separated and comma-separated forms actually present. Reject the wrong number of components, NaN, infinity and out-of-range edited values. Preserve alpha unless the user edits it.

The editor may display a swatch, numeric RGB channels, hex and a separate alpha control. Use a canonical in-memory RGBA representation with sufficient precision, but retain the raw source string and never rewrite an untouched field just because a picker rounds to 8-bit values. Do not assume or introduce a gamma/colour-space conversion without evidence.

Do not infer editability from every numeric tuple. `OGSLighting/.../@ShadowColor` contains negative values and belongs to lighting, not a normalized UI-colour field to clamp. Keep `Direction`, gains, widths, booleans, textures, HDRI references, geometry, display-name translations and all unrelated content unchanged.

A no-op open/save/preview must preserve the original bytes. For a real patch, preserve unrelated XML bytes as far as the writer permits, and in all cases prove that only the selected attributes changed semantically. Select a round-trip-safe editing strategy; a global regular expression replacement is not an XML patcher. Reject DTD/external-entity input; no parser network access.

### Profile format: new proposal

`examples/profile.noop.json` is the starting data shape, not an already implemented interface. Non-empty `patches` should include:

```json
{
  "element_path": "/PhotoBooth[1]/SketchLineColor[1]",
  "attribute": "ARGB",
  "encoding": "ARGB",
  "expected_raw_value": "1.0 0.02 0.59 0.84",
  "rgba": [0.02, 0.59, 0.84, 1.0]
}
```

This example represents the observed unchanged sample value, not a requested colour change. Include schema version, profile ID/name and environment identity. Keep portable profiles separate from machine-specific transaction plans. A plan binds the selected target, build/channel, current hash, resolved field changes and proposed output hash; an imported profile alone is never authorization to write a file.

Save reusable profiles outside versioned Fusion deployment directories. As a new proposal, use `%APPDATA%\Fusion_environment\profiles` for user profiles and `%LOCALAPPDATA%\Fusion_environment` for machine state/backups, with a documented override. Keep machine paths and logs out of Git. Review portable custom profiles before committing them.

## 8. HTML palette behaviour

Preserve the six panels and ten option slots. Use Photo Booth for the first end-to-end validation. Other environments can show availability and pending integration rather than faking support or disappearing from the design.

A sensible **proposed, not recovered** ten-group mapping is: background; grids; sketch geometry; sketch constraints/inference; sketch dimensions/text; selection; hover/error highlighting; work geometry/origin/manipulators; modelling/measurement/joint previews; component/slice colour tables and advanced fields. Store groups in data rather than hardcoding sixty duplicate forms. Simulation-only controls can be an advanced subgroup, clearly labelled as unrelated to the design background.

Each field should show a human label, its exact XML identity, current value, edited value/swatch, alpha where present and a changed indicator. Provide revert-field, discard unapplied edits, save/load profile, preview diff, prepare apply, and restore access. Show the absolute selected resource path, build/channel, verification state and backup/plan status in an unobtrusive diagnostic section.

A canvas mockup helps judge contrast but must be labelled as an approximation. It is not proof that Fusion rendered the change.

Maintain the Stop / Apply / Restart layout intent, but do not invent destructive behaviour from the old captions. Proposed safe semantics: Stop cancels pending UI work without terminating Fusion; Apply prepares or invokes only the validated permitted route; Restart explains/requires the appropriate reload/restart after saving work. Explicitly distinguish **restart the add-in** from **restart Fusion**. Never force terminate the process or discard unsaved documents.

Use the documented palette bridge: HTML calls `adsk.fusionSendData`, C++ receives `incomingFromHTML`, and C++ can use `sendInfoToHTML` with `window.fusionJavaScriptHandler.handle` on the HTML side. Correlate requests/results, validate JSON actions and payloads, and never turn HTML messages into arbitrary shell commands or arbitrary-path writes. Return an acknowledgement distinct from operation success. Keep native event handlers alive and remove only this add-in's UI/event registrations when stopping.

## 9. Safe apply and restore

The initial prompt authorizes repository work, tests and diagnostics, **not installation writes or deployment**. For a later authorized apply, require all of the following:

1. A specifically selected Fusion build/root and schema-compatible resource, plus resolved resource-layer uncertainty. A filename, marker or read-only discovery heuristic is insufficient.
2. An exact preview of selected field changes. Parse and validate the proposed XML; show no-op status when nothing changes.
3. An immutable, byte-for-byte backup of the actual current target outside the deployment tree, keyed by canonical path/build/hash, with a manifest and verified backup hash. An uploaded reference is never that backup.
4. A fresh check that the target is still the expected file/hash and that no affected Fusion instance is running for the offline route. Access-denied process checks, a changed build, an updater race, a moved path or a conflicting hash block the write.
5. A complete temporary output, validation and safe same-volume replacement with appropriate Windows metadata/permissions handling. No truncate-and-rewrite of the target. Flush where appropriate, re-read the result, and verify its hash/content. Record failure and recovery state precisely.

Implement one-file transactions first. Do not simulate a multi-file transaction by partially applying a group. Guard against path traversal, symbolic links/reparse escapes, accidental Inventor targets and repeated/replayed plans. An already-applied plan can be a verified no-op, not a second uncontrolled write.

Restore checks that the selected backup belongs to the same intended path/build. Preserve the currently installed bytes as a separate pre-restore snapshot. If the current target differs from the known applied hash, stop for review rather than overwriting another change or a software update. Restore exact original bytes and verify. Do not silently restore an old build's XML into a new deployment.

Do not escalate privileges, change ACLs, disable protection, or force-write a locked file as an automatic fallback. Report a permission failure and leave the target intact.

## 10. Cache and updates

Preserve the recovered `Resources/envpaths` contract and six required names. A valid first-run collection uses only verified Fusion resources, preserving relative provenance and hashes. Do not mix versions/channels or choose an Inventor lookalike to satisfy a missing filename.

An existing `firstrunok.txt` suppresses repeated initial discovery, as requested historically; it does not certify that a live target is safe to patch. Maintain a separate cache/source manifest. Before apply, revalidate the selected installation and file identities regardless of the marker. If the cache directory is absent, show the absolute path and installation error; the explicit installer/setup step must create it.

Without the marker, do not create it until all six required caches are genuinely complete. If the current build no longer supplies a required environment or uses an unverified layered layout, report the unresolved item. Photo Booth offline development can continue, but do not silently weaken the original first-run contract or mark the whole cache ready.

Store user profiles and immutable transaction backups independently of the add-in cache. A Fusion update requires rediscovery and a new baseline/backup for that build. Re-resolve the selected profile's fields and regenerate a diff; a missing field or changed baseline is a compatibility conflict, not permission to restore an old complete XML. No automatic startup overwrite or background reapplication.

## 11. Current API capability and limits

Autodesk currently documents `Application.lightingEnvironment` and `LightingEnvironments`, introduced in **November 2025**, including `PhotoBoothLightingEnvironment` and the other five historical environments. Use the documented property when the installed SDK/runtime supports it rather than guessing text commands. Record the local SDK/build used. [A1, A2]

This property selects an environment. It does **not** document arbitrary sketch-colour modification or a cache invalidation/hot-reload mechanism. Switching away and back, viewport refresh and restarting the add-in must not be advertised as XML reloads without an actual test. Likewise, an offline write that parses successfully is not proof of a visual change.

The references checked here establish palette communication and environment selection, not a supported general XML editing contract. Treat file editing as a version-dependent customization route until the active installation has been validated. Prefer a documented per-field API if current research finds one, but cite and test it rather than assuming it exists. [A1-A5]

If a full Fusion restart is required, say so. Arrange it only after explicit user action and normal save/close handling. The handoff does not authorize restarting the user's application.

## 12. Implementation stages and deliverables

**Stage 0 - preserve and verify.** Run the supplied reference checker. Read the evidence notes. Establish a status log. No backup hunting and no invented recovered code.

**Stage 1 - diagnose.** Implement read-only Windows installation/SDK discovery and candidate classification. Save a machine-local report. Record the chosen root or the exact remaining ambiguity. Do not modify Autodesk files.

**Stage 2 - offline core.** Build classification, explicit colour parsing, unique field addressing, a reviewed profile schema, validation and dry-run diff. Exercise all five references and disposable mutated copies. Demonstrate no-op byte identity, alpha preservation, duplicate-name handling and rejection of the wrong schema. No Fusion SDK dependency in these tests.

**Stage 3 - add-in and form.** Build the SDK-configurable C++ adapter and local HTML palette, initially with offline fixture mode and production writes disabled. Retain the recovered UI layout. Loading it into Fusion is a separate explicit deployment/test step, not implied by compiling it.

**Stage 4 - apply/restore engine.** Implement the one-file transaction helper and fake-install tests for backup, conflicts, failures, no-op, rollback and restore. Keep real installation writes blocked until the target/route and user authorization are established.

**Stage 5 - actual Fusion validation.** On the explicitly selected build, with authorization and a tested backup, apply one small reviewed change. Restart/reload only by the verified safe procedure. Check the actual result, restore it, and prove restoration. Then extend to the other colour groups and historical environments, keeping missing support explicit.

**Stage 6 - maintainability.** Document installation, disable/uninstall, update recovery, profile portability and the exact verified build/test commands. Keep source history and a useful session status so a future recovery does not depend on chat history.

## 13. Acceptance and reporting

The test matrix is in `docs/ACCEPTANCE_TESTS.md`. The work is not complete because a form opens, a DLL compiles or a screenshot of a browser mockup looks right.

Completion requires: verified current target; repeatable build; correct field editing; profiles; dry-run; reliable backup/restore; real in-Fusion visual evidence for supported fields; and explicit limitations for unverified fields/environments. Record the precise build/channel in that evidence.

Before ending each coding session, update `docs/STATUS.md` with files changed, commands actually executed, test results, unresolved assumptions and the next actionable task. Mark unrun tests as unrun. Keep progressing on safe repository work without asking repetitive permission, but stop installation writes when their preconditions are not met.

Reference labels A1-A6 resolve in `docs/OFFICIAL_REFERENCES.md`. Source observations resolve in `docs/SOURCE_EVIDENCE.md` and the byte-preserved references.
