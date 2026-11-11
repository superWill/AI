#!/usr/bin/env bash
# P0 实机能力取证 —— 在 BL412B(RK3568J/Ubuntu 20.04)上跑,把输出存成报告。
# 目的:用命令输出证明 RKNN/MPP/RGA 是否可用,而不是假设。
# 用法:  bash scripts/check_platform.sh   (输出存到 docs/p0-platform-<host>-<date>.txt)
set -u

OUT="docs/p0-platform-$(hostname)-$(date +%Y%m%d-%H%M%S).txt"
mkdir -p docs

run() {  # run "标题" 命令...
  echo "==== $1 ====" | tee -a "$OUT"
  shift
  "$@" 2>&1 | tee -a "$OUT"
  echo | tee -a "$OUT"
}

echo "P0 平台能力报告  $(date -Is)" | tee "$OUT"
echo | tee -a "$OUT"

run "内核/架构"            uname -a
run "发行版"              bash -c 'cat /etc/os-release'
run "设备树 compatible"   bash -c "cat /proc/device-tree/compatible | tr '\0' '\n'"
run "设备树 model"        bash -c 'cat /proc/device-tree/model 2>/dev/null; echo'
run "CPU"                bash -c 'lscpu | grep -Ei "model name|architecture|cpu\(s\)|max mhz" || cat /proc/cpuinfo | grep -i "model name" | head -1'
run "内存"               free -h
run "存储"               df -h
run "网口"               ip -br addr
run "NPU/MPP/DRI 设备"    bash -c 'ls -l /dev/rknpu* /dev/mpp_service /dev/dri 2>/dev/null; echo "---"'
run "RKNN/MPP/RGA 运行库"  bash -c "ldconfig -p | grep -Ei 'rknn|rknrt|rockchip_mpp|libmpp|rga' || echo '(未找到相关 .so)'"
run "librknnrt 版本"      bash -c 'strings $(ldconfig -p | grep -oE "/[^ ]*librknnrt[^ ]*" | head -1) 2>/dev/null | grep -iE "librknnrt version|rknn.*version" | head -3 || echo "(librknnrt 未安装或无版本串)"'
run "内核日志(rk3568/npu/rga/mpp)" bash -c 'dmesg 2>/dev/null | grep -Ei "rk3568|rknpu|rga|mpp" | tail -40 || echo "(需 sudo 看 dmesg)"'
run "ffmpeg/ffprobe"      bash -c 'which ffmpeg ffprobe 2>/dev/null; ffprobe -version 2>/dev/null | head -1 || echo "(未装 ffmpeg)"'
run "python3"            bash -c 'python3 --version; python3 -c "import cv2,sys;print(\"opencv\",cv2.__version__)" 2>/dev/null || echo "(无 opencv)"'
run "rknn-toolkit-lite2"  bash -c 'python3 -c "import rknnlite;print(\"rknnlite ok\")" 2>/dev/null || python3 -c "from rknnlite.api import RKNNLite;print(\"rknnlite ok\")" 2>/dev/null || echo "(无 rknn-toolkit-lite2)"'

echo "==== 准入判断(P0 通过条件) ====" | tee -a "$OUT"
echo "[必须]  设备树确认 RK3568" | tee -a "$OUT"
echo "[必须]  /dev/rknpu 存在 或 RKNN runtime 库在" | tee -a "$OUT"
echo "[必须]  MPP/RGA 设备或库可用(硬解码 + 预处理)" | tee -a "$OUT"
echo "[记录]  可用内存/存储、网口、librknnrt 版本" | tee -a "$OUT"
echo "缺任一 → 先出缺口清单+安装方案,不直接开发完整应用。" | tee -a "$OUT"

echo
echo ">>> 报告已存: $OUT"
