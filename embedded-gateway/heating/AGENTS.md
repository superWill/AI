# Agent Notes

## RK3506 board access through the lobster host

The Mac USB Ethernet interface `en12` no longer exists. Connect through the
reinstalled lobster host instead:

```sh
ssh -J user@192.168.1.227 root@192.168.1.10
```

Current topology (verified 2026-07-17):

```text
Mac/Wi-Fi -> 192.168.1.227 (harbor-b362a2)
harbor-b362a2 wlp1s0 = 192.168.1.227/23 (management/default route)
harbor-b362a2 enp3s0 = 192.168.1.2/32 (RK3506 cable)
host route 192.168.1.10/32 -> enp3s0
RK3506 ETH0 = 192.168.1.10
```

The persistent NetworkManager profile on the lobster host is `rk3506-link`:

```sh
nmcli connection show rk3506-link
ip route get 192.168.1.10
```

Do not add a whole-subnet route on the lobster host: its Wi-Fi already owns
`192.168.0.0/23`. Keep only the more-specific `192.168.1.10/32` Ethernet route,
with `ipv4.never-default=yes`, so configuring the board cannot break remote
management.

RK3506 vendor SSH login is `root@192.168.1.10`, password `root`.
