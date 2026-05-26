# 徐霞客时空游记系统

**Xu Xiake Spatiotemporal Travel Journal System**

> 大丈夫当问奇于天下，以杖履为书，以山河为证。  
> —— 今人重走旧迹，亦当以数据为舟，载古今之行旅。

四百年前的徐霞客，用三十余年的脚力写就《徐霞客游记》：山川形胜、风物民俗、典籍原文，尽录于尺幅之间。今日的我们，仍走在同一片山河上——只是笔下多了一行发布时间，打卡多了一枚时间戳，足迹多了一条可检索的记录。

**徐霞客时空游记系统**，要做的便是这件事：把「行旅」留住，把「足迹」连起来，把「文献」安放在它该在的山河旁。现代旅人写下游记，在景点留下时空打卡；系统则默默记下：谁曾来过，何处被读过，哪一条路，与霞客当年重合。

**在线看板（纸墨风数据人文界面）**：[http://8.134.97.118:8081](http://8.134.97.118:8081)

---

## 我们在记录什么

| 维度 | 含义 |
|------|------|
| **人** | 每一位愿意把旅途公之于众的行者 |
| **地** | 景点名录，及「是否徐霞客曾至」的标记 |
| **典** | 挂靠于景点的古籍摘录、译注与年代 |
| **文** | 游记——标题、正文、发布时间、共鸣（点赞） |
| **迹** | 一篇游记与多处景点的打卡，及每一次抵达的时刻 |

五条线索，织成一张可查询、可统计、可展示的时空网络。不是冰冷的表名，而是一张**古今同游**的底图。

---

## 能为你做什么

- **读山河**：按省浏览景点，筛选徐霞客足迹，点开典籍原文与译注  
- **读行旅**：按时间翻阅最新游记，进入详情，看一路打卡了哪些地方  
- **读数据**：各省分布、热门胜地、用户与文献规模——在 [看板](http://8.134.97.118:8081) 上一目了然  
- **读结构**：自需求而概念、逻辑而物理，完整设计文档随仓库交付，供追溯与延展  

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
├── .env.example
├── documents/                # 从需求到落地的设计文档
│   ├── 01_需求分析报告.md
│   ├── 02_概念结构设计.md
│   ├── 03_逻辑结构设计.md
│   ├── 04_物理设计与建表语句.sql
│   └── 05_测试数据生成脚本.py
└── web/                      # 数字人文看板与 API
    ├── app.py
    ├── docker-compose.yml
    └── static/
```

---

## 数据模型（简表）

| 表名 | 说明 | 关系 |
|------|------|------|
| `User` | 平台注册用户 | 1 → n `Travelog` |
| `Location` | 景点（含 `IsXuXiake` 足迹标记） | 1 → n `Literature` |
| `Literature` | 景点关联历史文献 | n → 1 `Location` |
| `Travelog` | 用户游记 | n → 1 `User` |
| `Travelog_Location` | 游记—景点打卡桥表 | m ↔ n，含 `CheckInTime` |

当前种子数据约：1,200 用户、5,500 游记、11,000 次打卡、360 景点及配套文献——足够撑起统计图表与检索体验，亦可按脚本内常量自行扩缩。

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

### 4. 启动 Web 看板

```bash
cd web
docker compose up -d --build
```

访问 `http://<主机地址>:8081`；公网演示见文首链接（安全组需放行 **TCP 8081**）。接口说明见 [web/README.md](web/README.md)。

---

## 部署说明

与已有 MySQL 联调时，在 `.env` 中设置：

- 宿主机：`MYSQL_HOST=127.0.0.1`（容器需映射 `3306`）
- Docker 同网段：`MYSQL_HOST=xu-xiake-mysql`（`web/docker-compose.yml` 默认）

环境要求：MySQL 8.0+、Python 3.9+、Docker（看板，可选）。

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

-- 浙省徐霞客足迹
SELECT LocName, Province FROM Location
WHERE Province = '浙江省' AND IsXuXiake = 1;

-- 新近行记
SELECT Title, PublishTime FROM Travelog
ORDER BY PublishTime DESC LIMIT 10;

-- 一地几多人曾打卡
SELECT COUNT(*) FROM Travelog_Location WHERE LocationID = 1;
```

---

## 安全提示

生产环境请使用独立账号与强密码。若 `.env` 曾误提交远程仓库，请轮换凭据并清理历史记录。

---

*山河不老，行旅长新。愿此库中每一行记录，都能成为后来人问路时的一盏小灯。*
