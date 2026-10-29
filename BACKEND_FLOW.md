# 后端流转流程说明

本文用于快速理解 `base-agent-trip-planner` 后端各模块职责，以及一次旅行规划请求在模块之间如何流转。

## 1. 后端整体分层

```text
前端 Vue
  |
  | POST /api/trip/plan
  v
FastAPI 应用入口
  |
  | 注册 /api/trip、/api/poi、/api/map
  v
路由层 routes
  |
  | 调用 Agent 或服务层
  v
Agent 编排层 / Service 层
  |
  | LLM + 高德 MCP + Unsplash
  v
Pydantic 数据模型
  |
  | 统一响应给前端
  v
前端结果页展示
```

## 2. 关键目录与文件

```text
backend/
  run.py                         后端启动脚本
  base_agents/                   内置 BaseAgent 框架源码
  app/
    api/
      main.py                    FastAPI 主应用，注册路由、配置 CORS、启动检查
      routes/
        trip.py                  旅行规划接口
        map.py                   地图能力接口：POI、天气、路线
        poi.py                   POI 详情和图片相关接口
        memory.py                旅行记忆接口：查看、添加、删除用户记忆
    agents/
      trip_planner_agent.py      多 Agent 旅行规划主流程
    services/
      llm_service.py             LLM 单例封装
      amap_service.py            高德地图 MCP 服务封装
      unsplash_service.py        Unsplash 图片服务封装
      memory_service.py          基于 base_agents SQLiteDocumentStore 的旅行记忆服务
    models/
      schemas.py                 请求和响应数据结构
    config.py                    环境变量和配置校验
```

## 3. 应用启动流程

1. `backend/run.py` 读取配置，然后用 Uvicorn 启动 `app.api.main:app`。
2. `app/api/main.py` 创建 FastAPI 实例。
3. 配置 CORS，允许前端开发地址访问后端。
4. 注册三个路由组：
   - `/api/trip`：旅行规划
   - `/api/poi`：POI 详情、POI 搜索、景点图片
   - `/api/map`：地图 POI、天气、路线规划
5. 启动时调用 `validate_config()`，主要检查 `AMAP_API_KEY` 是否配置；LLM Key 缺失只给警告。

## 4. 主流程：生成旅行计划

主入口是前端调用：

```text
POST /api/trip/plan
```

请求数据结构是 `TripRequest`：

```text
user_id           用户ID,用于区分不同用户记忆
city              目的地城市
start_date        开始日期
end_date          结束日期
travel_days       旅行天数
transportation    交通偏好
accommodation     住宿偏好
preferences       旅行偏好标签
free_text_input   用户额外要求
memory_enabled    是否启用个性化记忆
```

完整链路如下：

```text
frontend/src/services/api.ts
  generateTripPlan()
    |
    | POST /api/trip/plan
    v
backend/app/api/routes/trip.py
  plan_trip(request)
    |
    | get_trip_planner_agent()
    v
backend/app/agents/trip_planner_agent.py
  MultiAgentTripPlanner.plan_trip(request)
    |
    | 步骤 0：读取旅行记忆
    |   TravelMemoryService.build_context(...)
    |   使用 base_agents.memory.storage.SQLiteDocumentStore
    |
    | 步骤 1：景点搜索 Agent
    |   attraction_agent.run(...)
    |   使用高德 MCP 工具 amap_maps_text_search
    |
    | 步骤 2：天气查询 Agent
    |   weather_agent.run(...)
    |   使用高德 MCP 工具 amap_maps_weather
    |
    | 步骤 3：酒店推荐 Agent
    |   hotel_agent.run(...)
    |   使用高德 MCP 工具 amap_maps_text_search
    |
    | 步骤 4：行程规划 Agent
    |   planner_agent.run(...)
    |   汇总景点、天气、酒店、用户偏好，要求 LLM 返回 JSON
    |
    | _parse_response()
    |
    | 步骤 5：保存旅行记忆
    |   TravelMemoryService.save_trip_memory(...)
    v
TripPlan Pydantic 对象
    |
    v
TripPlanResponse(success=True, data=trip_plan)
```

### 4.1 多 Agent 初始化

`MultiAgentTripPlanner.__init__()` 初始化时会创建：

```text
共享工具：
  amap_tool = MCPTool(server_command=["uvx", "amap-mcp-server"])

Agent：
  attraction_agent  景点搜索专家，带高德 MCP 工具
  weather_agent     天气查询专家，带高德 MCP 工具
  hotel_agent       酒店推荐专家，带高德 MCP 工具
  planner_agent     行程规划专家，不直接挂工具，只整合前三者结果
```

这里的 Agent 使用同一个 `BaseAgentLLM` 实例，LLM 实例由 `services/llm_service.py` 用单例方式创建。

### 4.2 为什么前 3 个 Agent 必须用工具

三个专家 Agent 的系统提示词都明确要求输出工具调用格式，例如：

```text
[TOOL_CALL:amap_maps_text_search:keywords=历史文化,city=北京]
[TOOL_CALL:amap_maps_weather:city=北京]
```

这样 BaseAgent 能识别并调用 MCP 工具，而不是让模型直接编造景点或天气。

### 4.3 最终 JSON 如何变成后端响应

`planner_agent` 被要求返回固定 JSON 格式，`_parse_response()` 会按以下顺序提取：

1. 优先找 ```json 代码块。
2. 其次找普通 ``` 代码块。
3. 最后从第一个 `{` 到最后一个 `}` 截取 JSON。
4. `json.loads()` 解析。
5. 用 `TripPlan(**data)` 转成 Pydantic 对象。

如果任一步失败，会进入 `_create_fallback_plan()`，生成一个兜底行程。兜底行程使用模拟景点、模拟坐标和基础餐饮信息，不依赖外部服务。

## 5. 其他后端接口

### 5.1 `/api/map` 地图接口

文件：`backend/app/api/routes/map.py`

```text
GET  /api/map/poi       搜索 POI
GET  /api/map/weather   查询天气
POST /api/map/route     规划路线
GET  /api/map/health    地图服务健康检查
```

这些接口调用 `AmapService`：

```text
map.py
  |
  v
services/amap_service.py
  |
  v
MCPTool.run(...)
  |
  v
amap-mcp-server
```

注意：当前 `search_poi()`、`get_weather()`、`plan_route()` 已经调用了 MCP 工具，但结果解析部分还是 TODO，所以现在分别返回空列表或空对象。它们更像是地图能力的接口骨架。

### 5.2 `/api/poi` POI 辅助接口

文件：`backend/app/api/routes/poi.py`

```text
GET /api/poi/detail/{poi_id}
  调用 AmapService.get_poi_detail()
  使用高德 maps_search_detail
  尝试从 MCP 返回文本中解析 JSON

GET /api/poi/search
  调用 AmapService.search_poi()
  当前受 AmapService 解析 TODO 影响，可能返回空列表

GET /api/poi/photo?name=...
  调用 UnsplashService.get_photo_url()
  从 Unsplash 搜索景点图片
```

前端结果页会额外请求 `/api/poi/photo`，按景点名称补图片。

### 5.3 `/api/memory` 旅行记忆接口

文件：`backend/app/api/routes/memory.py`

```text
GET    /api/memory/{user_id}           查看用户记忆
GET    /api/memory/{user_id}/context   获取可注入 Agent 的记忆上下文
POST   /api/memory/{user_id}           手动添加旅行记忆
DELETE /api/memory/{user_id}           清空用户记忆
DELETE /api/memory/{user_id}/{id}      删除单条记忆
GET    /api/memory/system/stats        查看记忆库统计
```

记忆服务没有重新造存储层，而是直接复用内置 `base_agents.memory.storage.SQLiteDocumentStore`。当前默认保存三类旅行记忆：

```text
travel_preference   用户交通、住宿、旅行风格偏好
user_requirement    用户额外要求,例如过敏、无障碍、慢节奏
trip_history        已生成过的城市、天数、景点和预算摘要
```

规划时会按 `user_id` 读取相关记忆并注入到 `planner_agent` 的提示词；规划成功后会把本次请求和结果摘要写回 SQLite 记忆库。

## 6. 数据模型关系

文件：`backend/app/models/schemas.py`

```text
TripRequest
  前端提交的旅行需求

TripPlanResponse
  后端统一响应包装：
  success + message + data

TripPlan
  最终旅行计划：
  city、start_date、end_date、days、weather_info、overall_suggestions、budget

DayPlan
  单日行程：
  date、day_index、description、transportation、accommodation、hotel、attractions、meals

Attraction
  景点：
  name、address、location、visit_duration、description、category、ticket_price 等

Meal
  餐饮：
  type、name、address、location、description、estimated_cost

Hotel
  酒店：
  name、address、location、price_range、rating、distance、estimated_cost

WeatherInfo
  天气：
  date、day_weather、night_weather、day_temp、night_temp、wind_direction、wind_power

Budget
  预算汇总：
  total_attractions、total_hotels、total_meals、total_transportation、total
```

## 7. 配置与外部依赖

文件：`backend/app/config.py`

关键配置：

```text
AMAP_API_KEY           高德地图 MCP 必需
LLM_API_KEY            LLM API Key，可由 BaseAgentLLM 读取
OPENAI_API_KEY         另一个可选 LLM Key 来源
LLM_BASE_URL           LLM 服务地址
LLM_MODEL_ID           LLM 模型名
UNSPLASH_ACCESS_KEY    景点图片接口需要
```

高德 MCP 的启动命令：

```text
uvx amap-mcp-server
```

因此运行后端时，本机需要能执行 `uvx`，并能访问对应 MCP 服务依赖。

## 8. 模块之间的联系

```text
config.py
  被 main.py、llm_service.py、amap_service.py、unsplash_service.py、trip_planner_agent.py 使用

schemas.py
  被 routes 和 Agent 使用，用于请求校验、响应约束、LLM 输出落地

main.py
  只负责 FastAPI 应用创建、CORS、路由注册、启动配置校验

routes/trip.py
  接收旅行规划请求，不做复杂业务，转交 MultiAgentTripPlanner

agents/trip_planner_agent.py
  后端核心业务编排层，负责：
  1. 创建 LLM
  2. 创建高德 MCP 工具
  3. 创建多个 SimpleAgent
  4. 串行调用景点、天气、酒店、行程规划
  5. 解析 LLM JSON
  6. 失败时生成兜底计划

services/llm_service.py
  从本地 backend/base_agents 创建和缓存 BaseAgentLLM

services/amap_service.py
  给 /api/map 和 /api/poi 提供直接地图能力封装
  主旅行规划流程没有直接走 AmapService，而是在 Agent 内直接挂 MCPTool

services/unsplash_service.py
  给 /api/poi/photo 提供图片搜索能力

services/memory_service.py
  直接使用 base_agents.memory.storage.SQLiteDocumentStore
  负责旅行记忆的查询、重排、提示词上下文构建和规划结果写回
```

## 9. 当前实现需要注意的点

1. `POST /api/trip/plan` 是主流程，功能最完整。
2. `/api/map/*` 和 `/api/poi/search` 虽然会调用高德 MCP，但返回结果解析还没完成，因此现在更偏接口骨架。
3. `trip.py` 里的 `/api/trip/health` 当前访问了 `agent.agent.name` 和 `agent.agent.list_tools()`，但 `MultiAgentTripPlanner` 没有 `agent` 属性，实际调用时可能报错。更合理的是检查 `attraction_agent`、`weather_agent`、`hotel_agent`、`planner_agent`。
4. 主规划流程是串行执行：景点 -> 天气 -> 酒店 -> 规划。没有并发调用，因此生成计划可能比较慢。
5. `planner_agent` 的 JSON 输出质量决定最终响应是否完整；如果 LLM 输出格式不稳定，就会触发兜底计划。
6. 兜底计划不会调用真实地图或天气服务，只保证前端有结构化数据可展示。

## 10. 一句话总结

这个后端的核心是 `MultiAgentTripPlanner`：FastAPI 接住前端请求后，把用户的旅行需求交给多个 BaseAgent Agent；前三个 Agent 通过高德 MCP 分别拿景点、天气、酒店信息，最后由规划 Agent 汇总成 JSON，再用 Pydantic 模型校验后返回给前端。
