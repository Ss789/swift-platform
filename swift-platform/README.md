 # SwiftPlatform（后端）
 
 基于 **FastAPI + SQLAlchemy(异步) + PostgreSQL** 的系统管理 + 流程引擎后端服务。
 
 ## 本地启动（示例）
 
 1. 准备数据库并初始化
 
 ```bash
 psql -U swift -d swift_platform -f scripts/init.sql
 ```
 
 2. 安装依赖并启动
 
 ```bash
 pip install -r requirements.txt --break-system-packages
 uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
 ```
 
 3. 访问
 
 - API: http://localhost:8000/api
 - Swagger: http://localhost:8000/docs
 
