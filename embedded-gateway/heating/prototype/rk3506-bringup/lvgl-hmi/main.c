/* RK3506 本地 LVGL 控制面板(配置驱动)—— 裸 DRM + 触摸 + Modbus 读/写 + cJSON。
 *
 * 面板内容不写死:读 /root/panel_config.json(后台/网页配置的单一真相源)→ 自动生成
 * tabview 多页(触摸左右滑动或点页名切屏);每个 tile 按配置读 Modbus 显示/控制。
 * 在 104 上 arm-linux-gnueabihf 交叉静态编译,只依赖 libc(DRM/触摸用裸 ioctl/读 input)。
 */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <sys/select.h>
#include <time.h>
#include <termios.h>
#include <pthread.h>
#include <linux/input.h>
#include "lvgl/lvgl.h"
#include "cJSON.h"

/* ---------- 裸 DRM ---------- */
#define DRM_IOCTL_SET_MASTER 0x641e
#define DRM_IOCTL_MODE_CREATE_DUMB 0xc02064b2
#define DRM_IOCTL_MODE_MAP_DUMB 0xc01064b3
#define DRM_IOCTL_MODE_ADDFB 0xc01c64ae
#define DRM_IOCTL_MODE_SETCRTC 0xc06864a2
#define W 800
#define H 480
#define CONN 75
#define CRTC 72
struct create_dumb { uint32_t height, width, bpp, flags, handle, pitch; uint64_t size; };
struct map_dumb { uint32_t handle, pad; uint64_t offset; };
struct fb_cmd { uint32_t fb_id, width, height, pitch, bpp, depth, handle; };
struct modeinfo { uint32_t clock; uint16_t hdisplay, hsync_start, hsync_end, htotal, hskew,
    vdisplay, vsync_start, vsync_end, vtotal, vscan; uint32_t vrefresh, flags, type; char name[32]; };
struct set_crtc { uint64_t set_connectors_ptr; uint32_t count_connectors, crtc_id, fb_id, x, y,
    gamma_size, mode_valid; struct modeinfo mode; };
static uint8_t *g_fb; static uint32_t g_pitch;

static void drm_init(void) {
    int fd = open("/dev/dri/card0", O_RDWR);
    if (fd < 0) { fprintf(stderr, "open card0: %m\n"); exit(1); }
    ioctl(fd, DRM_IOCTL_SET_MASTER, 0);
    struct create_dumb cd = { .height = H, .width = W, .bpp = 32 };
    if (ioctl(fd, DRM_IOCTL_MODE_CREATE_DUMB, &cd) < 0) { fprintf(stderr, "create_dumb: %m\n"); exit(1); }
    struct fb_cmd fb = { .width = W, .height = H, .pitch = cd.pitch, .bpp = 32, .depth = 24, .handle = cd.handle };
    ioctl(fd, DRM_IOCTL_MODE_ADDFB, &fb);
    struct map_dumb md = { .handle = cd.handle };
    ioctl(fd, DRM_IOCTL_MODE_MAP_DUMB, &md);
    g_fb = mmap(0, cd.size, PROT_READ | PROT_WRITE, MAP_SHARED, fd, md.offset);
    if (g_fb == MAP_FAILED) { fprintf(stderr, "mmap: %m\n"); exit(1); }
    g_pitch = cd.pitch;
    uint32_t conn = CONN;
    struct set_crtc sc = { 0 };
    sc.set_connectors_ptr = (uint64_t)(uintptr_t)&conn;
    sc.count_connectors = 1; sc.crtc_id = CRTC; sc.fb_id = fb.fb_id; sc.mode_valid = 1;
    struct modeinfo m = { .clock = 30000, .hdisplay = 800, .hsync_start = 806, .hsync_end = 811, .htotal = 816,
        .vdisplay = 480, .vsync_start = 485, .vsync_end = 493, .vtotal = 503, .vrefresh = 73, .flags = 0x0a, .type = 0x48 };
    strcpy(m.name, "800x480"); sc.mode = m;
    ioctl(fd, DRM_IOCTL_MODE_SETCRTC, &sc);
}
static void flush_cb(lv_display_t *disp, const lv_area_t *area, uint8_t *px_map) {
    int w = area->x2 - area->x1 + 1; uint32_t *src = (uint32_t *)px_map;
    for (int y = area->y1; y <= area->y2; y++) { memcpy(g_fb + y * g_pitch + area->x1 * 4, src, w * 4); src += w; }
    lv_display_flush_ready(disp);
}
static uint32_t tick_cb(void) { struct timespec ts; clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec * 1000 + ts.tv_nsec / 1000000; }

/* ---------- 触摸 ---------- */
static int touch_fd = -1, tx, ty, tpr;
static void touch_read(lv_indev_t *indev, lv_indev_data_t *data) {
    (void)indev; struct input_event ev;
    while (read(touch_fd, &ev, sizeof(ev)) == (int)sizeof(ev)) {
        if (ev.type == EV_ABS) {
            if (ev.code == ABS_X || ev.code == ABS_MT_POSITION_X) tx = ev.value;
            else if (ev.code == ABS_Y || ev.code == ABS_MT_POSITION_Y) ty = ev.value;
        } else if (ev.type == EV_KEY && ev.code == BTN_TOUCH) tpr = ev.value;
    }
    data->point.x = tx; data->point.y = ty;
    data->state = tpr ? LV_INDEV_STATE_PRESSED : LV_INDEV_STATE_RELEASED;
}

/* ---------- Modbus ---------- */
static int ser_fd = -1;
static void ser_open(const char *dev) {
    ser_fd = open(dev, O_RDWR | O_NOCTTY);
    struct termios t; tcgetattr(ser_fd, &t);
    cfmakeraw(&t); cfsetspeed(&t, B9600);
    t.c_cflag |= CLOCAL | CREAD; t.c_cflag &= ~CRTSCTS;
    t.c_cc[VMIN] = 0; t.c_cc[VTIME] = 0;
    tcsetattr(ser_fd, TCSANOW, &t); tcflush(ser_fd, TCIOFLUSH);
}
static uint16_t crc16(const uint8_t *d, int n) { uint16_t c = 0xFFFF;
    for (int i = 0; i < n; i++) { c ^= d[i]; for (int b = 0; b < 8; b++) c = (c & 1) ? (c >> 1) ^ 0xA001 : c >> 1; }
    return c; }
static int rd_frame(uint8_t *buf, int cap) {
    int len = 0; struct timeval tv = { 0, 150000 };     /* 150ms 够响应,失败更快恢复 */
    for (;;) {
        fd_set rf; FD_ZERO(&rf); FD_SET(ser_fd, &rf);
        if (select(ser_fd + 1, &rf, 0, 0, &tv) <= 0) break;
        int r = read(ser_fd, buf + len, cap - len); if (r > 0) len += r;
        usleep(15000);
        FD_ZERO(&rf); FD_SET(ser_fd, &rf); struct timeval z = { 0, 0 };
        if (select(ser_fd + 1, &rf, 0, 0, &z) <= 0) break;
    }
    return len;
}
static int read_reg(int addr, int reg, int *out) {
    uint8_t req[8] = { addr, 3, reg >> 8, reg, 0, 1 };
    uint16_t c = crc16(req, 6); req[6] = c; req[7] = c >> 8;
    tcflush(ser_fd, TCIOFLUSH); if (write(ser_fd, req, 8) != 8) return -1;
    uint8_t b[64]; int len = rd_frame(b, sizeof(b));
    if (len < 7 || (b[1] & 0x80)) return -1;
    if (crc16(b, len - 2) != (uint16_t)(b[len - 2] | (b[len - 1] << 8))) return -1;
    *out = (b[3] << 8) | b[4]; return 0;
}
static void write_reg(int addr, int reg, int val) {
    uint8_t req[8] = { addr, 6, reg >> 8, reg, val >> 8, val };
    uint16_t c = crc16(req, 6); req[6] = c; req[7] = c >> 8;
    tcflush(ser_fd, TCIOFLUSH); if (write(ser_fd, req, 8) != 8) return;
    uint8_t b[64]; rd_frame(b, sizeof(b));
}

/* 写命令队列:UI 回调只入队(瞬间),串口读/写全在采集线程里做 → UI 永不阻塞 */
typedef struct { int addr, reg, val; } wcmd_t;
static wcmd_t wq[32]; static int wq_head, wq_tail;
static pthread_mutex_t wq_mtx = PTHREAD_MUTEX_INITIALIZER;
static void enqueue_write(int a, int r, int v) {
    pthread_mutex_lock(&wq_mtx);
    int n = (wq_head + 1) % 32;
    if (n != wq_tail) { wq[wq_head] = (wcmd_t){ a, r, v }; wq_head = n; }
    pthread_mutex_unlock(&wq_mtx);
}
static int dequeue_write(wcmd_t *out) {
    int have = 0; pthread_mutex_lock(&wq_mtx);
    if (wq_tail != wq_head) { *out = wq[wq_tail]; wq_tail = (wq_tail + 1) % 32; have = 1; }
    pthread_mutex_unlock(&wq_mtx); return have;
}

/* ---------- 配置驱动 UI ---------- */
#define C_BG 0xf3f6f8
#define C_CARD 0xffffff
#define C_INK 0x1c2733
#define C_MUT 0x6b7785
#define C_LINE 0xdfe6ec
#define C_ACC 0x0f766e
#define WIDGET_VALUE 0
#define WIDGET_SET 1
#define WIDGET_SW 2

typedef struct {
    int addr, reg, write_reg, step, vmin, vmax, widget, inited;
    double scale; char unit[10];
    lv_obj_t *val, *sw; int cur;
    volatile int rawval, ok, ever;    /* 采集线程写,UI 线程读;ever=读到过(缓存最后好值) */
    volatile uint32_t last_ok_ms;     /* 最后一次成功读的时刻,用于判新鲜/变旧 */
} tile_t;
static tile_t tiles[64]; static int ntiles;
typedef struct { tile_t *t; int dir; } btnctx_t;
static btnctx_t btnctxs[16]; static int nbtn;

static char *slurp(const char *p) {
    FILE *f = fopen(p, "rb"); if (!f) return NULL;
    fseek(f, 0, SEEK_END); long n = ftell(f); fseek(f, 0, SEEK_SET);
    char *b = malloc(n + 1); if (fread(b, 1, n, f) != (size_t)n) { /* tolerate */ } b[n] = 0; fclose(f); return b;
}
static void card_style(lv_obj_t *c) {
    lv_obj_set_style_bg_color(c, lv_color_hex(C_CARD), 0);
    lv_obj_set_style_border_color(c, lv_color_hex(C_LINE), 0);
    lv_obj_set_style_border_width(c, 1, 0); lv_obj_set_style_radius(c, 10, 0);
    lv_obj_set_style_pad_all(c, 6, 0); lv_obj_clear_flag(c, LV_OBJ_FLAG_SCROLLABLE);
    lv_obj_set_style_shadow_width(c, 10, 0); lv_obj_set_style_shadow_color(c, lv_color_hex(0x9fb3c8), 0);
    lv_obj_set_style_shadow_opa(c, LV_OPA_20, 0); lv_obj_set_style_shadow_ofs_y(c, 3, 0);
}
static lv_obj_t *lbl(lv_obj_t *p, const lv_font_t *f, uint32_t col, lv_align_t a, int dx, int dy, const char *s) {
    lv_obj_t *l = lv_label_create(p);
    lv_obj_set_style_text_font(l, f, 0); lv_obj_set_style_text_color(l, lv_color_hex(col), 0);
    lv_label_set_text(l, s); lv_obj_align(l, a, dx, dy); return l;
}
static void set_btn_cb(lv_event_t *e) {
    btnctx_t *bc = lv_event_get_user_data(e); tile_t *t = bc->t;
    t->cur += bc->dir * t->step;
    if (t->cur < t->vmin) t->cur = t->vmin; if (t->cur > t->vmax) t->cur = t->vmax;
    enqueue_write(t->addr, t->write_reg, t->cur);
    char s[24]; snprintf(s, sizeof(s), "%.1f", t->cur * t->scale); lv_label_set_text(t->val, s);
}
static void sw_cb(lv_event_t *e) {
    tile_t *t = lv_event_get_user_data(e);
    int on = lv_obj_has_state(lv_event_get_target(e), LV_STATE_CHECKED) ? 1 : 0;
    enqueue_write(t->addr, t->write_reg, on);
}

static void build_tile(lv_obj_t *parent, int x, int y, int w, int h, cJSON *tj) {
    tile_t *t = &tiles[ntiles++];
    t->addr = cJSON_GetObjectItem(tj, "addr")->valueint;
    t->reg = cJSON_GetObjectItem(tj, "reg")->valueint;
    cJSON *sc = cJSON_GetObjectItem(tj, "scale"); t->scale = sc ? sc->valuedouble : 1.0;
    cJSON *u = cJSON_GetObjectItem(tj, "unit"); snprintf(t->unit, sizeof(t->unit), "%s", u ? u->valuestring : "");
    cJSON *wr = cJSON_GetObjectItem(tj, "write_reg"); t->write_reg = wr ? wr->valueint : t->reg;
    cJSON *st = cJSON_GetObjectItem(tj, "step"); t->step = st ? st->valueint : 1;
    cJSON *mn = cJSON_GetObjectItem(tj, "min"); t->vmin = mn ? mn->valueint : 0;
    cJSON *mx = cJSON_GetObjectItem(tj, "max"); t->vmax = mx ? mx->valueint : 65535;
    const char *wg = cJSON_GetObjectItem(tj, "widget")->valuestring;
    t->widget = !strcmp(wg, "setpoint") ? WIDGET_SET : !strcmp(wg, "switch") ? WIDGET_SW : WIDGET_VALUE;
    const char *label = cJSON_GetObjectItem(tj, "label")->valuestring;

    lv_obj_t *c = lv_obj_create(parent); lv_obj_set_pos(c, x, y); lv_obj_set_size(c, w, h); card_style(c);
    lbl(c, &lv_font_montserrat_14, C_MUT, LV_ALIGN_TOP_LEFT, 2, 0, label);
    if (t->widget == WIDGET_SW) {
        t->sw = lv_switch_create(c); lv_obj_set_size(t->sw, 70, 36);
        lv_obj_align(t->sw, LV_ALIGN_BOTTOM_LEFT, 2, -2);
        lv_obj_add_event_cb(t->sw, sw_cb, LV_EVENT_VALUE_CHANGED, t);
    } else if (t->widget == WIDGET_SET) {
        t->val = lbl(c, &lv_font_montserrat_28, C_INK, LV_ALIGN_LEFT_MID, 60, 6, "--");
        lbl(c, &lv_font_montserrat_14, C_MUT, LV_ALIGN_LEFT_MID, 130, 8, t->unit);
        btnctx_t *bm = &btnctxs[nbtn++]; bm->t = t; bm->dir = -1;
        btnctx_t *bp = &btnctxs[nbtn++]; bp->t = t; bp->dir = +1;
        lv_obj_t *bn = lv_button_create(c); lv_obj_set_size(bn, 46, 40); lv_obj_align(bn, LV_ALIGN_LEFT_MID, 4, 6);
        lv_obj_add_event_cb(bn, set_btn_cb, LV_EVENT_CLICKED, bm);
        lv_obj_center(lbl(bn, &lv_font_montserrat_28, 0xffffff, LV_ALIGN_CENTER, 0, 0, "-"));
        lv_obj_t *bp2 = lv_button_create(c); lv_obj_set_size(bp2, 46, 40); lv_obj_align(bp2, LV_ALIGN_RIGHT_MID, -4, 6);
        lv_obj_add_event_cb(bp2, set_btn_cb, LV_EVENT_CLICKED, bp);
        lv_obj_center(lbl(bp2, &lv_font_montserrat_28, 0xffffff, LV_ALIGN_CENTER, 0, 0, "+"));
    } else {
        t->val = lbl(c, &lv_font_montserrat_28, C_INK, LV_ALIGN_LEFT_MID, 2, 8, "--");
        lbl(c, &lv_font_montserrat_14, C_MUT, LV_ALIGN_BOTTOM_RIGHT, -2, -2, t->unit);
    }
}

static void ui_build(const char *cfg_path) {
    lv_obj_t *scr = lv_screen_active();
    lv_obj_set_style_bg_color(scr, lv_color_hex(C_BG), 0); lv_obj_set_style_pad_all(scr, 0, 0);
    char *buf = slurp(cfg_path);
    cJSON *root = buf ? cJSON_Parse(buf) : NULL;
    if (!root) { lbl(scr, &lv_font_montserrat_28, C_INK, LV_ALIGN_CENTER, 0, 0, "config error"); return; }
    lv_obj_t *tv = lv_tabview_create(scr);
    lv_tabview_set_tab_bar_size(tv, 42);
    lv_obj_set_style_bg_color(tv, lv_color_hex(C_BG), 0);
    cJSON *pages = cJSON_GetObjectItem(root, "pages"), *page;
    cJSON_ArrayForEach(page, pages) {
        const char *title = cJSON_GetObjectItem(page, "title")->valuestring;
        lv_obj_t *tab = lv_tabview_add_tab(tv, title);
        lv_obj_set_style_pad_all(tab, 6, 0);
        cJSON *tjs = cJSON_GetObjectItem(page, "tiles"), *tj; int i = 0;
        cJSON_ArrayForEach(tj, tjs) {
            int col = i % 2, row = i / 2;
            build_tile(tab, col * 392, row * 132, 380, 124, tj);
            i++;
        }
    }
}

/* 采集线程:持续读串口,只写缓存(rawval/ok),不碰 LVGL */
static void *poll_thread(void *arg) {
    (void)arg; wcmd_t cmd;
    for (;;) {
        while (dequeue_write(&cmd)) write_reg(cmd.addr, cmd.reg, cmd.val);   /* 先把控制命令发出去(优先) */
        for (int i = 0; i < ntiles; i++) {
            tile_t *t = &tiles[i]; int v;
            while (dequeue_write(&cmd)) write_reg(cmd.addr, cmd.reg, cmd.val); /* 读的间隙也及时处理写,控制更跟手 */
            t->ok = (read_reg(t->addr, t->reg, &v) == 0);
            if (!t->ok) { usleep(40000); t->ok = (read_reg(t->addr, t->reg, &v) == 0); }  /* 失败重试一次 */
            if (t->ok) { t->rawval = v; t->ever = 1; t->last_ok_ms = tick_cb(); }  /* 缓存最后好值 */
            usleep(40000);                               /* 帧间静默,避免请求粘连(RTU 必须) */
        }
        usleep(100000);
    }
    return NULL;
}

/* UI 定时器:只读缓存刷新界面,不做串口 I/O → 触摸丝滑 */
static void ui_tick(lv_timer_t *tm) {
    (void)tm; char s[32];
    for (int i = 0; i < ntiles; i++) {
        tile_t *t = &tiles[i];
        if (t->widget == WIDGET_SW) {
            if (t->ok && !t->inited) { if (t->rawval) lv_obj_add_state(t->sw, LV_STATE_CHECKED);
                else lv_obj_clear_state(t->sw, LV_STATE_CHECKED); t->inited = 1; }
        } else if (t->widget == WIDGET_SET) {
            if (t->ok && !t->inited) { t->cur = t->rawval;
                snprintf(s, sizeof(s), "%.1f", t->rawval * t->scale); lv_label_set_text(t->val, s); t->inited = 1; }
        } else {
            uint32_t col;
            if (!t->ever) { strcpy(s, "--"); col = 0xc0392b; }          /* 从没读到:红 */
            else {
                snprintf(s, sizeof(s), "%.1f", t->rawval * t->scale);
                col = (tick_cb() - t->last_ok_ms > 4000) ? 0xb45309 : C_INK;  /* >4s 没刷新:橙(旧值) */
            }
            lv_label_set_text(t->val, s);
            lv_obj_set_style_text_color(t->val, lv_color_hex(col), 0);
        }
    }
}

int main(int argc, char **argv) {
    const char *dev = argc > 1 ? argv[1] : "/dev/ttyS1";
    const char *cfg = argc > 2 ? argv[2] : "/root/panel_config.json";
    drm_init();
    ser_open(dev);
    touch_fd = open("/dev/input/event0", O_RDONLY | O_NONBLOCK);
    lv_init();
    lv_tick_set_cb(tick_cb);
    lv_display_t *disp = lv_display_create(W, H);
    static uint32_t fbuf[W * 120];
    lv_display_set_buffers(disp, fbuf, NULL, sizeof(fbuf), LV_DISPLAY_RENDER_MODE_PARTIAL);
    lv_display_set_flush_cb(disp, flush_cb);
    if (touch_fd >= 0) {
        lv_indev_t *in = lv_indev_create();
        lv_indev_set_type(in, LV_INDEV_TYPE_POINTER);
        lv_indev_set_read_cb(in, touch_read);
    }
    ui_build(cfg);
    pthread_t th; pthread_create(&th, NULL, poll_thread, NULL);   /* 采集线程 */
    lv_timer_create(ui_tick, 300, NULL);                          /* UI 刷新,不阻塞 */
    for (;;) { lv_timer_handler(); usleep(3000); }
    return 0;
}
