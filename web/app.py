#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
徐霞客时空游记系统 — 看板 REST API

为 Web 数据看板提供只读 JSON 接口，直连 MySQL 业务库 xuxiake_travel_db。
涵盖运营统计、景点与游记查询、文献摘录等能力。
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

import pymysql
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from pymysql.cursors import DictCursor

# ---------------------------------------------------------------------------
# 应用配置
# ---------------------------------------------------------------------------

APP_NAME = "徐霞客时空游记 API"
APP_VERSION = "1.0.0"
STATIC_DIR = Path(__file__).resolve().parent / "static"

DB_CONFIG = {
    "host": os.environ.get("MYSQL_HOST", "127.0.0.1"),
    "port": int(os.environ.get("MYSQL_PORT", "3306")),
    "user": os.environ.get("MYSQL_USER", "root"),
    "password": os.environ.get("MYSQL_PASSWORD", ""),
    "database": os.environ.get("MYSQL_DATABASE", "xuxiake_travel_db"),
    "charset": "utf8mb4",
    "cursorclass": DictCursor,
}

app = Flask(__name__, static_folder=str(STATIC_DIR))
CORS(app)


# ---------------------------------------------------------------------------
# 数据访问
# ---------------------------------------------------------------------------

@contextmanager
def get_db():
    """获取数据库连接，请求结束后自动关闭。"""
    conn = pymysql.connect(**DB_CONFIG)
    try:
        yield conn
    finally:
        conn.close()


def query_all(sql: str, params: tuple | None = None) -> list[dict[str, Any]]:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            return list(cur.fetchall())


def query_one(sql: str, params: tuple | None = None) -> dict[str, Any] | None:
    rows = query_all(sql, params)
    return rows[0] if rows else None


def serialize_datetimes(row: dict[str, Any], fields: tuple[str, ...]) -> None:
    """将行内 datetime 字段格式化为 ISO 字符串，便于 JSON 序列化。"""
    for key in fields:
        val = row.get(key)
        if isinstance(val, datetime):
            row[key] = val.isoformat(sep=" ", timespec="seconds")


def error_response(message: str, status: int, code: str) -> tuple[Any, int]:
    return jsonify({"error": message, "code": code}), status


# ---------------------------------------------------------------------------
# REST API
# ---------------------------------------------------------------------------

@app.get("/api/health")
def health():
    """服务与数据库连通性探针。"""
    row = query_one("SELECT 1 AS ok")
    return jsonify({
        "status": "ok" if row else "degraded",
        "service": APP_NAME,
        "version": APP_VERSION,
        "database": DB_CONFIG["database"],
        "connected": bool(row),
    })


@app.get("/api/stats")
def stats():
    """平台核心指标汇总（用户、景点、游记、打卡、文献、互动）。"""
    row = query_one(
        """
        SELECT
            (SELECT COUNT(*) FROM `User`) AS users,
            (SELECT COUNT(*) FROM `Location`) AS locations,
            (SELECT COUNT(*) FROM `Location` WHERE IsXuXiake = 1) AS xuxiake_locations,
            (SELECT COUNT(*) FROM `Literature`) AS literature,
            (SELECT COUNT(*) FROM `Travelog`) AS travelogs,
            (SELECT COUNT(*) FROM `Travelog_Location`) AS checkins,
            (SELECT COALESCE(SUM(Likes), 0) FROM `Travelog`) AS total_likes
        """
    )
    return jsonify(row)


@app.get("/api/locations/provinces")
def province_stats():
    """各省级行政区景点数量及徐霞客足迹分布。"""
    rows = query_all(
        """
        SELECT Province,
               COUNT(*) AS total,
               SUM(IsXuXiake) AS xuxiake_count
        FROM `Location`
        GROUP BY Province
        ORDER BY total DESC
        """
    )
    return jsonify(rows)


@app.get("/api/locations/top-checkins")
def top_checkins():
    """按游记打卡次数排序的热门景点。"""
    limit = min(int(request.args.get("limit", 12)), 50)
    rows = query_all(
        """
        SELECT l.LocationID, l.LocName, l.Province, l.IsXuXiake,
               COUNT(tl.TravelogID) AS checkin_count
        FROM `Location` l
        JOIN `Travelog_Location` tl ON l.LocationID = tl.LocationID
        GROUP BY l.LocationID, l.LocName, l.Province, l.IsXuXiake
        ORDER BY checkin_count DESC
        LIMIT %s
        """,
        (limit,),
    )
    return jsonify(rows)


@app.get("/api/locations")
def locations():
    """
    景点分页列表。
    查询参数：province, is_xuxiake (0|1), limit, offset
    """
    province = request.args.get("province")
    is_xuxiake = request.args.get("is_xuxiake")
    limit = min(int(request.args.get("limit", 50)), 200)
    offset = max(int(request.args.get("offset", 0)), 0)

    sql = """
        SELECT LocationID, LocName, Province, OpeningHours, IsXuXiake,
               LEFT(Description, 120) AS Description
        FROM `Location`
        WHERE 1=1
    """
    params: list[Any] = []
    if province:
        sql += " AND Province = %s"
        params.append(province)
    if is_xuxiake is not None and is_xuxiake != "":
        sql += " AND IsXuXiake = %s"
        params.append(1 if is_xuxiake in ("1", "true", "yes") else 0)
    sql += " ORDER BY IsXuXiake DESC, LocName LIMIT %s OFFSET %s"
    params.extend([limit, offset])
    return jsonify(query_all(sql, tuple(params)))


@app.get("/api/travelogs/latest")
def latest_travelogs():
    """按发布时间倒序返回最新游记摘要。"""
    limit = min(int(request.args.get("limit", 20)), 100)
    rows = query_all(
        """
        SELECT t.TravelogID, t.Title, t.PublishTime, t.Likes,
               u.Username,
               (SELECT COUNT(*) FROM `Travelog_Location` tl
                WHERE tl.TravelogID = t.TravelogID) AS spot_count
        FROM `Travelog` t
        JOIN `User` u ON t.UserID = u.UserID
        ORDER BY t.PublishTime DESC
        LIMIT %s
        """,
        (limit,),
    )
    for row in rows:
        serialize_datetimes(row, ("PublishTime",))
    return jsonify(rows)


@app.get("/api/travelogs/<int:travelog_id>")
def travelog_detail(travelog_id: int):
    """单篇游记详情，含关联打卡景点与时间线。"""
    row = query_one(
        """
        SELECT t.TravelogID, t.Title, t.Content, t.PublishTime, t.Likes,
               u.UserID, u.Username
        FROM `Travelog` t
        JOIN `User` u ON t.UserID = u.UserID
        WHERE t.TravelogID = %s
        """,
        (travelog_id,),
    )
    if not row:
        return error_response("未找到该游记", 404, "TRAVELOG_NOT_FOUND")

    serialize_datetimes(row, ("PublishTime",))

    spots = query_all(
        """
        SELECT l.LocationID, l.LocName, l.Province, l.IsXuXiake, tl.CheckInTime
        FROM `Travelog_Location` tl
        JOIN `Location` l ON tl.LocationID = l.LocationID
        WHERE tl.TravelogID = %s
        ORDER BY tl.CheckInTime
        """,
        (travelog_id,),
    )
    for spot in spots:
        serialize_datetimes(spot, ("CheckInTime",))
    row["checkins"] = spots
    return jsonify(row)


@app.get("/api/locations/<int:location_id>/literature")
def location_literature(location_id: int):
    """指定景点下的历史文献摘录列表。"""
    loc = query_one(
        "SELECT LocationID, LocName, Province, IsXuXiake FROM `Location` WHERE LocationID = %s",
        (location_id,),
    )
    if not loc:
        return error_response("未找到该景点", 404, "LOCATION_NOT_FOUND")

    literature = query_all(
        """
        SELECT LitID, OriginalText, TranslateInfo, WriteDate
        FROM `Literature`
        WHERE LocationID = %s
        ORDER BY LitID
        LIMIT 20
        """,
        (location_id,),
    )
    return jsonify({"location": loc, "literature": literature})


# ---------------------------------------------------------------------------
# 静态资源（看板前端）
# ---------------------------------------------------------------------------

@app.get("/")
def index():
    return send_from_directory(STATIC_DIR, "index.html")


@app.get("/<path:path>")
def static_files(path: str):
    if (STATIC_DIR / path).is_file():
        return send_from_directory(STATIC_DIR, path)
    return send_from_directory(STATIC_DIR, "index.html")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8081"))
    app.run(host="0.0.0.0", port=port, debug=False)
