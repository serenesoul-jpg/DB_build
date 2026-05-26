# 徐霞客时空游记系统

**Xu Xiake Spatiotemporal Travel Journal System**

连接古今的旅游文化数据平台：现代旅人发布游记、在景点「时空打卡」，并与徐霞客足迹、古籍文献形成对照。本仓库包含完整的数据库 schema、种子数据工具链，以及面向运营与展示的 Web 数据看板。

**在线看板**：[http://8.134.97.118:8081](http://8.134.97.118:8081)

---

## 功能概览

- **用户与内容**：注册用户信息、游记发布与互动数据（点赞等）
- **景点与文献**：全国景点库、徐霞客足迹标识、景点关联古籍摘录与译注
- **时空打卡**：游记与景点的多对多关联，记录每次打卡时间戳
- **数据看板**：实时统计、区域分布、热门景点与内容浏览（端口 `8081`）

---

## 技术栈

| 层级 | 选型 |
|------|------|
| 数据库 | MySQL 8.0+，`utf8mb4`，InnoDB |
| Schema | 规范化关系模型，外键级联与查询优化索引 |
| 种子数据 | Python 3.9+，`Faker`，`PyMySQL` |
| 看板服务 | Flask 3，静态前端 + REST API，Docker Compose |

业务库名：`xuxiake_travel_db`

---

## 仓库结构

```
DB_build/
├── README.md
├── .env.example              # 环境变量模板
├── documents/                # 设计与交付文档
│   ├── 01_需求分析报告.md
│   ├── 02_概念结构设计.md
│   ├── 03_逻辑结构设计.md
│   ├── 04_物理设计与建表语句.sql
│   └── 05_测试数据生成脚本.py
└── web/                      # 看板与 API 服务
    ├── app.py
    ├── docker-compose.yml
    └── static/
```

---

## 数据模型

| 表名 | 说明 | 关系 |
|------|------|------|
| `User` | 平台注册用户 | 1 → n `Travelog` |
| `Location` | 景点资源（含 `IsXuXiake` 足迹标记） | 1 → n `Literature` |
| `Literature` | 景点关联历史文献 | n → 1 `Location` |
| `Travelog` | 用户发布的游记 | n → 1 `User` |
| `Travelog_Location` | 游记—景点打卡（桥表） | m ↔ n，含 `CheckInTime` |

种子数据默认规模（可在脚本内调整）：约 1,200 用户、5,500 游记、11,000 次打卡、360 景点及配套文献记录。

---

## 快速开始

### 1. 环境配置

```bash
cp .env.example .env
# 编辑 .env：MYSQL_HOST、MYSQL_PASSWORD、MYSQL_DATABASE 等
```

`.env` 已列入 `.gitignore`，请勿将含凭据的文件提交至版本库。

### 2. 初始化数据库

```bash
mysql -h127.0.0.1 -uroot -p < documents/04_物理设计与建表语句.sql
```

Docker 环境示例：

```bash
docker cp documents/04_物理设计与建表语句.sql <容器名>:/tmp/schema.sql
docker exec -i <容器名> mysql -uroot -p<密码> --default-character-set=utf8mb4 \
  -e "source /tmp/schema.sql"
```

### 3. 导入种子数据

```bash
pip install faker pymysql
python documents/05_测试数据生成脚本.py
```

可选参数：

```bash
python documents/05_测试数据生成脚本.py --host 127.0.0.1 --password '<密码>'
python documents/05_测试数据生成脚本.py --export-sql documents/05_test_data.sql
```

脚本自动读取项目根目录 `.env` 中的 `MYSQL_*` 配置。

### 4. 启动 Web 看板

```bash
cd web
docker compose up -d --build
```

本地或内网访问 `http://<主机地址>:8081`；当前公网实例见上方链接（需安全组放行 **TCP 8081**）。

看板提供运营统计、图表分析与游记 / 景点 / 文献详情；REST 接口说明见 [web/README.md](web/README.md)。

---

## 部署说明

**与已有 MySQL 实例联调**时，在 `.env` 中设置：

- 宿主机连接：`MYSQL_HOST=127.0.0.1`（需映射 `3306`）
- Docker 同网段：`MYSQL_HOST=xu-xiake-mysql`（`web/docker-compose.yml` 默认接入该网络）

**环境要求**：MySQL 8.0+、Python 3.9+（种子脚本）、Docker（看板，可选）。

---

## 文档索引

| 文档 | 内容 |
|------|------|
| [01 需求分析](documents/01_需求分析报告.md) | 业务场景与核心查询 |
| [02 概念结构](documents/02_概念结构设计.md) | E-R 模型与实体联系 |
| [03 逻辑结构](documents/03_逻辑结构设计.md) | 关系模式与范式 |
| [04 物理设计](documents/04_物理设计与建表语句.sql) | DDL、索引与约束 |

---

## 查询示例

```sql
USE xuxiake_travel_db;

-- 按省筛选徐霞客足迹景点
SELECT LocName, Province FROM Location
WHERE Province = '浙江省' AND IsXuXiake = 1;

-- 最新发布的游记
SELECT Title, PublishTime FROM Travelog
ORDER BY PublishTime DESC LIMIT 10;

-- 某景点的游记打卡次数
SELECT COUNT(*) FROM Travelog_Location WHERE LocationID = 1;
```

---

## 安全提示

生产部署请使用独立数据库账号、强密码与最小权限；定期轮换凭据。若 `.env` 曾误提交至远程仓库，请修改密码并从历史中清理敏感记录。
