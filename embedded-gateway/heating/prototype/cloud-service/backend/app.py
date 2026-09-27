#!/usr/bin/env python3
"""供热运营后管 · FastAPI 后端（阶段 C）。

把阶段 B 已验对的四类报表 SQL 包成接口 + JWT 登录 + 站点元数据维护
+ 报警确认/解除 + Excel 导出，并同源托管单文件前端（static/index.html）。

口径与 reports/*.sql 完全一致——本文件是它们的 HTTP 封装，不另立口径。

依赖： pip install -r requirements.txt
运行： HEATING_DSN=... uvicorn app:app --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import datetime as dt
import hashlib
import hmac
import io
import os
import secrets

import jwt
import psycopg2
import psycopg2.extras
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# --------------------------------------------------------------------------- #
# 配置
# --------------------------------------------------------------------------- #
def _default_dsn() -> str:
    pw = ""
    try:
        with open("/var/lib/heating/.dbpass") as f:
            pw = f.read().strip()
    except OSError:
        pass
    return f"host=127.0.0.1 dbname=heating user=heating password={pw}"


DSN = os.environ.get("HEATING_DSN") or _default_dsn()
JWT_SECRET = os.environ.get("HEATING_JWT_SECRET", "change-me-in-prod")
JWT_ALG = "HS256"
TOKEN_TTL_H = 12
HERE = os.path.dirname(os.path.abspath(__file__))


def db():
    con = psycopg2.connect(DSN, cursor_factory=psycopg2.extras.RealDictCursor)
    con.autocommit = True
    return con


# --------------------------------------------------------------------------- #
# 口令 / JWT
# --------------------------------------------------------------------------- #
def hash_pwd(pwd: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(8)
    h = hashlib.pbkdf2_hmac("sha256", pwd.encode(), bytes.fromhex(salt), 100_000).hex()
    return f"{salt}${h}"


def verify_pwd(pwd: str, stored: str) -> bool:
    try:
        salt, _ = stored.split("$")
    except ValueError:
        return False
    return hmac.compare_digest(hash_pwd(pwd, salt), stored)


def make_token(username: str, role: str, scope: str | None) -> str:
    payload = {
        "sub": username, "role": role, "scope": scope or "",
        "exp": dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=TOKEN_TTL_H),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)


bearer = HTTPBearer(auto_error=True)


def current_user(cred: HTTPAuthorizationCredentials = Depends(bearer)) -> dict:
    try:
        p = jwt.decode(cred.credentials, JWT_SECRET, algorithms=[JWT_ALG])
    except jwt.PyJWTError:
        raise HTTPException(401, "无效或过期的登录")
    return {"username": p["sub"], "role": p["role"],
            "scope": [s for s in p.get("scope", "").split(",") if s]}


def require_admin(user: dict = Depends(current_user)) -> dict:
    if user["role"] != "admin":
        raise HTTPException(403, "需要管理员权限")
    return user


def scoped_stations(user: dict) -> list[str] | None:
    """返回该用户可见站点列表；None 表示全部（admin 或未设范围）。"""
    if user["role"] == "admin" or not user["scope"]:
        return None
    return user["scope"]


# --------------------------------------------------------------------------- #
# 启动：建用户表 + 种子 admin/admin
# --------------------------------------------------------------------------- #
def init_users():
    with db() as con, con.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS app_user (
                username   text PRIMARY KEY,
                pwd_hash   text NOT NULL,
                role       text NOT NULL DEFAULT 'viewer',
                scope      text,            -- 逗号分隔 device_id；空=全部
                created_at timestamptz NOT NULL DEFAULT now()
            )""")
        cur.execute("SELECT count(*) AS n FROM app_user")
        if cur.fetchone()["n"] == 0:
            cur.execute(
                "INSERT INTO app_user (username, pwd_hash, role) VALUES (%s,%s,'admin')",
                ("admin", hash_pwd("admin")))


# --------------------------------------------------------------------------- #
# 报表查询（口径同 reports/*.sql）
# --------------------------------------------------------------------------- #
def q(con, sql, params):
    with con.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def report_daily(con, station, day):
    fields = q(con, """
        SELECT m.label_cn, m.unit,
               round(avg(t.value)::numeric,2) AS avg,
               round(min(t.value)::numeric,2) AS min,
               round(max(t.value)::numeric,2) AS max,
               count(*) AS n
        FROM telemetry t JOIN metric_def m ON m.metric=t.metric AND m.kind='instant'
        WHERE t.device_id=%(s)s AND t.quality='good'
          AND (t.ts AT TIME ZONE 'Asia/Shanghai')::date=%(d)s
        GROUP BY m.metric, m.label_cn, m.unit ORDER BY m.metric""",
        {"s": station, "d": day})
    dtrow = q(con, """
        SELECT round((avg(value) FILTER (WHERE metric='pri_supply_temp')
                    - avg(value) FILTER (WHERE metric='pri_return_temp'))::numeric,2) AS pri_dt,
               round((avg(value) FILTER (WHERE metric='sec_supply_temp')
                    - avg(value) FILTER (WHERE metric='sec_return_temp'))::numeric,2) AS sec_dt
        FROM telemetry WHERE device_id=%(s)s AND quality='good'
          AND (ts AT TIME ZONE 'Asia/Shanghai')::date=%(d)s""",
        {"s": station, "d": day})
    device = q(con, """
        SELECT equip, round(run_minutes::numeric,1) AS run_minutes,
               start_count, fault_count
        FROM device_status_daily WHERE device_id=%(s)s AND day=%(d)s""",
        {"s": station, "d": day})
    return {"fields": fields, "dt": dtrow[0] if dtrow else {}, "device": device}


def report_settlement(con, station, ym):
    return q(con, """
        SELECT md.device_id,
               round(sum(md.delta) FILTER (WHERE md.metric='heat_total')::numeric,3)   AS heat_gj,
               round(sum(md.delta) FILTER (WHERE md.metric='refill_total')::numeric,2) AS refill_m3,
               sm.heat_area_m2,
               CASE WHEN sm.heat_area_m2>0 THEN
                 round((sum(md.delta) FILTER (WHERE md.metric='heat_total')/sm.heat_area_m2*1000)::numeric,3)
               END AS unit_heat_mj_m2
        FROM meter_daily md JOIN station_meta sm ON sm.device_id=md.device_id
        WHERE md.device_id=%(s)s AND to_char(md.day,'YYYY-MM')=%(ym)s AND NOT md.rollover
        GROUP BY md.device_id, sm.heat_area_m2""",
        {"s": station, "ym": ym})


def report_energy_saving(con, station, dfrom, dto):
    return q(con, """
        WITH heat AS (
            SELECT device_id, day, sum(delta) AS heat_gj
            FROM meter_daily WHERE metric='heat_total' AND NOT rollover
            GROUP BY device_id, day)
        SELECT h.device_id,
               round(sum(h.heat_gj)::numeric,3) AS heat_gj,
               round(sum(w.hdd)::numeric,2) AS hdd,
               sm.heat_area_m2, sm.retrofit_date,
               round((sum(h.heat_gj)/(sm.heat_area_m2*NULLIF(sum(w.hdd),0))*1e6)::numeric,4) AS norm_heat
        FROM heat h JOIN weather_daily w ON w.device_id=h.device_id AND w.day=h.day
                    JOIN station_meta sm ON sm.device_id=h.device_id
        WHERE h.device_id=%(s)s AND h.day BETWEEN %(f)s AND %(t)s
        GROUP BY h.device_id, sm.heat_area_m2, sm.retrofit_date""",
        {"s": station, "f": dfrom, "t": dto})


def report_data_quality(con, dfrom, dto, stations=None):
    filt = "AND device_id = ANY(%(st)s)" if stations else ""
    p = {"f": dfrom, "t": dto, "st": stations}
    completeness = q(con, f"""
        WITH frames AS (
            SELECT device_id, count(DISTINCT seq) AS got, min(ts) AS t0, max(ts) AS t1
            FROM telemetry WHERE ts BETWEEN %(f)s AND %(t)s AND NOT replay {filt}
            GROUP BY device_id)
        SELECT f.device_id, f.got AS got_frames,
               round((extract(epoch FROM (f.t1-f.t0))/sm.report_interval_s+1)::numeric,0) AS expect_frames,
               round((100.0*f.got/NULLIF(extract(epoch FROM (f.t1-f.t0))/sm.report_interval_s+1,0))::numeric,1) AS pct
        FROM frames f JOIN station_meta sm ON sm.device_id=f.device_id ORDER BY f.device_id""", p)
    badrate = q(con, f"""
        SELECT device_id, count(*) AS total,
               round((100.0*count(*) FILTER (WHERE quality<>'good')/count(*))::numeric,2) AS pct
        FROM telemetry WHERE ts BETWEEN %(f)s AND %(t)s {filt}
        GROUP BY device_id ORDER BY device_id""", p)
    alarms = q(con, f"""
        SELECT device_id, count(*) AS n,
               count(*) FILTER (WHERE status='cleared') AS cleared,
               round(avg(extract(epoch FROM (cleared_ts-ts))/60) FILTER (WHERE cleared_ts IS NOT NULL)::numeric,1) AS avg_min
        FROM alarm WHERE ts BETWEEN %(f)s AND %(t)s {filt}
        GROUP BY device_id ORDER BY device_id""", p)
    return {"completeness": completeness, "badrate": badrate, "alarms": alarms}


# --------------------------------------------------------------------------- #
# FastAPI
# --------------------------------------------------------------------------- #
app = FastAPI(title="供热运营后管 API")


@app.on_event("startup")
def _startup():
    init_users()


class LoginIn(BaseModel):
    username: str
    password: str


@app.post("/api/login")
def login(body: LoginIn):
    with db() as con, con.cursor() as cur:
        cur.execute("SELECT * FROM app_user WHERE username=%s", (body.username,))
        u = cur.fetchone()
    if not u or not verify_pwd(body.password, u["pwd_hash"]):
        raise HTTPException(401, "用户名或密码错误")
    return {"token": make_token(u["username"], u["role"], u["scope"]),
            "role": u["role"], "username": u["username"]}


@app.get("/api/me")
def me(user: dict = Depends(current_user)):
    return user


@app.get("/api/health")
def health():
    try:
        with db() as con, con.cursor() as cur:
            cur.execute("SELECT 1")
        return {"ok": True}
    except Exception as e:
        raise HTTPException(503, f"db down: {e}")


@app.get("/api/stations")
def stations(user: dict = Depends(current_user)):
    scope = scoped_stations(user)
    sql = """
        SELECT s.device_id, s.online, s.last_seq, s.last_seen,
               m.heat_area_m2, m.building_count, m.household_count,
               m.design_sec_supply_temp, m.report_interval_s, m.retrofit_date
        FROM station s LEFT JOIN station_meta m ON m.device_id=s.device_id
        {filt} ORDER BY s.device_id"""
    if scope:
        rows = q(db(), sql.format(filt="WHERE s.device_id = ANY(%(st)s)"), {"st": scope})
    else:
        rows = q(db(), sql.format(filt=""), {})
    return rows


class MetaIn(BaseModel):
    heat_area_m2: float | None = None
    building_count: int | None = None
    household_count: int | None = None
    design_pri_supply_temp: float | None = None
    design_pri_return_temp: float | None = None
    design_sec_supply_temp: float | None = None
    design_sec_return_temp: float | None = None
    design_load_kw: float | None = None
    report_interval_s: int = 30
    retrofit_date: str | None = None
    commissioned_date: str | None = None


@app.put("/api/stations/{device_id}/meta")
def upsert_meta(device_id: str, body: MetaIn, user: dict = Depends(require_admin)):
    d = body.model_dump()
    d["device_id"] = device_id
    with db() as con, con.cursor() as cur:
        cur.execute("""
            INSERT INTO station_meta
              (device_id, heat_area_m2, building_count, household_count,
               design_pri_supply_temp, design_pri_return_temp,
               design_sec_supply_temp, design_sec_return_temp,
               design_load_kw, report_interval_s, retrofit_date, commissioned_date, updated_at)
            VALUES (%(device_id)s,%(heat_area_m2)s,%(building_count)s,%(household_count)s,
               %(design_pri_supply_temp)s,%(design_pri_return_temp)s,
               %(design_sec_supply_temp)s,%(design_sec_return_temp)s,
               %(design_load_kw)s,%(report_interval_s)s,
               NULLIF(%(retrofit_date)s,'')::date, NULLIF(%(commissioned_date)s,'')::date, now())
            ON CONFLICT (device_id) DO UPDATE SET
               heat_area_m2=excluded.heat_area_m2, building_count=excluded.building_count,
               household_count=excluded.household_count,
               design_pri_supply_temp=excluded.design_pri_supply_temp,
               design_pri_return_temp=excluded.design_pri_return_temp,
               design_sec_supply_temp=excluded.design_sec_supply_temp,
               design_sec_return_temp=excluded.design_sec_return_temp,
               design_load_kw=excluded.design_load_kw,
               report_interval_s=excluded.report_interval_s,
               retrofit_date=excluded.retrofit_date,
               commissioned_date=excluded.commissioned_date, updated_at=now()""", d)
    return {"ok": True}


@app.get("/api/reports/daily")
def api_daily(station: str, day: str, user: dict = Depends(current_user)):
    return report_daily(db(), station, day)


@app.get("/api/reports/settlement")
def api_settlement(station: str, ym: str, user: dict = Depends(current_user)):
    return report_settlement(db(), station, ym)


@app.get("/api/reports/energy_saving")
def api_energy(station: str, dfrom: str, dto: str, user: dict = Depends(current_user)):
    return report_energy_saving(db(), station, dfrom, dto)


@app.get("/api/reports/data_quality")
def api_quality(dfrom: str, dto: str, user: dict = Depends(current_user)):
    return report_data_quality(db(), dfrom, dto, scoped_stations(user))


@app.get("/api/alarms")
def alarms(status: str | None = None, user: dict = Depends(current_user)):
    scope = scoped_stations(user)
    conds, p = [], {}
    if status:
        conds.append("status=%(st)s"); p["st"] = status
    if scope:
        conds.append("device_id = ANY(%(sc)s)"); p["sc"] = scope
    where = ("WHERE " + " AND ".join(conds)) if conds else ""
    return q(db(), f"""SELECT id, device_id, ts, alarm_id, message, status,
                              acked_at, acked_by, cleared_ts
                       FROM alarm {where} ORDER BY ts DESC LIMIT 200""", p)


@app.post("/api/alarms/{aid}/ack")
def ack(aid: int, user: dict = Depends(current_user)):
    with db() as con, con.cursor() as cur:
        cur.execute("UPDATE alarm SET status='acked', acked_at=now(), acked_by=%s "
                    "WHERE id=%s AND status='active'", (user["username"], aid))
    return {"ok": True}


@app.post("/api/alarms/{aid}/clear")
def clear(aid: int, user: dict = Depends(current_user)):
    with db() as con, con.cursor() as cur:
        cur.execute("UPDATE alarm SET status='cleared', cleared_at=now(), "
                    "cleared_ts=now() WHERE id=%s", (aid,))
    return {"ok": True}


# --------------------------------------------------------------------------- #
# Excel 导出
# --------------------------------------------------------------------------- #
def _xlsx(sheets: dict) -> io.BytesIO:
    from openpyxl import Workbook
    wb = Workbook()
    wb.remove(wb.active)
    for name, rows in sheets.items():
        ws = wb.create_sheet(name[:31])
        if rows:
            headers = list(rows[0].keys())
            ws.append(headers)
            for r in rows:
                ws.append([r.get(h) for h in headers])
        else:
            ws.append(["(无数据)"])
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


@app.get("/api/export/{rtype}")
def export(rtype: str, station: str = "", day: str = "", ym: str = "",
           dfrom: str = "", dto: str = "", user: dict = Depends(current_user)):
    con = db()
    if rtype == "daily":
        r = report_daily(con, station, day)
        sheets = {"工况": r["fields"], "温差": [r["dt"]] if r["dt"] else [], "设备状态": r["device"]}
        fn = f"daily_{station}_{day}.xlsx"
    elif rtype == "settlement":
        sheets = {"结算": report_settlement(con, station, ym)}
        fn = f"settlement_{station}_{ym}.xlsx"
    elif rtype == "energy_saving":
        sheets = {"节能": report_energy_saving(con, station, dfrom, dto)}
        fn = f"energy_{station}.xlsx"
    elif rtype == "data_quality":
        r = report_data_quality(con, dfrom, dto, scoped_stations(user))
        sheets = {"完整率": r["completeness"], "坏点率": r["badrate"], "报警": r["alarms"]}
        fn = "data_quality.xlsx"
    else:
        raise HTTPException(404, "未知报表类型")
    buf = _xlsx(sheets)
    return StreamingResponse(
        buf, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={fn}"})


# 同源托管前端（放最后，避免吃掉 /api 路由）
app.mount("/", StaticFiles(directory=os.path.join(HERE, "static"), html=True), name="static")
