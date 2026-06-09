#!/bin/sh
set -eu

# RK3506-side Nordic UART Service probe.
# Usage:
#   MSG=final-proof ./ble_nus_probe.sh 90:7A:DA:D3:CD:DD
#
# Current tested peer is the 227 host running ble_peripheral.py as GW-PEER.
# The RK3506 Buildroot bluetoothctl Device1 path is unreliable for Connect(),
# so this probe temporarily stops bluetoothd and lets gatttool own hci0.

PEER="${1:-90:7A:DA:D3:CD:DD}"
TX_CCCD="${TX_CCCD:-0x001e}"
RX_VALUE="${RX_VALUE:-0x0020}"
DESC_START="${DESC_START:-0x001b}"
DESC_END="${DESC_END:-0x0020}"
MSG="${MSG:-notify-proof}"
HEX="$(printf '%s' "$MSG" | od -An -tx1 | tr -d ' \n')"

cleanup() {
  killall hcidump >/dev/null 2>&1 || true
  killall gatttool >/dev/null 2>&1 || true
  if ! ps w | grep '[b]luetoothd' >/dev/null 2>&1; then
    /usr/libexec/bluetooth/bluetoothd -n -d >/tmp/bluetoothd.log 2>&1 &
  fi
}
trap cleanup EXIT INT TERM

killall gatttool >/dev/null 2>&1 || true
killall bluetoothd >/dev/null 2>&1 || true
sleep 2
hciconfig hci0 down
sleep 1
hciconfig hci0 up
sleep 2

echo "== descriptors =="
timeout 12 gatttool -i hci0 -b "$PEER" -t public --char-desc \
  --start="$DESC_START" --end="$DESC_END" || true

hcidump -i hci0 -X >/tmp/hci_notify.txt 2>&1 &
CAP="$!"
sleep 1

echo "== subscribe TX =="
timeout 15 gatttool -i hci0 -b "$PEER" -t public \
  --char-write-req -a "$TX_CCCD" -n 0100

echo "== write RX: $MSG =="
timeout 15 gatttool -i hci0 -b "$PEER" -t public \
  --char-write-req -a "$RX_VALUE" -n "$HEX"

sleep 3
kill "$CAP" >/dev/null 2>&1 || true

echo "== notifications captured =="
grep -n -A3 -B1 'ATT: Handle notify' /tmp/hci_notify.txt || true
