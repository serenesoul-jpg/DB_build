#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""徐霞客时空游记系统 — 数据可视化 API"""

from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path

import pymysql
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from pymysql.cursors import DictCursor

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


@contextmanager
def get_db():
    conn = pymysql.connect(**DB_CONFIG)
    try:
        yield conn
    finally:
        conn.close()


def query_all(sql: str, params: tuple | None = None) -> list[dict]:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            return list(cur.fetchall())


def query_one(sql: str, params: tuple | None = None) -> dict | None:
    rows = query_all(sql, params)
    return rows[0] if rows else None


@app.get("/api/health")
def health():
    row = query_one("SELECT 1 AS ok")
    return jsonify({"status": "ok", "database": DB_CONFIG["database"], "connected": bool(row)})


@app.get("/api/stats")
def stats():
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
    limit = min(int(request.args.get("limit", 12)), 50)
    rows = query_all(
        f"""
        SELECT l.LocationID, l.LocName, l.Province, l.IsXuXiake,
               COUNT(tl.TravelogID) AS checkin_count
        FROM `Location` l
        JOIN `Travelog_Location` tl ON l.LocationID = tl.LocationID
        GROUP BY l.LocationID, l.LocName, l.Province, l.IsXuXiake
        ORDER BY checkin_count DESC
        LIMIT {limit}
        """
    )
    return jsonify(rows)


@app.get("/api/locations")
def locations():
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
    params: list = []
    if province:
        sql += " AND Province = %s"
        params.append(province)
    if is_xuxiake is not None and is_xuxiake != "":
        sql += " AND IsXuXiake = %s"
        params.append(1 if is_xuxiake in ("1", "true", "yes") else 0)
    sql += " ORDER BY IsXuXiake DESC, LocName LIMIT %s OFFSET %s"
    params.extend([limit, offset])
    rows = query_all(sql, tuple(params))
    return jsonify(rows)


@app.get("/api/travelogs/latest")
def latest_travelogs():
    limit = min(int(request.args.get("limit", 20)), 100)
    rows = query_all(
        f"""
        SELECT t.TravelogID, t.Title, t.PublishTime, t.Likes,
               u.Username,
               (SELECT COUNT(*) FROM `Travelog_Location` tl
                WHERE tl.TravelogID = t.TravelogID) AS spot_count
        FROM `Travelog` t
        JOIN `User` u ON t.UserID = u.UserID
        ORDER BY t.PublishTime DESC
        LIMIT {limit}
        """
    )
    for r in rows:
        if r.get("PublishTime"):
            r["PublishTime"] = r["PublishTime"].isoformat(sep=" ", timespec="seconds")
    return jsonify(rows)


@app.get("/api/travelogs/<int:travelog_id>")
def travelog_detail(travelog_id: int):
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
        return jsonify({"error": "游记不存在"}), 404
    if row.get("PublishTime"):
        row["PublishTime"] = row["PublishTime"].isoformat(sep=" ", timespec="seconds")

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
    for s in spots:
        if s.get("CheckInTime"):
            s["CheckInTime"] = s["CheckInTime"].isoformat(sep=" ", timespec="seconds")
    row["checkins"] = spots
    return jsonify(row)


@app.get("/api/locations/<int:location_id>/literature")
def location_literature(location_id: int):
    loc = query_one(
        "SELECT LocationID, LocName, Province, IsXuXiake FROM `Location` WHERE LocationID = %s",
        (location_id,),
    )
    if not loc:
        return jsonify({"error": "景点不存在"}), 404
    lit = query_all(
        """
        SELECT LitID, OriginalText, TranslateInfo, WriteDate
        FROM `Literature`
        WHERE LocationID = %s
        ORDER BY LitID
        LIMIT 20
        """,
        (location_id,),
    )
    return jsonify({"location": loc, "literature": lit})


@app.get("/")
def index():
    return send_from_directory(STATIC_DIR, "index.html")


@app.get("/<path:path>")
def static_files(path: str):
    if (STATIC_DIR / path).is_file():
        return send_from_directory(STATIC_DIR, path)
    return send_from_directory(STATIC_DIR, "index.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8081")), debug=False)
