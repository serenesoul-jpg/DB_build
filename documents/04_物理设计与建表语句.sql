-- ============================================================================
-- 徐霞客时空游记系统 — 物理结构设计与 MySQL 建表脚本
-- 文档编号：04
-- 目标版本：MySQL 8.0+
-- 字符集：utf8mb4（支持中文及 emoji）
-- 存储引擎：InnoDB（支持事务、外键、行级锁）
-- 编写日期：2026-05-26
-- 前置文档：01 需求分析、02 概念结构、03 逻辑结构
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 0. 数据库级配置
-- ----------------------------------------------------------------------------

DROP DATABASE IF EXISTS `xuxiake_travel_db`;

CREATE DATABASE `xuxiake_travel_db`
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE `xuxiake_travel_db`;

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------------------------------------------------------
-- 1. 用户表 User
-- 实体：现代注册用户；与游记为 1:n
-- ----------------------------------------------------------------------------

DROP TABLE IF EXISTS `User`;

CREATE TABLE `User` (
    `UserID`       INT            NOT NULL AUTO_INCREMENT COMMENT '用户编号，主键，自增',
    `Username`     VARCHAR(50)    NOT NULL                COMMENT '登录用户名，全局唯一',
    `Password`     VARCHAR(255)   NOT NULL                COMMENT '加密后的密码摘要（如 bcrypt），禁止明文',
    `AvatarPath`   VARCHAR(255)   NULL                    COMMENT '头像文件路径或 URL',
    `RegisterDate` DATE           NOT NULL DEFAULT (CURRENT_DATE) COMMENT '账号注册日期',
    `Bio`          TEXT           NULL                    COMMENT '个人简介',
    PRIMARY KEY (`UserID`),
    CONSTRAINT `uk_user_username` UNIQUE (`Username`)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci
  COMMENT='用户表：平台注册主体，发布游记';

-- ----------------------------------------------------------------------------
-- 2. 景点表 Location
-- 实体：旅游景点；与文献 1:n，与游记经桥表 m:n
-- ----------------------------------------------------------------------------

DROP TABLE IF EXISTS `Location`;

CREATE TABLE `Location` (
    `LocationID`   INT            NOT NULL AUTO_INCREMENT COMMENT '景点编号，主键，自增',
    `LocName`      VARCHAR(100)   NOT NULL                COMMENT '景点名称',
    `Province`     VARCHAR(50)    NOT NULL                COMMENT '所属省级行政区',
    `OpeningHours` VARCHAR(100)   NULL                    COMMENT '开放时间描述，如 08:00-18:00',
    `IsXuXiake`    TINYINT(1)     NOT NULL DEFAULT 0      COMMENT '是否徐霞客足迹：0否 1是',
    `Description`  TEXT           NULL                    COMMENT '景点历史文化与地理介绍',
    PRIMARY KEY (`LocationID`),
    CONSTRAINT `chk_location_isxuxiake` CHECK (`IsXuXiake` IN (0, 1))
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci
  COMMENT='景点表：旅游资源与徐霞客足迹标识';

-- ----------------------------------------------------------------------------
-- 3. 文献表 Literature
-- 实体：景点关联古籍文献；外键 LocationID，ON DELETE CASCADE
-- ----------------------------------------------------------------------------

DROP TABLE IF EXISTS `Literature`;

CREATE TABLE `Literature` (
    `LitID`         INT           NOT NULL AUTO_INCREMENT COMMENT '文献编号，主键，自增',
    `LocationID`    INT           NOT NULL                COMMENT '所属景点编号，外键',
    `OriginalText`  TEXT          NOT NULL                COMMENT '古籍原文或摘录',
    `TranslateInfo` TEXT          NULL                    COMMENT '现代汉语译注或学术注释',
    `WriteDate`     VARCHAR(30)   NULL                    COMMENT '成文年代，兼容历史纪年',
    PRIMARY KEY (`LitID`),
    CONSTRAINT `fk_literature_location`
        FOREIGN KEY (`LocationID`)
        REFERENCES `Location` (`LocationID`)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci
  COMMENT='文献表：从属于景点的历史文献资料';

-- ----------------------------------------------------------------------------
-- 4. 游记表 Travelog
-- 实体：用户发布的游记；外键 UserID，ON DELETE CASCADE
-- ----------------------------------------------------------------------------

DROP TABLE IF EXISTS `Travelog`;

CREATE TABLE `Travelog` (
    `TravelogID`  INT           NOT NULL AUTO_INCREMENT COMMENT '游记编号，主键，自增',
    `UserID`      INT           NOT NULL                COMMENT '发布用户编号，外键',
    `Title`       VARCHAR(200)  NOT NULL                COMMENT '游记标题',
    `Content`     LONGTEXT      NOT NULL                COMMENT '游记正文',
    `PublishTime` DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '发布时间，支持时间线排序',
    `Likes`       INT           NOT NULL DEFAULT 0      COMMENT '点赞数，非负整数',
    PRIMARY KEY (`TravelogID`),
    CONSTRAINT `fk_travelog_user`
        FOREIGN KEY (`UserID`)
        REFERENCES `User` (`UserID`)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT `chk_travelog_likes` CHECK (`Likes` >= 0)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci
  COMMENT='游记表：用户发布的时空游记作品';

-- ----------------------------------------------------------------------------
-- 5. 游记景点打卡关联表 Travelog_Location（桥表）
-- 消解 Travelog 与 Location 的 m:n；联合主键；联系属性 CheckInTime
-- ----------------------------------------------------------------------------

DROP TABLE IF EXISTS `Travelog_Location`;

CREATE TABLE `Travelog_Location` (
    `TravelogID`  INT      NOT NULL COMMENT '游记编号，联合主键之一，外键',
    `LocationID`  INT      NOT NULL COMMENT '景点编号，联合主键之一，外键',
    `CheckInTime` DATETIME NOT NULL COMMENT '时空打卡时间，联系属性',
    PRIMARY KEY (`TravelogID`, `LocationID`),
    CONSTRAINT `fk_tl_travelog`
        FOREIGN KEY (`TravelogID`)
        REFERENCES `Travelog` (`TravelogID`)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT `fk_tl_location`
        FOREIGN KEY (`LocationID`)
        REFERENCES `Location` (`LocationID`)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci
  COMMENT='游记景点打卡桥表：记录游记与景点的 m:n 时空打卡';

SET FOREIGN_KEY_CHECKS = 1;

-- ============================================================================
-- 6. 查询优化索引（Query Optimization Indexes）
-- ============================================================================
-- 说明：主键与 UNIQUE 约束在 InnoDB 中自动建有聚簇/唯一索引。
-- 以下补充普通索引以加速高频查询（见 01 需求分析报告 Q1-Q5）。
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 索引 1：用户名唯一索引（显式命名，便于 EXPLAIN 与运维文档引用）
-- ----------------------------------------------------------------------------
-- 【为何需要】
-- 场景 Q1：用户登录时 WHERE Username = ? 需 O(log n) 定位而非全表扫描。
-- User.Username 已通过 uk_user_username 实现唯一约束并自带唯一索引；
-- 此处显式 CREATE UNIQUE INDEX 与约束等价，用于实验报告中「索引设计」章节点名，
-- 并统一索引命名规范 idx_user_username。
-- 若已存在 uk_user_username，MySQL 不会重复存储，本语句与约束共享同一索引结构。
-- 为兼容「单独列出用户名索引」的作业要求，采用可重复执行写法：

-- Username 已由 UNIQUE 约束索引覆盖；下列语句在仅当需独立命名索引时使用（可选）：
-- CREATE UNIQUE INDEX `idx_user_username` ON `User` (`Username`);

-- 作业明确要求「用户名字段的唯一索引」：约束 uk_user_username 已满足。
-- 补充：为登录以外按注册时间统计用户，可选普通索引（非强制要求，此处不建）。

-- ----------------------------------------------------------------------------
-- 索引 2：游记发布时间普通索引
-- ----------------------------------------------------------------------------

CREATE INDEX `idx_travelog_publish_time`
    ON `Travelog` (`PublishTime` DESC);

-- 【为何需要】
-- 场景 Q3：首页「最新游记」按 PublishTime 降序分页（ORDER BY PublishTime DESC LIMIT n）。
-- 无索引时需 filesort 全表排序；5000+ 游记规模下 B+ 树索引显著降低排序与扫描成本。

-- ----------------------------------------------------------------------------
-- 索引 3：景点省份普通索引
-- ----------------------------------------------------------------------------

CREATE INDEX `idx_location_province`
    ON `Location` (`Province`);

-- 【为何需要】
-- 场景 Q2：按省份筛选景点 WHERE Province = ?，常结合 IsXuXiake 过滤徐霞客足迹。
-- 省份基数低于行数（三十余省级），索引仍可减少扫描行数，支持区域旅游统计。

-- ----------------------------------------------------------------------------
-- 索引 4（扩展）：徐霞客足迹复合索引 — 覆盖 Q2 组合条件
-- ----------------------------------------------------------------------------

CREATE INDEX `idx_location_province_xuxiake`
    ON `Location` (`Province`, `IsXuXiake`);

-- 【为何需要】
-- 场景 Q2 进阶：WHERE Province = ? AND IsXuXiake = 1。
-- 复合索引最左前缀可先按省过滤再按足迹标志位定位，避免回表多次随机 I/O。

-- ----------------------------------------------------------------------------
-- 索引 5（扩展）：桥表景点侧索引 — 覆盖 Q5 统计
-- ----------------------------------------------------------------------------

CREATE INDEX `idx_tl_location_id`
    ON `Travelog_Location` (`LocationID`);

-- 【为何需要】
-- 场景 Q5：统计某景点被多少篇游记打卡 COUNT(*) WHERE LocationID = ?。
-- 外键 LocationID 在 InnoDB 中通常已有辅助索引；显式命名便于实验报告引用。
-- TravelogID 侧由联合主键 (TravelogID, LocationID) 最左前缀覆盖 Q4 查询。

-- ----------------------------------------------------------------------------
-- 索引 6（扩展）：游记发布用户索引 — 个人主页游记列表
-- ----------------------------------------------------------------------------

CREATE INDEX `idx_travelog_user_id`
    ON `Travelog` (`UserID`);

-- 【为何需要】
-- 查询某用户全部游记 WHERE UserID = ? ORDER BY PublishTime DESC。
-- 外键 UserID 通常已有索引；与 idx_travelog_publish_time 配合可优化排序（视优化器选择）。

-- ============================================================================
-- 7. 验证脚本（可选执行）
-- ============================================================================
-- SHOW TABLES;
-- SHOW CREATE TABLE `User`;
-- SHOW CREATE TABLE `Location`;
-- SHOW CREATE TABLE `Literature`;
-- SHOW CREATE TABLE `Travelog`;
-- SHOW CREATE TABLE `Travelog_Location`;
-- SHOW INDEX FROM `User`;
-- SHOW INDEX FROM `Travelog`;
-- SHOW INDEX FROM `Location`;
-- SHOW INDEX FROM `Travelog_Location`;

-- ============================================================================
-- 脚本结束
-- ============================================================================
