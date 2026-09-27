# Embedded Gateway Agent Instructions

## Task Start Protocol

Before executing a task that requires tools or repository changes, first give a concise description of:

1. The target outcome.
2. The proposed implementation approach.
3. How the result will be verified.

Only begin tool calls or file changes after presenting this brief. Purely conversational or explanatory responses that require no execution are exempt.

## Project Memory

For work involving IP cameras, RTSP, main/sub streams, H.264/H.265, MPP, RGA,
RKNN, YOLO, RetinaFace, person detection, event recording, or video upload,
read `docs/edge-video-processing-pipeline.md` first and treat it as the current
project memory and implementation-status baseline.

Do not collapse these distinct capacity measures into one number: physical
cameras, RTSP streams, MPP decode sessions, recording streams, and NPU analysis
tasks. In particular, RK3568 multi-stream decode capacity does not prove equal
multi-stream real-time AI capacity.

Preserve the documented boundary between current implementation and target
architecture. RGA preprocessing, tracking, line crossing, dwell analysis,
people counting, first-frame persistence, representative face-frame storage,
real splitmuxsink recording, and full multi-model throughput remain unverified
or incomplete unless newer repository evidence supersedes the document.

For work involving LoRa, LoRaWAN, fire-alarm auxiliary monitoring, fire two-bus
integration, RS485-LoRa concentrators, device provisioning, or wireless device
identity, read `docs/lora-fire-scenario-memory.md` first. Use
`docs/lora-fire-scenario.xmind` as the navigable mind-map companion and
`docs/lora-protocol-and-integration.md` for the broader protocol and RK3506
integration baseline.
