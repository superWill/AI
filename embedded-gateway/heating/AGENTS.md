# Agent Notes

## RK3506 board access on this Mac

When connecting to the HD-RK3506-IOT board, do not assume `192.168.1.10` should
go through the default `en0` route. The board is wired to the USB Ethernet
adapter `en12`.

Run this first if SSH to the board fails:

```sh
scripts/setup_rk3506_macos_route.sh
```

Expected routes:

```text
192.168.1.10  -> en12   # RK3506 ETH0
192.168.1.227 -> en0    # claw-harbor / lobster host
```

Important: do not route the whole `192.168.1.0/24` network to `en12`, and do
not add `192.168.1.227 -interface en0`. That can create a bad permanent ARP
entry pointing at the Mac itself. The helper script only pins the RK3506 host
route and ARP entry.

RK3506 vendor SSH login is `root@192.168.1.10`, password `root`.
