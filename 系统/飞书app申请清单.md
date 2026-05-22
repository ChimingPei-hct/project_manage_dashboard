# 飞书 App 复用核对清单 — PMD v1

> 决定:复用已有 lark-cli 应用 `cli_a943bae284f89cd1`,不新建。
> 凭证位置:`~/.lark-cli/config.json`(app_id) + macOS keychain(secret) + 环境变量 `LARK_APP_ID` / `LARK_APP_SECRET`。

后端 Phase 6 实现会优先读 `LARK_APP_ID` / `LARK_APP_SECRET`,无需粘贴 secret。

---

## 你要在 open.feishu.cn 做的两件事

### 1. 加重定向 URL

路径:开发者后台 → 找到 `cli_a943bae284f89cd1` → **安全设置** → **重定向 URL** → 追加:

```
http://localhost:15173/feishu/callback
```

> 大小写、端口、尾斜杠精确匹配。生产域名稳定后再加一条 https。

### 2. 核对 scope(可能已有,缺则补)

路径:**权限管理**,确认下列已勾选(或缺失则勾选→创建版本→走租户审批):

| Scope | 用途 |
|-------|------|
| `contact:user.base:readonly` 获取用户基本信息 | OAuth 拿 open_id/name/avatar |
| `contact:user.email:readonly` 获取邮箱(可选) | 展示用 |
| `contact:contact.base:readonly` 通讯录基本信息 | admin 配 owner 搜人 |
| 「以应用身份搜索通讯录」/ `contact:user:readonly` | 搜人 API 必需 |

**不要勾**:im / wiki / docx / drive / 日历 / Base — PMD v1 用不到。

---

## 完成后告诉我

- [ ] 重定向 URL 已加 `http://localhost:15173/feishu/callback`
- [ ] scope 已具备(或已申请审批通过)

我这边并行写 Phase 6 代码,你这两步完成 + 我代码完成,就能跑通真实登录。

---

## 注意

- 这个 app 原本是 lark-cli 用的,**OAuth 弹窗里显示的名字/图标就是当时建 app 时填的**(不是"PMD 项目看板")。dev 期自己测无所谓;后期演示前再建一个独立 app。
- App Secret 不要贴到聊天或 commit 到代码,后端读环境变量。
