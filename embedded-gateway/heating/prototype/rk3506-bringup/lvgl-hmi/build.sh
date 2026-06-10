#!/bin/bash
# 在 104(x86 Ubuntu)上交叉静态编译 LVGL HMI for RK3506(armv7 hardfloat)。
# 首次把 LVGL 编成 liblvgl.a(慢);之后改 main.c 只重链接(秒级)。
set -e
cd ~/lvgl_hmi

CC=arm-linux-gnueabihf-gcc
FLAGS="-O2 -DLV_CONF_INCLUDE_SIMPLE -I. -I lvgl -march=armv7-a -mfpu=neon -mfloat-abi=hard"

if [ ! -f liblvgl.a ]; then
    cp -f lvgl/lv_conf_template.h lv_conf.h
    sed -i '0,/#if 0/s//#if 1/' lv_conf.h
    sed -i 's/#define LV_COLOR_DEPTH .*/#define LV_COLOR_DEPTH 32/' lv_conf.h   # 配 DRM XRGB8888
    sed -i 's/#define LV_FONT_MONTSERRAT_28 .*/#define LV_FONT_MONTSERRAT_28 1/' lv_conf.h
    sed -i 's/#define LV_FONT_MONTSERRAT_48 .*/#define LV_FONT_MONTSERRAT_48 1/' lv_conf.h
    echo "首次编 LVGL → liblvgl.a(慢)…"
    mkdir -p obj
    for f in $(find lvgl/src -name '*.c'); do
        o="obj/$(echo "$f" | tr '/' '_').o"
        [ -f "$o" ] || $CC $FLAGS -c "$f" -o "$o"
    done
    ar rcs liblvgl.a obj/*.o
fi

echo "链接 main + cJSON + 中文字体…"
$CC $FLAGS -static main.c cJSON.c cjk20.c liblvgl.a -lm -lpthread -o hmi_lvgl
arm-linux-gnueabihf-strip hmi_lvgl
echo "=== 产物 ==="; ls -lh hmi_lvgl; file hmi_lvgl
