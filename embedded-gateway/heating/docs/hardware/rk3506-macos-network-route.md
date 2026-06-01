# RK3506 macOS Network Route

Use this note when connecting the HD-RK3506-IOT board to this Mac by Ethernet.

## Known Network

| Target | IP | Interface |
|---|---:|---|
| RK3506 ETH0 | `192.168.1.10` | `en12` |
| Mac address for RK3506 link | `192.168.1.100/24` | `en12` |
| claw-harbor / lobster host | `192.168.1.227` | keep on `en0` |

The Mac's main network also covers `192.168.0.0/23` on `en0`, so macOS often
routes `192.168.1.10` to `en0` by mistake.

Do not route the whole `192.168.1.0/24` network to `en12`, because that breaks
other machines such as `192.168.1.227`. Fix only the RK3506 host route:

```sh
scripts/setup_rk3506_macos_route.sh
```

Expected route check:

```text
192.168.1.10  -> interface: en12
192.168.1.227 -> interface: en0
```

Expected RK3506 ARP:

```text
192.168.1.10 -> de:26:83:a2:cb:09 on en12 ifscope
```

Vendor SSH login:

```sh
ssh root@192.168.1.10
# password: root
```

These settings are temporary and may be lost after reboot, unplugging the USB
Ethernet adapter, or changing macOS network settings.
