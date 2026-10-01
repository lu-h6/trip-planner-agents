# BaseAgent 智能旅行助手

基于 BaseAgent、FastAPI 和 Vue 3 构建的智能旅行规划助手。后端负责行程生成、地图服务和旅行记忆，前端提供行程填写、地图展示和结果导出。

## 功能

- AI 驱动的多日旅行计划生成
- 通过 MCP 调用高德地图搜索、天气和路线服务
- 支持 LLM、Unsplash 和本地 SQLite 旅行记忆
- Vue 3 + TypeScript + Vite 前端
- 行程地图展示、编辑和图片/PDF 导出

## 项目结构

```text
trip-planner-agents/
├── backend/
│   ├── app/                   # FastAPI 应用
│   └── base_agents/           # 内置 BaseAgent 框架源码
├── frontend/                  # Vue 3 前端
├── .env.example               # 后端环境变量模板
├── frontend/.env.example      # 前端环境变量模板
├── main.py                    # 从仓库根目录启动后端
├── pyproject.toml             # Python 项目元数据和依赖
└── requirements.txt           # pip 兼容安装入口
```

## 环境要求

- Python 3.12+
- Node.js 18+
- `uv`，推荐用于管理 Python 环境和依赖
- 高德地图 API Key
- 一个兼容 OpenAI API 的 LLM 服务

## 配置

在仓库根目录创建后端配置：

```powershell
Copy-Item .env.example .env
```

至少填写：

```dotenv
LLM_MODEL_ID=your-model-name
LLM_API_KEY=your-api-key
LLM_BASE_URL=https://api.openai.com/v1
AMAP_API_KEY=your_amap_api_key
```

也可以使用 `KIMI_API_KEY`、`DEEPSEEK_API_KEY`、`DASHSCOPE_API_KEY` 等提供商专用变量。后端会从仓库根目录读取 `.env`，不依赖启动命令所在的当前目录。

创建前端配置：

```powershell
Copy-Item frontend/.env.example frontend/.env
```

开发环境下 `VITE_API_BASE_URL` 保持为空，前端会通过 Vite 代理访问 `http://localhost:8000`。填写 `VITE_AMAP_WEB_JS_KEY` 后，结果页才能加载高德地图。

## 启动后端

使用 `uv`：

```powershell
uv sync
uv run trip-planner
```

也可以使用根目录启动脚本：

```powershell
uv run python main.py
```

API 地址：

- 服务首页：`http://localhost:8000/`
- 健康检查：`http://localhost:8000/health`
- Swagger 文档：`http://localhost:8000/docs`
- ReDoc 文档：`http://localhost:8000/redoc`

如果使用传统 `pip`，项目也提供兼容入口：

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

## 启动前端

```powershell
Set-Location frontend
npm install
npm run dev
```

打开 `http://localhost:5173`。

生产构建：

```powershell
npm run build
npm run preview
```

## 主要 API

- `POST /api/trip/plan`：生成旅行计划
- `GET /api/poi/search`：搜索 POI
- `GET /api/poi/photo`：获取景点图片
- `GET /api/map/poi`：搜索地图 POI
- `GET /api/map/weather`：查询天气
- `POST /api/map/route`：规划路线
- `GET /api/memory/{user_id}`：读取用户旅行记忆
- `POST /api/memory/{user_id}`：添加旅行记忆
- `DELETE /api/memory/{user_id}`：清空用户旅行记忆

## 开发检查

```powershell
uv run python -m compileall backend
Set-Location frontend
npm run build
```

Python 项目的依赖源是 `pyproject.toml`；`requirements.txt` 仅作为 pip 用户的兼容安装入口。`.env`、本地数据库和前端依赖不会提交到仓库。

## 许可证

CC BY-NC-SA 4.0
