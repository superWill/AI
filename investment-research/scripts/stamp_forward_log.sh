#!/bin/bash
# 给前向记录打 OpenTimestamps 时间戳（锚到比特币）。
#
# 做什么：取 HEAD 提交里的笔记文件，把它的 SHA-256 提交给公共日历服务器，
# 证明文件（.ots）存到 data/timestamps/。发出去的只有哈希，文件内容不出本机。
#
# 用法：
#   scripts/stamp_forward_log.sh            # 打戳（笔记有未提交改动时拒绝执行）
#   scripts/stamp_forward_log.sh upgrade    # 几小时后跑：把比特币区块证明补进 .ots
#   scripts/stamp_forward_log.sh verify     # 逐个核对已有证明
#
# 什么时候打：前向记录新增或改动判决行并提交之后。填「复核结果」之前的那一版必须有戳。
set -euo pipefail
cd "$(dirname "$0")/.."

NOTE="notes/2026-11-16-value-investor-agent-eval.md"
DIR="data/timestamps"
OTS=".venv/bin/ots"
LOG="$DIR/INDEX.tsv"
mkdir -p "$DIR"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

case "${1:-stamp}" in
stamp)
  if ! git diff --quiet HEAD -- "$NOTE"; then
    echo "笔记有未提交的改动，先提交再打戳。" >&2
    exit 1
  fi
  COMMIT="$(git rev-parse HEAD)"
  SHORT="${COMMIT:0:7}"
  OUT="$DIR/$(date +%F)-$SHORT-forward-log.ots"
  if [ -e "$OUT" ]; then
    echo "已存在：$OUT" >&2
    exit 1
  fi
  git show "HEAD:investment-research/$NOTE" >"$TMP/note.md"
  SHA="$(shasum -a 256 "$TMP/note.md" | cut -d' ' -f1)"
  "$OTS" stamp "$TMP/note.md"
  mv "$TMP/note.md.ots" "$OUT"
  [ -e "$LOG" ] || printf 'date\tcommit\tsha256\tproof\n' >"$LOG"
  printf '%s\t%s\t%s\t%s\n' "$(date +%F)" "$COMMIT" "$SHA" "$(basename "$OUT")" >>"$LOG"
  echo "已打戳：$OUT"
  echo "sha256：$SHA"
  echo "几小时后跑：scripts/stamp_forward_log.sh upgrade"
  ;;
upgrade)
  for f in "$DIR"/*.ots; do
    "$OTS" upgrade "$f" || true
  done
  rm -f "$DIR"/*.ots.bak
  ;;
verify)
  tail -n +2 "$LOG" | while IFS=$'\t' read -r _ commit sha proof; do
    git show "$commit:investment-research/$NOTE" >"$TMP/note.md"
    got="$(shasum -a 256 "$TMP/note.md" | cut -d' ' -f1)"
    if [ "$got" != "$sha" ]; then
      echo "✗ ${proof}：提交 ${commit:0:7} 里的文件哈希与记录不符"
      continue
    fi
    echo "— ${proof}（提交 ${commit:0:7}）"
    "$OTS" verify -f "$TMP/note.md" "$DIR/$proof" || true
  done
  ;;
*)
  echo "用法：$0 [stamp|upgrade|verify]" >&2
  exit 2
  ;;
esac
