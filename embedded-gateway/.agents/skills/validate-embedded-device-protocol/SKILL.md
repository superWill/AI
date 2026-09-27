---
name: validate-embedded-device-protocol
description: Validate evidence and implementation readiness for embedded field-device protocol integrations. Use when adding, reviewing, debugging, or claiming support for an RS485, Modbus RTU/ASCII/TCP, UART, CAN, I2C, SPI, LoRa concentrator, meter, sensor, actuator, PLC, or vendor-private protocol device; when interpreting register maps, serial parameters, byte/word order, scaling, writable points, or raw frames; and when creating device templates or protocol drivers. Require an exact-model communication manual or official register map before approving a concrete integration.
---

# Validate Embedded Device Protocol

Treat the device communication manual as an implementation input, not optional background. Separate interface discovery from protocol support: a product page that says `RS485` does not prove Modbus support or define a register map.

## Workflow

1. Read the nearest `AGENTS.md` and any required project memory before inspecting or changing code.
2. Identify the exact manufacturer, model, hardware variant, firmware version, and intended operation: read-only monitoring, configuration, or control.
3. Search the repository and user-provided files for the matching communication manual, protocol manual, or official register map. If absent and web research is authorized or required, use the manufacturer's official source.
4. Record the evidence before interpreting frames or editing a driver.
5. Apply the evidence gate below.
6. Complete the protocol checklist for every concrete device template or driver.
7. Validate with raw-frame test vectors and, when hardware is available, read-only probing before enabling writes.
8. Report the decision, evidence, unknowns, risks, and allowed next action.

## Evidence gate

Accept as primary evidence:

- An official communication/protocol manual matching the exact device model or declared model family.
- An official register map or integration guide that defines the implemented firmware behavior.
- A manufacturer-supplied machine-readable device description when it contains equivalent protocol detail.

Treat generic Modbus specifications, marketing pages, product datasheets, screenshots, third-party summaries, packet captures, and existing code as supplementary evidence. They do not replace the device-specific communication manual.

Assign exactly one status:

- `PASS`: Exact device identity is known; authoritative manual coverage is sufficient; required fields are resolved; read/write behavior has representative test vectors.
- `CONDITIONAL`: An authoritative manual exists but the firmware/model match or one or more required fields remain ambiguous. Permit read-only experiments; prohibit production writes and claims of complete support.
- `BLOCKED`: No authoritative device-specific manual/register map exists, the device identity is unclear, or writable behavior is undocumented. Do not implement concrete register semantics or claim device support.
- `EXPLORATORY`: The user explicitly requests reverse engineering. Keep all inferred fields labeled as hypotheses, preserve raw captures, use isolated hardware, and never promote the result to production support without authoritative confirmation or a separately approved validation standard.

When blocked, allow only reversible scaffolding such as a generic transport interface, evidence checklist, capture tool, or placeholder device template whose unknown fields fail closed. Never guess register addresses, scaling, byte order, write values, unlock sequences, or safety limits.

## Required evidence record

Record these fields in the review or device template provenance:

```text
manufacturer:
model:
hardware_variant:
firmware_version:
manual_title:
manual_version_or_date:
manual_source_or_repo_path:
relevant_pages_or_sections:
evidence_match: exact | family | ambiguous
```

If a manual omits a field, write `undocumented`; do not silently select a common default.

## Protocol checklist

### Physical and link layer

- Confirm the physical interface and transceiver level; do not equate RS485 with Modbus.
- Confirm connector pinout, signal polarity labels, reference ground, isolation, termination, biasing, and topology constraints.
- Confirm baud rate, data bits, parity, stop bits, and whether all devices sharing one serial bus can use the same framing.
- Confirm address range, reserved/broadcast addresses, duplicate-address prevention, and provisioning method.
- Confirm timing: response timeout, silent interval, turnaround delay, retries, and maximum frame size.

### Framing and operations

- Confirm protocol variant, frame layout, CRC/checksum, supported function or command codes, and exception/error responses.
- Confirm whether the device may transmit spontaneously or only responds to polling.
- Confirm maximum contiguous read/write sizes and any atomic multi-register requirements.
- Reject undocumented vendor extensions unless they are isolated and explicitly labeled.

### Data interpretation

- Confirm whether documented register numbers are zero-based protocol offsets or human-facing `3xxxx/4xxxx` references.
- For every point, record address, register count, access mode, data type, signedness, byte order, word order, scale/offset, unit, valid range, invalid sentinel, refresh behavior, and firmware applicability.
- For 32/64-bit values, record the actual wire-byte permutation such as `ABCD` or `CDAB`; do not rely only on ambiguous labels such as "little-endian".
- Distinguish raw acquisition time, receive time, quality, stale state, timeout, protocol exception, and invalid engineering value.

### Write and safety behavior

- Treat every write as unsafe until the manual defines the writable address, value domain, units, side effects, and confirmation behavior.
- Confirm unlock/login sequences, operating-mode prerequisites, interlocks, rate limits, persistence, flash endurance, reboot behavior, defaults, and rollback.
- Keep UI limits separate from device-side and system safety limits.
- Require read-back or an independent feedback point before claiming a physical command succeeded.
- Start with read-only integration. Enable writes only through an explicit allowlist and a reviewed safety policy.

## Validation

Require at least one manual-derived raw-frame vector for each distinct data encoding and command shape:

```text
raw request bytes:
raw response bytes:
expected decoded value:
data type:
byte/word order:
scale and unit:
source manual section:
```

Test applicable failure paths: wrong baud/framing, timeout, CRC/checksum error, protocol exception, duplicate address, short frame, out-of-range value, invalid sentinel, device reboot, and interrupted write. Add deterministic regression tests before declaring support.

## Required output

Lead with the gate result and do not bury missing evidence:

```text
Decision: PASS | CONDITIONAL | BLOCKED | EXPLORATORY
Device: manufacturer / model / variant / firmware
Manual: title / version / path or URL / relevant sections
Evidence match: exact | family | ambiguous

Resolved:
- ...

Unknown or conflicting:
- ...

Write safety:
- disabled | allowlisted points and constraints

Validation performed:
- ...

Allowed next action:
- ...
```

Tag factual conclusions using the repository's required claim and confidence labels. Never convert a successful transport probe into a claim that the complete device protocol is supported.
