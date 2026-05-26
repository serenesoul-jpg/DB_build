# 徐霞客时空游记系统 — 数据库课程项目

**Xu Xiake Spatiotemporal Travel Journal System**

面向数据库课程设计的完整链路：需求分析 → 概念 / 逻辑结构 → 物理 DDL → 测试数据灌入 → Web 数据看板。业务库为 MySQL 8.0+ 下的 `xuxiake_travel_db`。

---

## 项目结构

```
DB_build/
├── README.md                 # 本文件
├── .env.example              # 环境变量模板（复制为 .env 使用）
├── documents/
│   ├── 01_需求分析报告.md
│   ├── 02_概念结构设计.md
│   ├── 03_逻辑结构设计.md
│   ├── 04_物理设计与建表语句.sql
│   └── 05_测试数据生成脚本.py
└── web/                      # 数据可视化（Flask + 静态前端）
    ├── app.py
    ├── docker-compose.yml
    └── static/
```

---

## 核心数据模型

| 表名 | 说明 | 主要关系 |
|------|------|----------|
| `User` | 注册用户 | 1 : n → `Travelog` |
| `Location` | 景点（含徐霞客足迹标志） | 1 : n → `Literature` |
| `Literature` | 景点关联古籍文献 | n : 1 → `Location` |
| `Travelog` | 用户游记 | n : 1 → `User` |
| `Travelog_Location` | 游记—景点打卡桥表 | m : n（含 `CheckInTime`） |

默认测试数据规模（脚本可配置）：用户 ≥ 1,200、游记 ≥ 5,500、打卡 ≥ 11,000、景点 360、文献若干。

---

## 环境要求

- **MySQL** 8.0+（`utf8mb4` / InnoDB）
- **Python** 3.9+（仅灌数脚本；推荐 3.11）
- **Docker**（可选，用于 Web 看板一键部署）

---

## 快速开始

### 1. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填写 MYSQL_HOST、MYSQL_PASSWORD 等
```

> `.env` 已加入 `.gitignore`，**请勿将含真实密码的 `.env` 提交到 Git**。若仓库历史中曾误提交过 `.env`，应从远程删除并轮换数据库密码。

### 2. 建库建表

```bash
mysql -h127.0.0.1 -uroot -p < documents/04_物理设计与建表语句.sql
```

或在 Docker MySQL 容器内执行：

```bash
docker cp documents/04_物理设计与建表语句.sql <mysql容器名>:/tmp/schema.sql
docker exec -i <mysql容器名> mysql -uroot -p<密码> --default-character-set=utf8mb4 \
  -e "source /tmp/schema.sql"
```

### 3. 灌入测试数据

```bash
pip install faker pymysql
python documents/05_测试数据生成脚本.py
```

常用参数：

```bash
python documents/05_测试数据生成脚本.py --host 127.0.0.1 --password '你的密码'
python documents/05_测试数据生成脚本.py --export-sql documents/05_test_data.sql  # 仅导出 SQL
```

脚本会读取项目根目录 `.env` 中的 `MYSQL_*` 变量（无需安装 `python-dotenv`）。

### 4. 启动数据看板（公网展示）

```bash
cd web
docker compose up -d --build
```

浏览器访问：`http://<服务器公网 IP>:8081`（需在云安全组放行 **TCP 8081**）。

看板功能：各表统计、各省景点分布、热门打卡、最新游记与详情、景点 / 文献浏览。API 说明见 [web/README.md](web/README.md)。

---

## 与现有 MySQL 容器联调

若本机已有 `xu-xiake-mysql` 等容器，可将 `.env` 中 `MYSQL_HOST` 设为：

- 宿主机访问：`127.0.0.1`（需容器映射 `3306` 端口）
- 同 Docker 网络内：`xu-xiake-mysql`（Web 的 `docker-compose.yml` 已按此配置）

---

## 设计文档阅读顺序

1. [01 需求分析报告](documents/01_需求分析报告.md) — 业务场景与查询需求（Q1–Q5）
2. [02 概念结构设计](documents/02_概念结构设计.md) — E-R 图与实体联系
3. [03 逻辑结构设计](documents/03_逻辑结构设计.md) — 关系模式与范式说明
4. [04 物理设计与建表语句](documents/04_物理设计与建表语句.sql) — DDL 与查询优化索引

---

## 典型 SQL 验证

```sql
USE xuxiake_travel_db;

-- Q2：某省徐霞客足迹景点
SELECT LocName, Province FROM Location
WHERE Province = '浙江省' AND IsXuXiake = 1;

-- Q3：最新游记
SELECT Title, PublishTime FROM Travelog
ORDER BY PublishTime DESC LIMIT 10;

-- Q5：某景点被打卡次数
SELECT COUNT(*) FROM Travelog_Location WHERE LocationID = 1;
```

---

## 许可证与说明

课程数据库设计作业仓库。文档与 SQL 仅供学习交流；生产环境请使用强密码、独立账号，并避免将 `.env` 纳入版本控制。
