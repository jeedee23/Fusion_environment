# RRT and OGS lighting notes

## Source and confidence

This note records a user-supplied AI conversation dated 14 October 2026. It is
context for designing the settings grid, not verified Fusion documentation.

The conversation's claims about rendering internals, shader mathematics, and
the meaning of negative colour-like values must be tested in the selected
Fusion build before becoming behaviour or UI assertions.

## Terms described by the supplied conversation

### OGS

The conversation expands **OGS** as **One Graphics System** and describes it
as Fusion's real-time viewport graphics system.

It proposes that OGS lighting is relevant to the regular Design workspace
display, using image-based/environment lighting and fast graphics
approximations rather than a progressive render.

### RRT

The conversation expands **RRT** as **Rapid Ray Tracer** and describes it as a
ray-traced/rendering lighting system.

It proposes that RRT handles global illumination, reflections, shadows, and
progressive refinement in an in-canvas or render workflow.

### Proposed distinction for the grid

Until tested, use these as **draft context labels**, not hard rules:

| XML area | Draft mode label | What needs confirmation |
|---|---|---|
| `OGSLighting` | Design — needs confirmation | Whether each field affects the Design viewport, and whether Fusion reloads the change. |
| `RRTLighting` | Render — needs confirmation | Whether each field affects in-canvas/render output, and which render path uses it. |
| `Background`, grids, sketch, selection | Design / Sketch — needs confirmation | The actual Fusion contexts in which each setting is visible. |

## Observed active PhotoBooth values

These values were read from the active discovered resource, not inferred from
the supplied conversation:

```text
PhotoBooth.xml SHA-256
79810da1933a75733383a55dd0a4791546a3a49f6ab1e8720f9718338366e4d5
```

| Exact XML identity | Current raw value | Observation |
|---|---|---|
| `/PhotoBooth[1]/OGSLighting[1]/Light[1]/@Color` | `1 1 1` | A normalised three-component colour-like value. |
| `/PhotoBooth[1]/OGSLighting[1]/Light[1]/@ShadowColor` | `-0.3 -0.3 -0.3` | The only colour-named value found with negative components. Its rendering meaning is unverified. |
| `/PhotoBooth[1]/RRTLighting[1]/@AmbientLightColor` | `0.25 0.25 0.25` | A normalised three-component ambient-light value. |
| `/PhotoBooth[1]/RRTLighting[1]/Light[1]/@Color` | `1 1 1` | A normalised three-component light value. |
| `/PhotoBooth[1]/RRTLighting[1]/Light[2]/@Color` | `1 1 1` | A normalised three-component light value. |
| `/PhotoBooth[1]/RRTLighting[1]/Light[3]/@Color` | `1 1 1` | A normalised three-component light value. |
| `/PhotoBooth[1]/RRTLighting[1]/Light[4]/@Color` | `1 1 1` | A normalised three-component light value. |
| `/PhotoBooth[1]/RRTBackground[1]/@RGB` | `.929 .929 .929` | A normalised three-component background value. |

## Negative values found in the active XML

The active XML contains negative components in six attributes:

| Exact XML identity | Current raw value | Classification |
|---|---|---|
| `/PhotoBooth[1]/OGSLighting[1]/Light[1]/@Direction` | `0.1 -0.55 -1.0` | Signed direction vector, not a colour. |
| `/PhotoBooth[1]/OGSLighting[1]/Light[1]/@ShadowColor` | `-0.3 -0.3 -0.3` | Signed colour-named triplet; meaning needs testing. |
| `/PhotoBooth[1]/RRTLighting[1]/Light[1]/@Direction` | `0.1 -0.55 -1.0` | Signed direction vector, not a colour. |
| `/PhotoBooth[1]/RRTLighting[1]/Light[2]/@Direction` | `0.0 -0.6 -0.4` | Signed direction vector, not a colour. |
| `/PhotoBooth[1]/RRTLighting[1]/Light[3]/@Direction` | `-0.3 -0.6 0.4` | Signed direction vector, not a colour. |
| `/PhotoBooth[1]/RRTLighting[1]/Light[4]/@Direction` | `0.3 -0.6 0.4` | Signed direction vector, not a colour. |

This evidence does **not** establish a general `-1..+1` colour range:

- the five `Direction` attributes are clearly signed 3D vectors;
- all observed RRT colour-like values are within `0..1`;
- `ShadowColor` is the one exceptional colour-named signed value.

## Implication for the settings grid

Until an actual Fusion test proves otherwise:

- treat normalised `RGB`, `ARGB`, and `RGBA` values as ordinary colour/swatch
  candidates;
- treat `OGSLighting/Light/@ShadowColor` as an **advanced, unverified signed
  triplet**, not a normal colour-picker value;
- retain its raw value and exact identity;
- do not clamp, remap, or display it as a normal swatch;
- mark its explanation and any OGS/RRT workspace label as needing confirmation.

## Questions for Fusion validation

1. Does changing `OGSLighting/Light/@Color` visibly affect the Design
   viewport?
2. Does changing `RRTLighting/@AmbientLightColor` visibly affect in-canvas or
   saved rendering?
3. What visual result, if any, follows a small reversible change to
   `OGSLighting/Light/@ShadowColor`?
4. Does the selected Fusion version reload either lighting block after the
   normal environment reload/restart procedure?
5. Which screenshot(s) prove the result for Design and Render respectively?
