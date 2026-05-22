# app/ — 代码与约束对齐路由

> 进入 `app/` 修改代码前,必须先按下方路由表读对应约束文档。

## 路由表

| 修改对象 | 必读约束 |
|---------|---------|
| 后端任何代码 | `design/11-后端API约束.md` |
| 数据读写实现 | `design/03-代码与数据分离约束.md` + 对应 Schema(`06`/`07`/`08`/`09`) |
| 认证 / 中间件 | `design/11-后端API约束.md` 第 6 节 + `design/10-权限与角色约束.md` |
| 新增写端点 | `design/10-权限与角色约束.md`(矩阵 + 测试用例) + `design/11` |
| 前端任何组件 | `design/12-前端实现约束.md` |
| 任意页面布局/编辑入口 | `design/13-页面编辑与展示约束.md` |
| 数据模型扩展 | `design/05-模块与状态模型基础规则.md` + 对应 Schema |

## 启动

```bash
./start.sh    # 拉起后端 (8000) + 前端 dev server (5173)
```

后端默认走 dev 后门(`DEV_LOGIN=1`),`DATA_DIR=../design`。

## 子目录

| 目录 | CLAUDE.md |
|------|-----------|
| `backend/` | `backend/CLAUDE.md` |
| `frontend/` | `frontend/CLAUDE.md` |
