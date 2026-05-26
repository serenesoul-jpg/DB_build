# 徐霞客时空游记 — 数据可视化 Web

连接 `xuxiake_travel_db`，在浏览器中展示用户、景点、游记、打卡等统计与列表。

项目总览、建库灌数与环境配置见仓库根目录 [README.md](../README.md)。

## 公网访问

云服务器安全组已放行 **8081** 后，在浏览器打开：

```
http://<你的公网IP>:8081
```

## 本地启动

```bash
cd /root/DB_build/web
docker compose up -d --build
```

## 直接运行（需 MySQL 可连）

```bash
pip install -r requirements.txt
export MYSQL_HOST=127.0.0.1 MYSQL_PASSWORD=xuxiake_root MYSQL_DATABASE=xuxiake_travel_db
python app.py
```

## API 接口

| 路径 | 说明 |
|------|------|
| `GET /api/health` | 健康检查 |
| `GET /api/stats` | 各表数量汇总 |
| `GET /api/travelogs/latest` | 最新游记 |
| `GET /api/travelogs/:id` | 游记详情与打卡 |
| `GET /api/locations` | 景点列表（支持省份、徐霞客足迹筛选） |
| `GET /api/locations/provinces` | 各省景点统计 |
| `GET /api/locations/top-checkins` | 热门打卡景点 |
