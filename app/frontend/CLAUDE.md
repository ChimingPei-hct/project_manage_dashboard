# app/frontend/ — 前端代码约束路由

## 进入前必读

- `design/12-前端实现约束.md` — 技术栈、目录、UI 规范、状态管理、SSE、API 客户端
- `design/13-页面编辑与展示约束.md` — 四类页面的展示主信息与编辑入口
- `design/10-权限与角色约束.md` — 前端按权限显隐编辑入口

## 技术栈红线(不可引入)

- ❌ Vue Router(用 `?view=` query 路由)
- ❌ Pinia(用 `composables/use*.js`)
- ❌ Element Plus / Ant Design Vue / Vuetify / Naive UI
- ❌ Tailwind CSS
- ❌ axios(用原生 `fetch`,封装在 `api/client.js`)

## UI 红线

- ❌ `border-radius: 50%` / `9999px` / 高度同量级的大圆角(禁止胶囊形)
- ❌ Hardcode 状态色(必须用 `--status-green/yellow/red` CSS 变量)
- ❌ 跳过 `v-tooltip` 直接 `title=""`(`title` 仅作长说明兜底)
- ❌ 在组件内直接 `fetch`(走 `api/client.js`)
- ❌ 给"未填报"赋绿/黄/红色(用灰)

## 新增可交互元素强制流程

1. 加 `v-tooltip="文案"`,动词开头说"会发生什么"
2. 权限可见性:从 composable 拿 `canEdit(moduleId)`,不在组件硬编码
3. 6px 圆角,色用 CSS 变量
4. 若引入新页面 → 同步更新 `design/13`

## 测试与构建

```bash
npm install
npm run dev      # 端口 5173,代理 /api → http://localhost:8000
npm run test     # vitest
npm run build    # 产出 dist/
```

## 参考实现

视觉与组件参考 `/Users/xubinfeng/repos/oversea_projects/app/frontend/src/`,但**不可直接拷贝业务逻辑**,需按本系统的 Schema(`design/06`–`09`)重写。
