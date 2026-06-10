#!/bin/sh
# 在 Mac 上运行:把 rk3506-app 经跳板机推到板子并安装+启动。
#   Mac ──► 跳板 192.168.1.104 (user/Ml@009988) ──► 板子 192.168.1.10 (root/root)
#
# 用法:  sh deploy/push.sh
# 可用环境变量覆盖:
#   JUMP_HOST JUMP_USER JUMP_PW BOARD_HOST BOARD_USER BOARD_PW
#
# 依赖 sshpass(Mac: brew install hudochenkov/sshpass/sshpass)。
# 若你已配好 ssh 免密到板子,设 NO_SSHPASS=1 跳过 sshpass。
set -eu

JUMP_HOST="${JUMP_HOST:-192.168.1.104}"
JUMP_USER="${JUMP_USER:-user}"
JUMP_PW="${JUMP_PW:-Ml@009988}"
BOARD_HOST="${BOARD_HOST:-192.168.1.10}"
BOARD_USER="${BOARD_USER:-root}"
BOARD_PW="${BOARD_PW:-root}"

SRC=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)       # .../rk3506-app
PARENT=$(dirname "$SRC")
NAME=$(basename "$SRC")

SSH_OPTS="-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
if [ "${NO_SSHPASS:-0}" = "1" ]; then
  PROXY="ssh $SSH_OPTS -W %h:%p ${JUMP_USER}@${JUMP_HOST}"
  BOARD_SSH="ssh $SSH_OPTS -o ProxyCommand=\"$PROXY\" ${BOARD_USER}@${BOARD_HOST}"
  run_board() { eval ssh $SSH_OPTS -o ProxyCommand="\"$PROXY\"" "${BOARD_USER}@${BOARD_HOST}" "$@"; }
else
  command -v sshpass >/dev/null 2>&1 || { echo "缺 sshpass: brew install hudochenkov/sshpass/sshpass(或设 NO_SSHPASS=1 用免密)"; exit 1; }
  PROXY="sshpass -p ${JUMP_PW} ssh $SSH_OPTS -W %h:%p ${JUMP_USER}@${JUMP_HOST}"
  run_board() { sshpass -p "$BOARD_PW" ssh $SSH_OPTS -o ProxyCommand="$PROXY" "${BOARD_USER}@${BOARD_HOST}" "$@"; }
fi

echo "[push] 打包并推送 $NAME 经跳板 $JUMP_HOST 到板子 $BOARD_HOST ..."
tar -C "$PARENT" --exclude="$NAME/data" --exclude="$NAME/run" \
    --exclude="*/__pycache__" --exclude="*.pyc" -cf - "$NAME" \
  | run_board 'mkdir -p /userdata/_stage && rm -rf /userdata/_stage/* && tar -C /userdata/_stage -xf - && sh /userdata/_stage/'"$NAME"'/deploy/install.sh'

echo "[push] 完成。验证:"
echo "  curl -s http://${BOARD_HOST}:8092/api/health   (经跳板或同网段)"
echo "  板子屏幕应已显示 RK3506 GATEWAY 第一屏。"
