#!/usr/bin/env bash
set -euo pipefail

# macOS helper for the HD-RK3506-IOT board on ETH0.
#
# Network shape on this workstation:
# - RK3506 ETH0 default IP: 192.168.1.10
# - USB Ethernet adapter connected to RK3506: en12
# - Mac static address on en12: 192.168.1.100/24
# - "claw-harbor" / lobster host: 192.168.1.227, keep it on en0
#
# This script is intentionally temporary. Routes may disappear after reboot,
# unplugging the adapter, or changing macOS network settings.

BOARD_IP="${BOARD_IP:-192.168.1.10}"
BOARD_IF="${BOARD_IF:-en12}"
BOARD_LOCAL_IP="${BOARD_LOCAL_IP:-192.168.1.100}"
BOARD_MAC="${BOARD_MAC:-de:26:83:a2:cb:09}"
KEEP_HOST_IP="${KEEP_HOST_IP:-192.168.1.227}"
KEEP_HOST_IF="${KEEP_HOST_IF:-en0}"

log() {
  printf '==> %s\n' "$*"
}

log "Configuring ${BOARD_IF} as ${BOARD_LOCAL_IP}/24 for RK3506"
sudo ifconfig "${BOARD_IF}" inet "${BOARD_LOCAL_IP}" netmask 255.255.255.0

log "Removing stale host route for ${KEEP_HOST_IP}, if present"
sudo route -n delete -host "${KEEP_HOST_IP}" >/dev/null 2>&1 || true
sudo arp -d "${KEEP_HOST_IP}" >/dev/null 2>&1 || true

log "Routing only ${BOARD_IP} via ${BOARD_IF}"
if sudo route -n add -host "${BOARD_IP}" -interface "${BOARD_IF}" 2>/dev/null; then
  :
else
  sudo route -n change -host "${BOARD_IP}" -interface "${BOARD_IF}" 2>/dev/null || true
fi

log "Pinning ${BOARD_IP} to RK3506 MAC ${BOARD_MAC} on ${BOARD_IF}"
sudo arp -s "${BOARD_IP}" "${BOARD_MAC}" ifscope "${BOARD_IF}"

log "Route check: RK3506"
route -n get "${BOARD_IP}"

log "Route check: preserved host (${KEEP_HOST_IP} should stay on ${KEEP_HOST_IF})"
route -n get "${KEEP_HOST_IP}"

log "SSH port check"
nc -vz -G 2 "${BOARD_IP}" 22

cat <<EOF

RK3506 route is ready.

SSH:
  ssh root@${BOARD_IP}

Default RK3506 credentials from vendor doc:
  user: root
  password: root
EOF
