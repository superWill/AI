# RK3506 Energy HMI Deploy

This package deploys the static Energy HMI to an HD-RK3506-IOT Buildroot image.
It does not require nginx, node, or systemd. It uses the target board's Python 3
standard library HTTP server.

Target defaults:

```text
Board IP: 192.168.1.10
Install path: /userdata/energy-hmi
HTTP port: 8092
URL: http://192.168.1.10:8092/
```

Install on the board:

```sh
cd /tmp/energy-hmi-rk3506
chmod +x install.sh start.sh stop.sh status.sh uninstall.sh
./install.sh
/userdata/energy-hmi/start.sh
```

Check:

```sh
/userdata/energy-hmi/status.sh
tail -f /userdata/energy-hmi/log/energy-hmi.log
```

Stop or remove:

```sh
/userdata/energy-hmi/stop.sh
/userdata/energy-hmi/uninstall.sh
```

Override defaults:

```sh
APP_ROOT=/userdata/my-hmi PORT=8080 ./install.sh
```
