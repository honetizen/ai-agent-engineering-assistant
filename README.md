# AI GitHub Engineering Assistant

AI GitHub Engineering Assistant 是一个面向 GitHub 工程协作场景的后端服务。项目目标是逐步接入 GitHub 数据，为后续的工程信息分析与辅助能力提供清晰、可扩展的服务基础。

## 当前阶段

当前处于 **V0：GitHub PR 数据接入** 阶段。本阶段仅建立最小可运行的 FastAPI 项目骨架，并为后续通过 GitHub REST API 获取 Pull Request 数据做好准备。

## 初步工作流

1. 从环境变量读取 `GITHUB_TOKEN`。
2. 接收 GitHub 仓库与 Pull Request 标识。
3. 使用 GitHub REST API 获取 Pull Request 数据。
4. 将标准化后的数据通过 API 返回给调用方。

当前版本仅实现服务健康检查，尚未实现 GitHub API 调用。

## 本地运行

1. 创建并激活 Python 虚拟环境。
2. 安装依赖：

   ```bash
   pip install -r requirements.txt
   ```

3. 复制 `.env.example` 为 `.env`，后续接入 GitHub API 时填写 Token。
4. 启动服务：

   ```bash
   uvicorn app.main:app --reload
   ```

5. 访问 `GET http://127.0.0.1:8000/health`，应返回：

   ```json
   {"status": "ok"}
   ```
