#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
徐霞客时空游记系统 — 测试数据生成脚本
文档编号：05

依赖安装：
    pip install faker pymysql

使用前请先执行 04_物理设计与建表语句.sql 创建库表。

数据规模（默认，满足课程要求）：
    User              >= 1,000
    Travelog          >= 5,000
    Travelog_Location >= 10,000
    Location / Literature 适量

用法：
    python 05_测试数据生成脚本.py
    python 05_测试数据生成脚本.py --host 127.0.0.1 --user root --password your_pass
    python 05_测试数据生成脚本.py --export-sql documents/05_test_data.sql
"""

from __future__ import annotations

import argparse
import hashlib
import os
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Iterable, Sequence

try:
    from faker import Faker
except ImportError:
    print("请先安装依赖: pip install faker pymysql", file=sys.stderr)
    sys.exit(1)

# ---------------------------------------------------------------------------
# 配置
# ---------------------------------------------------------------------------

def _load_dotenv() -> None:
    """从项目根目录 .env 加载 MYSQL_USER / MYSQL_PASSWORD（无 python-dotenv 依赖）。"""
    for base in (Path(__file__).resolve().parent.parent, Path.cwd()):
        env_path = base / ".env"
        if not env_path.is_file():
            continue
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key, val = key.strip(), val.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = val
        break


_load_dotenv()

DB_CONFIG = {
    "host": os.environ.get("MYSQL_HOST", "127.0.0.1"),
    "port": int(os.environ.get("MYSQL_PORT", "3306")),
    "user": os.environ.get("MYSQL_USER", "root"),
    "password": os.environ.get("MYSQL_PASSWORD", ""),
    "database": os.environ.get("MYSQL_DATABASE", "xuxiake_travel_db"),
    "charset": "utf8mb4",
}

NUM_USERS = 1200
NUM_LOCATIONS = 360
NUM_TRAVELOGS = 5500
# 每篇游记至少 2 个打卡点 => 5500 * 2 = 11000 >= 10000
CHECKINS_PER_TRAVELOG = 2
NUM_CHECKINS = NUM_TRAVELOGS * CHECKINS_PER_TRAVELOG

BATCH_SIZE = 500
SEED = 20260526

# 徐霞客足迹相关景点（部分为真实游历地名）
XUXIAKE_LOCATIONS: list[tuple[str, str]] = [
    ("黄山", "安徽省"),
    ("白岳", "安徽省"),
    ("九华山", "安徽省"),
    ("天柱山", "安徽省"),
    ("庐山", "江西省"),
    ("三清山", "江西省"),
    ("武夷山", "福建省"),
    ("雁荡山", "浙江省"),
    ("天台山", "浙江省"),
    ("四明山", "浙江省"),
    ("天姥山", "浙江省"),
    ("莫干山", "浙江省"),
    ("西湖", "浙江省"),
    ("灵岩寺", "山东省"),
    ("泰山", "山东省"),
    ("嵩山", "河南省"),
    ("华山", "陕西省"),
    ("五台山", "山西省"),
    ("恒山", "山西省"),
    ("峨眉山", "四川省"),
    ("青城山", "四川省"),
    ("都江堰", "四川省"),
    ("石林", "云南省"),
    ("鸡足山", "云南省"),
    ("丽江", "云南省"),
    ("大理", "云南省"),
    ("泸沽湖", "云南省"),
    ("漓江", "广西壮族自治区"),
    ("阳朔", "广西壮族自治区"),
    ("衡山", "湖南省"),
    ("武陵源", "湖南省"),
    ("武当山", "湖北省"),
    ("神农架", "湖北省"),
    ("三峡", "湖北省"),
    ("丹霞山", "广东省"),
    ("罗浮山", "广东省"),
    ("鼎湖山", "广东省"),
    ("普陀山", "浙江省"),
    ("天童寺", "浙江省"),
    ("阿育王寺", "浙江省"),
    ("雪窦山", "浙江省"),
    ("天童山", "浙江省"),
    ("烂柯山", "浙江省"),
    ("江郎山", "浙江省"),
    ("仙霞岭", "浙江省"),
    ("灵峰", "浙江省"),
    ("大龙湫", "浙江省"),
    ("灵岩", "浙江省"),
    ("观音洞", "浙江省"),
]

PROVINCES = [
    "北京市", "天津市", "河北省", "山西省", "内蒙古自治区",
    "辽宁省", "吉林省", "黑龙江省", "上海市", "江苏省",
    "浙江省", "安徽省", "福建省", "江西省", "山东省",
    "河南省", "湖北省", "湖南省", "广东省", "广西壮族自治区",
    "海南省", "重庆市", "四川省", "贵州省", "云南省",
    "西藏自治区", "陕西省", "甘肃省", "青海省", "宁夏回族自治区",
    "新疆维吾尔自治区",
]

OPENING_HOURS_POOL = [
    "06:00—18:00", "08:00—17:00", "08:30—17:30",
    "全天开放", "07:00—19:00", "09:00—16:00",
]

LITERATURE_SNIPPETS = [
    ("崇祯元年正月，余自浙入闽，历游雁荡诸山。", "正月入闽，开始考察雁荡山一线。"),
    ("越数日，登天柱，览其奇胜，记于册。", "数日后登天柱山，记录奇观。"),
    ("循江而下，至阳朔，江面开阔，峰林夹岸。", "顺流至阳朔，描述峰林夹岸。"),
    ("宿鸡足山，闻晨钟暮鼓，考寺志。", "宿于鸡足山，查阅寺志。"),
    ("过武夷，九曲溪流，曲曲有异。", "游历武夷九曲溪。"),
    ("登黄山，雾散日出，云海翻涌。", "黄山日出与云海之景。"),
]

WRITE_DATES = [
    "崇祯九年", "崇祯十年", "天启四年", "万历四十四年",
    "1616年", "1636年", "1638年秋",
]


def fake_password_hash(plain: str) -> str:
    """模拟加密存储（实验数据用 SHA-256，生产环境应使用 bcrypt）。"""
    return hashlib.sha256(plain.encode("utf-8")).hexdigest()


def batch_iter(rows: Sequence[tuple], size: int) -> Iterable[list[tuple]]:
    for i in range(0, len(rows), size):
        yield list(rows[i : i + size])


# ---------------------------------------------------------------------------
# 数据生成
# ---------------------------------------------------------------------------

def generate_locations(fake: Faker) -> list[tuple]:
    rows: list[tuple] = []
    used_names: set[str] = set()

    for name, province in XUXIAKE_LOCATIONS:
        if name in used_names:
            continue
        used_names.add(name)
        rows.append((
            name,
            province,
            random.choice(OPENING_HOURS_POOL),
            1,
            "徐霞客曾游历之地，系统预置景点描述。",
        ))

    seq = 1
    while len(rows) < NUM_LOCATIONS:
        province = random.choice(PROVINCES)
        name = f"{province[:-1]}风光带{seq:03d}号"
        seq += 1
        if name in used_names:
            continue
        used_names.add(name)
        rows.append((
            name,
            province,
            random.choice(OPENING_HOURS_POOL),
            0,
            f"合成测试景点，编号{seq}，供批量灌数使用。",
        ))

    return rows[:NUM_LOCATIONS]


def generate_literature(num_locations: int) -> list[tuple]:
    rows: list[tuple] = []
    for location_id in range(1, num_locations + 1):
        count = random.randint(2, 4) if location_id <= len(XUXIAKE_LOCATIONS) else (
            1 if random.random() < 0.35 else 0
        )
        for _ in range(count):
            orig, trans = random.choice(LITERATURE_SNIPPETS)
            rows.append((
                location_id,
                orig + random.choice(["", " " + orig[:8]]),
                trans,
                random.choice(WRITE_DATES),
            ))
    return rows


def generate_users(fake: Faker) -> list[tuple]:
    rows: list[tuple] = []
    for i in range(1, NUM_USERS + 1):
        username = f"traveler_{i:05d}"
        pwd = fake_password_hash(f"Pass@{i}!")
        avatar = f"/avatars/{username}.jpg" if random.random() < 0.7 else None
        reg_date = fake.date_between(start_date="-5y", end_date="today")
        bio = fake.text(max_nb_chars=120) if random.random() < 0.6 else None
        rows.append((username, pwd, avatar, reg_date, bio))
    return rows


def generate_travelogs(fake: Faker) -> list[tuple]:
    rows: list[tuple] = []
    titles_pool = [
        "穿越{}的时空之旅", "重走徐霞客{}线", "{}打卡记",
        "在{}遇见古今", "{}三日漫记", "云海下的{}行",
    ]
    places = [x[0] for x in XUXIAKE_LOCATIONS] + ["江南", "西南", "岭表"]
    for i in range(NUM_TRAVELOGS):
        user_id = random.randint(1, NUM_USERS)
        place = random.choice(places)
        title = random.choice(titles_pool).format(place)
        content = (
            f"第{i + 1}篇时空游记：途经{place}，记录山川形胜与行旅见闻。"
            f"行程约{random.randint(2, 12)}日，天气{random.choice(['晴', '阴', '雨', '雾'])}。"
        )
        publish = fake.date_time_between(start_date="-3y", end_date="now")
        likes = random.randint(0, 5000)
        rows.append((user_id, title, content, publish, likes))
    return rows


def generate_checkins(
    travelog_publish_times: list[datetime],
    num_locations: int,
) -> list[tuple]:
    """每篇游记固定 CHECKINS_PER_TRAVELOG 个景点，保证总数 >= 10000 且无重复配对。"""
    rows: list[tuple] = []
    for travelog_id, publish_time in enumerate(travelog_publish_times, start=1):
        location_ids = random.sample(range(1, num_locations + 1), CHECKINS_PER_TRAVELOG)
        for lid in location_ids:
            offset_days = random.randint(0, 14)
            offset_hours = random.randint(0, 23)
            check_in = publish_time + timedelta(days=offset_days, hours=offset_hours)
            rows.append((travelog_id, lid, check_in))
    return rows


# ---------------------------------------------------------------------------
# 数据库写入
# ---------------------------------------------------------------------------

def get_connection(config: dict):
    import pymysql

    return pymysql.connect(
        host=config["host"],
        port=config["port"],
        user=config["user"],
        password=config["password"],
        database=config["database"],
        charset=config["charset"],
        autocommit=False,
    )


def truncate_tables(cursor) -> None:
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
    for table in ("Travelog_Location", "Literature", "Travelog", "Location", "User"):
        cursor.execute(f"TRUNCATE TABLE `{table}`")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")


def insert_all(cursor, locations, literature, users, travelogs, checkins) -> None:
    loc_sql = (
        "INSERT INTO `Location` (`LocName`, `Province`, `OpeningHours`, `IsXuXiake`, `Description`) "
        "VALUES (%s, %s, %s, %s, %s)"
    )
    for chunk in batch_iter(locations, BATCH_SIZE):
        cursor.executemany(loc_sql, chunk)

    lit_sql = (
        "INSERT INTO `Literature` (`LocationID`, `OriginalText`, `TranslateInfo`, `WriteDate`) "
        "VALUES (%s, %s, %s, %s)"
    )
    for chunk in batch_iter(literature, BATCH_SIZE):
        cursor.executemany(lit_sql, chunk)

    user_sql = (
        "INSERT INTO `User` (`Username`, `Password`, `AvatarPath`, `RegisterDate`, `Bio`) "
        "VALUES (%s, %s, %s, %s, %s)"
    )
    for chunk in batch_iter(users, BATCH_SIZE):
        cursor.executemany(user_sql, chunk)

    trav_sql = (
        "INSERT INTO `Travelog` (`UserID`, `Title`, `Content`, `PublishTime`, `Likes`) "
        "VALUES (%s, %s, %s, %s, %s)"
    )
    for chunk in batch_iter(travelogs, BATCH_SIZE):
        cursor.executemany(trav_sql, chunk)

    chk_sql = (
        "INSERT INTO `Travelog_Location` (`TravelogID`, `LocationID`, `CheckInTime`) "
        "VALUES (%s, %s, %s)"
    )
    for chunk in batch_iter(checkins, BATCH_SIZE):
        cursor.executemany(chk_sql, chunk)


def export_sql_file(path: str, locations, literature, users, travelogs, checkins) -> None:
    """导出纯 SQL 插入文件（无需 pymysql 时可用 mysql < file 导入）。"""

    def esc(val: Any) -> str:
        if val is None:
            return "NULL"
        if isinstance(val, (int, float)):
            return str(val)
        if isinstance(val, datetime):
            return f"'{val.strftime('%Y-%m-%d %H:%M:%S')}'"
        if hasattr(val, "isoformat"):
            return f"'{val.isoformat()}'"
        s = str(val).replace("\\", "\\\\").replace("'", "''")
        return f"'{s}'"

    lines = [
        "-- 徐霞客时空游记系统测试数据",
        "USE `xuxiake_travel_db`;",
        "SET NAMES utf8mb4;",
        "SET FOREIGN_KEY_CHECKS = 0;",
        "TRUNCATE TABLE `Travelog_Location`;",
        "TRUNCATE TABLE `Literature`;",
        "TRUNCATE TABLE `Travelog`;",
        "TRUNCATE TABLE `Location`;",
        "TRUNCATE TABLE `User`;",
        "SET FOREIGN_KEY_CHECKS = 1;",
        "",
    ]

    for row in locations:
        lines.append(
            "INSERT INTO `Location` (`LocName`,`Province`,`OpeningHours`,`IsXuXiake`,`Description`) "
            f"VALUES ({esc(row[0])},{esc(row[1])},{esc(row[2])},{row[3]},{esc(row[4])});"
        )
    lines.append("")

    for row in literature:
        lines.append(
            "INSERT INTO `Literature` (`LocationID`,`OriginalText`,`TranslateInfo`,`WriteDate`) "
            f"VALUES ({row[0]},{esc(row[1])},{esc(row[2])},{esc(row[3])});"
        )
    lines.append("")

    for row in users:
        lines.append(
            "INSERT INTO `User` (`Username`,`Password`,`AvatarPath`,`RegisterDate`,`Bio`) "
            f"VALUES ({esc(row[0])},{esc(row[1])},{esc(row[2])},{esc(row[3])},{esc(row[4])});"
        )
    lines.append("")

    for row in travelogs:
        lines.append(
            "INSERT INTO `Travelog` (`UserID`,`Title`,`Content`,`PublishTime`,`Likes`) "
            f"VALUES ({row[0]},{esc(row[1])},{esc(row[2])},{esc(row[3])},{row[4]});"
        )
    lines.append("")

    for row in checkins:
        lines.append(
            "INSERT INTO `Travelog_Location` (`TravelogID`,`LocationID`,`CheckInTime`) "
            f"VALUES ({row[0]},{row[1]},{esc(row[2])});"
        )

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"已导出 SQL 文件: {path}")


def verify_counts(cursor) -> None:
    tables = ("User", "Location", "Literature", "Travelog", "Travelog_Location")
    print("\n========== 数据量校验 ==========")
    for t in tables:
        cursor.execute(f"SELECT COUNT(*) FROM `{t}`")
        cnt = cursor.fetchone()[0]
        print(f"  {t}: {cnt}")
    cursor.execute(
        "SELECT COUNT(*) FROM `Travelog` t "
        "LEFT JOIN `User` u ON t.UserID = u.UserID WHERE u.UserID IS NULL"
    )
    orphan_trav = cursor.fetchone()[0]
    cursor.execute(
        "SELECT COUNT(*) FROM `Travelog_Location` tl "
        "LEFT JOIN `Travelog` t ON tl.TravelogID = t.TravelogID WHERE t.TravelogID IS NULL"
    )
    orphan_chk = cursor.fetchone()[0]
    print(f"  孤儿游记(无用户): {orphan_trav} (应为 0)")
    print(f"  孤儿打卡(无游记): {orphan_chk} (应为 0)")
    print("================================\n")


# ---------------------------------------------------------------------------
# 主程序
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="徐霞客时空游记系统测试数据生成")
    parser.add_argument("--host", default=DB_CONFIG["host"])
    parser.add_argument("--port", type=int, default=DB_CONFIG["port"])
    parser.add_argument("--user", default=DB_CONFIG["user"])
    parser.add_argument("--password", default=DB_CONFIG["password"])
    parser.add_argument("--database", default=DB_CONFIG["database"])
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--truncate", action="store_true", default=True,
                        help="插入前清空表（默认开启）")
    parser.add_argument("--no-truncate", action="store_false", dest="truncate")
    parser.add_argument("--export-sql", metavar="PATH", default=None,
                        help="仅导出 SQL 文件，不连接数据库")
    args = parser.parse_args()

    random.seed(args.seed)
    fake = Faker("zh_CN")
    Faker.seed(args.seed)

    print("正在生成内存数据...")
    locations = generate_locations(fake)
    literature = generate_literature(len(locations))
    users = generate_users(fake)
    travelogs = generate_travelogs(fake)
    publish_times = [row[3] for row in travelogs]
    checkins = generate_checkins(publish_times, len(locations))

    print(f"  Location:           {len(locations)}")
    print(f"  Literature:         {len(literature)}")
    print(f"  User:               {len(users)}")
    print(f"  Travelog:           {len(travelogs)}")
    print(f"  Travelog_Location:  {len(checkins)}")

    if args.export_sql:
        export_sql_file(args.export_sql, locations, literature, users, travelogs, checkins)
        return

    try:
        import pymysql  # noqa: F401
    except ImportError:
        print("未安装 pymysql，请: pip install pymysql", file=sys.stderr)
        print("或使用 --export-sql 生成纯 SQL 文件。", file=sys.stderr)
        sys.exit(1)

    config = {
        "host": args.host,
        "port": args.port,
        "user": args.user,
        "password": args.password,
        "database": args.database,
        "charset": "utf8mb4",
    }

    print(f"\n连接数据库 {config['host']}:{config['port']}/{config['database']} ...")
    conn = get_connection(config)
    try:
        with conn.cursor() as cursor:
            if args.truncate:
                print("清空已有业务表...")
                truncate_tables(cursor)

            print("批量插入中...")
            insert_all(cursor, locations, literature, users, travelogs, checkins)
            conn.commit()
            verify_counts(cursor)
        print("测试数据写入完成。")
    except Exception as e:
        conn.rollback()
        print(f"写入失败，已回滚: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
