# RK3506 HMI Design QA

- Source visual truth: `design-reference.png`
- Implementation screenshot: `board-overview-800x480.png` (retrieved from `/tmp/dash_overview.png` on the RK3506 after deployment)
- Full-view comparison: `design-comparison.png`
- Focused comparisons: `design-comparison-header.png`, `design-comparison-content.png`
- Viewport: 800 × 480 physical LCD
- State: overview, simulated snapshot, 7/8 devices online
- Target interpretation: preserve the reference's light visual language and information hierarchy while adapting its desktop/cloud-agent composition to an offline, native DRM field HMI.

## Findings

- No actionable P0/P1/P2 mismatch remains for the adapted 800 × 480 target.
- [P3] Typography is visibly more mechanical than the reference.
  - Location: all labels and large values.
  - Evidence: the reference uses an antialiased proportional CJK UI font; the implementation uses a bundled 16-pixel GNU Unifont subset.
  - Impact: lower visual refinement, but stable offline rendering without a browser or font runtime.
  - Follow-up: use a board-verified raster font engine only if its memory, startup, licensing, and DRM compatibility are accepted.
- [P3] The reference mascot and product photos are intentionally absent.
  - Location: central hero and lower device cards.
  - Evidence: the implementation uses live operational cards and local-duty state instead of decorative imagery.
  - Impact: less brand personality, but more space for actionable data at 800 × 480 and no misleading cloud-agent affordance.
  - Follow-up: add approved raster brand assets later if a product asset pack is supplied and board decoding cost is accepted.

## Required Fidelity Surfaces

- Fonts and typography: hierarchy, wrapping, truncation, and contrast pass at 800 × 480; antialiasing differs by the native font constraint noted above.
- Spacing and layout rhythm: top bar, four KPI cards, three device cards, right duty rail, and bottom navigation preserve the reference's major-region proportions without overflow.
- Colors and visual tokens: pale blue canvas, white cards, navy text, blue primary actions, green normal state, amber attention state, subtle borders, radii, and shadows match the reference direction.
- Image quality and asset fidelity: no fake mascot or product imagery was introduced. Source imagery was intentionally omitted rather than approximated; all visible implementation graphics are functional native UI indicators.
- Copy and content: cloud-dependent assistant wording was replaced with observable local services—data acquisition, device operation, local control, and optional cloud uplink.

## Interaction And Runtime Checks

- All six page states render into exactly `800 × 480 × 3` RGB bytes.
- The board-rendered and local-rendered overview PNG files have the same SHA-256: `1663156a5119e337b2f787fbe2887fdbe31b74b32378491a75535fc965313542`.
- Every returned touch rectangle is positive, on-screen, and fully bounded.
- Navigation, device configuration entry, configuration adjustments, and local-control adjustment hit areas remain wired through the existing DRM touch controller.
- Browser and console checks are not applicable: this implementation is a Python framebuffer renderer written directly to DRM, not a web app.

## Comparison History

- Formal comparison pass 1: no P0/P1/P2 findings. Earlier implementation inspection had already corrected missing-glyph copy and misaligned configuration `−/+` labels before the formal side-by-side evidence was captured.

## Follow-up Polish

- Consider approved brand illustration and equipment image assets only after their offline footprint and renderer path are defined.
- Consider antialiased font rendering as a separate performance-qualified enhancement.

final result: passed
