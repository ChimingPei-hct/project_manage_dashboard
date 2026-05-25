# Luna 6 PDT 原始素材汇总（待回填）

> **用途**：本文件冷藏 Luna 6 产品线的组织结构与模块进展，源自三份飞书 wiki。
> 待后端 API / 写流程开发完成后，按本文件 1:1 翻译进 `data-luna6` 分支的 `design/pdt.json / ltcs.json / modules.json / module_status.json`。
> **不入产品**：`datas/` 已在 .gitignore，构建/校验不会读到本文件。
> **抓取日期**：2026-05-22

---

## 1. 来源

### 1.1 抓取信息

| 项 | 值 |
|---|---|
| 抓取日期 | 2026-05-22 |
| 抓取工具 | `lark-cli docs +fetch`（lark-doc / lark-wiki skill） |
| 飞书租户 | `neuehct.feishu.cn` |
| Wiki space | `7483771646793678876` |
| 抓取身份 | user（个人 token） |
| 原始 dump | `/tmp/luna6_doc1.md`（5/20 周报）、`/tmp/luna6_doc2.md`（5/13 周报）、`/tmp/luna6_doc3.md`（入门指南） |

### 1.2 源文档清单

| Wiki URL | node_token | docx token | 标题 | 字数 | 用途 |
|---|---|---|---|---|---|
| https://neuehct.feishu.cn/wiki/ChkuwPV5fidGkwkXHD3c8FiNnUe | `ChkuwPV5fidGkwkXHD3c8FiNnUe` | `SfQNdX3IMoreBQx5vOMcOJmznId` | Luna6 入门指南 | 2932 | PDT 章程 / 战略目标 / 运作机制 |
| https://neuehct.feishu.cn/wiki/JIAzwUpfbibduuk7Acic5WTtnrh | `JIAzwUpfbibduuk7Acic5WTtnrh` | `TTyLddmbQoYahFx2yQGcAEtcnQM` | 20260513-Luna6软件周例会 | 25840 | 模块矩阵（前一周，进展更详） |
| https://neuehct.feishu.cn/wiki/GgH1wGa5ZiPT2bk49Ppc5RlVn2m | `GgH1wGa5ZiPT2bk49Ppc5RlVn2m` | `NN94dEZNhoc2vkxCDALcEX3YnZb` | 20260520-Luna6软件周例会 | — | 模块矩阵（最新快照） |

两份周例会使用同一个 18 行 × 4 列表「Luna6 项目集进展」，列为：专项/领域 / 月度目标 / 本周进展 / 风险与求助。两次抓取结构一致，本文件主要数据来源为 5/13 版本（进展字段更饱满），少数差异处以 5/20 为准。

### 1.3 各节信息溯源

| 本文件节 | 来源 wiki | 来源段落/表行 |
|---|---|---|
| 2 PDT | 入门指南 | "Luna6 的共同使命" + "产品线核心目标" + "产品线核心价值" |
| 3 战略里程碑 | 入门指南 | "产品线核心目标" 三条 |
| 4 运作机制 | 入门指南 | "产品线运作 / 运作机制" 表（5 行 × 5 列） |
| 5 LTC 清单 | 两份周报 | 「Luna6 项目集进展」表中所有模块的子分组（按客户/平台维度反推聚合） |
| 6.1 性能专项 | 5/13 周报 | 表第 2 行 |
| 6.2 开发环境准备 | 5/13 周报 | 表第 3 行 |
| 6.3 Ut | 5/13 周报 | 表第 4 行 |
| 6.4 qnx 迁移 | 5/13 周报 | 表第 5 行 |
| 6.5 基础服务迁移 | 5/13 周报 | 表第 6 行 |
| 6.6 数据工具迁移 | 5/13 周报 | 表第 7 行 |
| 6.7 模型推理 | 5/13 周报 | 表第 8 行 |
| 6.8 全栈规控集成 | 5/13 周报 | 表第 9 行 |
| 6.9 感知集成 | 5/13 周报 | 表第 10 行 |
| 6.10 主线/泊车集成 | 5/13 周报 | 表第 11 行 |
| 6.11 软件底座-A 核 | 5/13 周报 | 表第 12 行 |
| 6.12 软件底座-MCU | 5/13 周报 | 表第 13 行 |
| 6.13 数采专项 | 5/13 周报 | 表第 14 行 |
| 6.14 标定 | 5/13 周报 | 表第 15 行 |
| 6.15 回灌 | 5/13 周报 | 表第 16 行 |
| 6.16 人力/非人力资源 | 5/13 周报 | 表第 17 行 |
| 7 PDT lead | 5/13 周报 | "Luna6 项目集进展" 表标题旁 @ 的 mention-user |
| 8 open_id 表 | 5/13 周报 + 5/20 周报 | 全部 `<mention-user id="ou_*"/>` 去重 |
| 9 关联资源 | 三份 wiki | 全部 `<mention-doc>`、`<bitable>`、`<whiteboard>`、`<sheet>` token |

### 1.4 重新抓取命令（如需更新）

```bash
# 抓取 wiki 节点正文为 markdown
lark-cli docs +fetch --wiki ChkuwPV5fidGkwkXHD3c8FiNnUe --format markdown > /tmp/luna6_doc3.md
lark-cli docs +fetch --wiki JIAzwUpfbibduuk7Acic5WTtnrh --format markdown > /tmp/luna6_doc2.md
lark-cli docs +fetch --wiki GgH1wGa5ZiPT2bk49Ppc5RlVn2m --format markdown > /tmp/luna6_doc1.md
```

---

## 2. PDT

```yaml
code: LUNA6
name: Luna 6
description: |
  Luna 6 是 PDT 级低阶智能驾驶产品线，含两个变体：
  - Luna6A: 8MP 一体机，可扩展至 5R+DMS；面向法规准入级最小系统，NCAP 5 星，safety always on
  - Luna6B: 5V5R12U 行泊一体小域控；ICA 纵向体验对齐 HSA Lite
  使命：智能驾驶平权，让全球每一个人的出行更安全、更便捷。
  愿景：行业领导者，将领先的智能驾驶产品带到世界的每一个角落。
  长期目标：生命周期出货千万，2030 年前进入全球低阶智驾 Top3。
updated_at: 2026-05-22T00:00:00+08:00
metadata:
  variants: [Luna6A, Luna6B]
  charter_wiki: ChkuwPV5fidGkwkXHD3c8FiNnUe
```

---

## 3. PDT 战略里程碑（pdt.json::milestones[]）

```yaml
- name: 国内项目出海 Alpha 量产
  date: 2026-06-30   # 26Q2 截止参考日，原文未给具体日期
  type: goal
  note: 26 年 Q2 前达成

- name: 极致成本之上的产品竞争力
  date: 2027-12-31
  type: goal
  note: 27 年目标

- name: 海外市场全面铺开
  date: 2028-12-31
  type: goal
  note: 28 年目标
```

---

## 4. 运作机制（参考，不入运行时数据）

来源：`HC-IPD-P01-W06 PDT 运作管理规范.docx`（wiki `PN0HwmobwiSLKNkKq1Ycmga6nlc`）

| 会议类型 | 目的 | 频次 | 核心成员 | 备注 |
|---|---|---|---|---|
| 经营分析会（产品线） | 检查目标达成进展，识别主要矛盾，明确解决路径、责任人及计划 | 月度 | 产品部负责人、PDT 经理、财务 BP、HR BP、市场代表、开发代表 | — |
| PDT 例会（产品线） | 同步 PDT 平台项目与交付项目进展、风险及问题 | 周度 | PDT 经理、核心代表、产品部负责人（可选） | 项目增加后，交付项目独立例会 |
| 领域例会（产品线） | 同步领域进展与风险，跟踪 PDT 衍生任务/问题 | 周度 | 关联领域核心代表、核心领域扩展代表 | 问题来源：目标分解 + PDT 例会输出 |
| 交付例会（待明确） | TBD | TBD | TBD | 需进一步明确会议定位 |
| 项目例会 | 跟踪单个客户交付项目的进展、风险及问题 | 周度 | CPM（客户项目经理）、DPM（开发项目经理）、项目核心组 | 聚焦具体客户项目执行层 |

软件周例会：每周三 16:00-17:00 (GMT+8)，会前写完周报，飞阅 10 分钟，16:10 开始周会。

---

## 5. LTC 清单（10 个，ltcs.json）

```yaml
- id: mainline-id4
  name: 主线 ID4
  order: 1
  archived: false
  metadata: { jira_prefix: LUNA6 }

- id: ay7
  name: AY7（白云山 / 广汽）
  order: 2
  archived: false
  metadata:
    customer: 广汽
    code_name: 白云山
    jira_prefix: LUNA6
    customer_req_wiki: CJyCwaMytiLFG0khk4Ac25CPndd
    sysarch_wiki: IiYzw5UJdiqloMkDnh8c9hTDnJd
    feature_list_wiki: QqpiwifZli9OwQkjhsxcIEiwnTh

- id: btet
  name: BTET
  order: 3
  archived: false
  metadata: { jira_prefix: BTETJ6 }

- id: zs32-allinone
  name: ZS32 一体机
  order: 4
  archived: false
  metadata: { variant: 一体机 }

- id: zs32-ecu
  name: ZS32 小域控
  order: 5
  archived: false
  metadata: { variant: 小域控 }

- id: zp22
  name: ZP22
  order: 6
  archived: false

- id: ft
  name: FT (KX21)
  order: 7
  archived: false
  metadata: { hw_platform: KX21 }

- id: mmc
  name: MMC
  order: 8
  archived: false
  metadata: { scope: 国内+海外 }

- id: byd
  name: BYD
  order: 9
  archived: false
  metadata: { stage: bringup/DV }

- id: ecarx-kx21
  name: ECarx KX21
  order: 10
  archived: false
  metadata: { hw_platform: KX21 }
```

---

## 6. 模块（16 个，modules.json）

> **scope 划分原则**：横向专项 → `scope: pdt`；按 LTC 分别推进的领域 → `scope: ltc` 并在每个 LTC 下重复一份 module。本节给出每个模块的「LTC 拆解」列表，落 JSON 时按 LTC 数量复制即可。
>
> **status_hint 来源**：源 wiki 中 `bgcolor="light-yellow"` → `yellow`；`bgcolor="light-red"` → `red`；其他 → `green`。

### 6.1 性能专项 (pdt-perf)

```yaml
id: pdt-perf
scope: pdt
group: 工具链与专项
name: 性能专项
order: 1
owners: [ou_b0ec727bdd0ea2fc9d7ffce5245a1737]
monthly_goal:
  - DeepPerf 功能维护、完善与优化
  - 项目性能分析和优化
status_hint: yellow   # 表头黄色标记
sub_items:
  - { id: deepperf, name: DeepPerf 服务与数据迁移 }
  - { id: delay-stat, name: delay 统计方案优化 }
  - { id: kev-stat, name: kev 数据采集与解析优化 }
weekly_progress: |
  已完成：
  - DeepPerf 服务迁移到阿里云稳定运行；老版本数据上传/下载通道全关，仅保留旧报告链接访问
  - 优化交互、修复后台重新解析、增加分支筛选、优化 CPU 大数据卡顿
  进行中：
  - 纯 C++ topic 录制工具，支持动态过滤落盘，初步验证较 mcap 降 50%+
  - kev：对 model_inference / pnc 插桩 >2000 次，10-15s 抓 1.5G，对感知/规控进程稳定性有影响，待优化
risk_note: ""
```

### 6.2 开发环境准备 (pdt-devenv)

```yaml
id: pdt-devenv
scope: pdt
group: 工具链与专项
name: 开发环境准备
order: 2
owners:
  - ou_c4433a950aebfa7ebcdd13620ee6aecb   # lead
  - ou_f62bc6e6034dfba1e82eef562bb75e6c
  - ou_f12c0a626727a06bc906a7da9022396d
  - ou_8328f796183de2c6872d9849090fd96c
  - ou_f3ea63f9f05ea0e0730692e1be3269e6
monthly_goal:
  - CICD APP/BSP 门禁 + 打包支持
  - APP 日常构建支持
status_hint: green
sub_items:
  - { id: ota-build, name: OTA 出包 }
  - { id: hil-test, name: 台架测试 }
  - { id: code-gate, name: 代码门禁 }
weekly_progress: |
  OTA 出包：BSP 编译归档 install；MCU/BSP 适配 ZS32-ME-ICE-LC-1J6B、ZS32-ME-HEV-LC-1J6B、ZP22-ME-HEV-LC-1J6B
  台架测试：搭建性能测试流水线，支持 ID4 / KX21
  代码门禁：APP 门禁支持 PNC 测试任务通过率为 0 的拦截；MCU 容器编译无法访问 Coverity License，正申请单独机器
risk_note: ""
```

### 6.3 Ut (pdt-ut)

```yaml
id: pdt-ut
scope: pdt
group: 工具链与专项
name: Ut（单元测试）
order: 3
owners: [ou_e4814d969b5108b8f11893107daa27ce]
monthly_goal:
  - auto_ut 最终版本定稿，适配高复杂代码覆盖率、适配 vcast 自动化方案脚本
  - auto_ut_batch 批量执行，规范输出物完成
  - vcast 24 版本 license 自动化方案开发，适配上游
status_hint: red   # vcast24 适配冲突标红
sub_items:
  - { id: auto-ut, name: auto_ut 5.0 }
  - { id: auto-ut-batch, name: auto_ut_batch }
  - { id: vcast24, name: vcast24 适配 }
weekly_progress: |
  vcast24 适配 auto_ut 5.0：g++11 与 auto_ut 用 g++13 冲突，适配方案设计开发中
  auto_ut 5.0 验收中，协助德谕完成关键问题设计与修改，预计 26/05/14 完成交接
risk_note: g++ 版本冲突
```

### 6.4 开源框架/协议 qnx 迁移 (pdt-qnx-migration)

```yaml
id: pdt-qnx-migration
scope: pdt
group: 框架与迁移
name: 开源框架/协议 qnx 迁移
order: 4
owners: [ou_c7bf1dca0d400e9fe9b2539a20cbf400]   # PDT lead
monthly_goal:
  - ros2 py 支持完成
  - 释放 ros2 提供给知行
  - 完成 ros2 第一轮裁剪
  - py 库支持完成
status_hint: red   # Gateway 标红
sub_items:
  - id: ros2-adaptation
    name: ROS2 适配（AY7/BTET/FT/ZS32）
    owners: [ou_f90be8f1191e284ecf437a87e3464092, ou_6513ec393c67947adf468ffe71ac4e2c]
  - id: ros2-upgrade
    name: ros2 升级
    owners: [ou_f90be8f1191e284ecf437a87e3464092]
  - id: gateway
    name: Gateway
    owners: [ou_f90be8f1191e284ecf437a87e3464092]
    status_hint: red
  - id: dvr
    name: DVR
    owners: [ou_6513ec393c67947adf468ffe71ac4e2c, ou_f90be8f1191e284ecf437a87e3464092]
weekly_progress: |
  ROS2-AY7：解决 model_infer / 标定压测 / 知行工具反序列化 / 日志降频 jira 单；ros2 发版测试完成
  ROS2 升级：升级分支直接使用有问题，分析代码差异，基础通信功能验证中
  Gateway：完成 adapter 使用说明文档；解决 zs32 worldsim 方案 x86 → j6b 透传数据问题
  DVR：kx21 关闭 rtcp 协议；分析 LUNA6-5636 遗留 bug
risk_note: ""
```

### 6.5 基础服务迁移 (ltc-*-base-service)

```yaml
id_pattern: ltc-{ltc_id}-base-service
scope: ltc
group: 集成
name: 基础服务迁移
order: 5
owners:
  - ou_87ece67c54c636362c4020ff0040592b
  - ou_2a65626de9196c1ff374c71dc81a94f0
  - ou_cfa2107ad7b43c2f4fa578d3e8772bca
monthly_goal:
  - Sensor 适配开发
  - Vehicleio 适配开发
  - OTA 适配开发
status_hint: green
ltc_breakdown:
  - ltc: mainline-id4
    owner: ou_cfa2107ad7b43c2f4fa578d3e8772bca
    weekly_progress: 主线消息裁剪了 100+ 无用文件，hil 台架回灌不能进功能，调查中；id4 方向盘握手信号增加，联调
  - ltc: ay7
    owner: ou_cfa2107ad7b43c2f4fa578d3e8772bca
    weekly_progress: ""
  - ltc: btet
    owner: ou_34be37dee83dfbc452d03a8b13fff9b7
    weekly_progress: ""
  - ltc: zs32-allinone
    owner: ou_658540583f0083b8f2d15314bbcf4348
    weekly_progress: 信息安全防火墙信息上报上线；http 故障上报验证；dos 攻击故障上报验证；02 文件刷写偶发诊断不回复定位；一体机配置字更新
  - ltc: zs32-ecu
    owner: ou_658540583f0083b8f2d15314bbcf4348
    weekly_progress: 小域控配置字更新；同步一体机 OTA 到小域控，验证 OFFER 报文及 IP 问题；摄像头 OTA 熟悉中；Uss msg 变更
  - ltc: ft
    owner: ou_d876d1bca4aeb42d1d13f9a08146ab11
    weekly_progress: 应用层适配工厂/用户模式；FT 反馈 fault id/DTC 无法上报排查；诊断/FM 配置更新；进入背景标定不出图，初定位 ptp0 与 hct_time 固定相差 200ms
  - ltc: mmc
    owner: ou_87ece67c54c636362c4020ff0040592b
    weekly_progress: ntp 作为初始时间源实车可行性验证；X86 复用海外配置字识别 ntp 授时；J6B 通过 ipcf 给 R 核设置 RTC
```

### 6.6 数据工具迁移 (ltc-*-data-tools)

```yaml
id_pattern: ltc-{ltc_id}-data-tools
scope: ltc
group: 工具链与专项
name: 数据工具迁移 / HDE
order: 6
owners:
  - ou_4d93967a8fe4b987011a4c023d948ef1
  - ou_6caaa36a550febdc00758ef45ebc33b8
  - ou_c40504df5ee4683e43c2ed31e5a406ff
  - ou_6a019448419b24a3cc3751ede1d89a36
monthly_goal:
  - 数据工具迁移
  - Someip 协议拆解与适配
status_hint: green
sub_modules:
  - id: ay7-hde
    name: AY7 客户 HDE
    owners: [ou_6caaa36a550febdc00758ef45ebc33b8, ou_c40504df5ee4683e43c2ed31e5a406ff]
    ltc_breakdown:
      - ltc: mainline-id4
        weekly_progress: 【泊车】后台搜车位开发完成，实车验证中
      - ltc: ay7
        weekly_progress: LUNA6-5331 ACC/ICA 接管报警时机优化
      - ltc: btet
        weekly_progress: 已完成 BTETJ6-86/90/95/93/96；进行中 TLR 红绿灯添加、动态目标显示、SWR 需求文档
      - ltc: zs32-allinone
        owner: ou_38e3ae26c22830f586bcb2643c4c40b3
        weekly_progress: ICA/ACC 功能状态显示、行驶提醒、接管需求开发完成；0.5.2 LSS / IHBC / TSR 提示完成；硬开关与软开关调试中；故障显示与环境渲染开发中
      - ltc: zs32-ecu
        owner: ou_c40504df5ee4683e43c2ed31e5a406ff
        weekly_progress: 泊车框架代码完成；APA 台架自测 OK，后台搜车位/软硬开关/文言交互/泊车渲染代码 OK；APA/后台搜车位/RPA/EPA 实车联调与开发中
      - ltc: ft
        weekly_progress: 修复车道线不显示、泊车 slot 数据缺失、slot topic 错误、is_standby 映射错误；进行中 fcw 开关映射、行车故障报警、SWR 文档
      - ltc: mmc
        weekly_progress: ""
  - id: data-feedback
    name: 数据回传
    owners: [ou_6a019448419b24a3cc3751ede1d89a36, ou_4d93967a8fe4b987011a4c023d948ef1]
    weekly_progress: |
      kx21 环视数据流接入 trigger，基于 FT 修复版本验证完成
      kx21 Trigger 支持 parking topic 录制，验证中
      主线 trigger2.0 迁移，进程编译完成，调试中
      主线 dc 模块 param2 适配，待验证
      新车质检、can 接入、atx 接入等适配
      客户车 T75 改制问题跟进，涉及新硬件分流器适配，方案待验证
```

### 6.7 模型推理及推理框架 (pdt-model-inference)

```yaml
id: pdt-model-inference
scope: pdt
group: 集成
name: 模型推理及推理框架
order: 7
owners:
  - ou_43a6d27bd8d7a5a426a7d8380bba99ac
  - ou_ed4ae550cfc4019866253c443789496f
  - ou_201c2467a7df5abc9479e3ab76dd8431
monthly_goal: []   # 原表月度目标空
status_hint: green
sub_items:
  - { id: model-integration, name: 模型集成 }
  - { id: model-perf, name: 性能 }
  - { id: overseas-single-pkg, name: 海外左右舵单包 }
  - { id: fisheye-sparse4d, name: 3v 鱼眼 sparse4d }
  - { id: tld-depth, name: tld+depth }
weekly_progress: |
  Modeinfer Coverity 初步分析确认工作量和修改思路
  红绿灯新增 Depth/Yaw 输出需求，兼容国内外方案
  空气悬架主线版本实车测试三种配置一致，附带回灌测试输入一致性验证
  KX21 实车联调，空气悬架信号接入完成，挡位切换功能等上游
  鱼眼感知与模型一起确定输入输出，模型集成代码 50%
risk_note: ""
```

### 6.8 全栈、规控集成 (ltc-*-fullstack-pnc)

```yaml
id_pattern: ltc-{ltc_id}-fullstack-pnc
scope: ltc
group: 集成
name: 全栈、规控集成
order: 8
owners:
  - ou_f9620d8c753df409e3068ddd0e8d26f9
  - ou_43dce79f6e7971b1507f42ad74c73773
  - ou_ee5b2fa0e6fc5e60362376fa07abeea2
  - ou_20868fffe17b4eab496fc12a16719835
monthly_goal:
  - 负载优化
  - 软件稳定性提升
  - 版本集成质量 & 效率提升
status_hint: green
ltc_breakdown:
  - ltc: ay7
    owner: ou_f9620d8c753df409e3068ddd0e8d26f9
    weekly_progress: ReleaseNote Luna6_LC-V9.0.0-WL19-20260511；LTC 标定首车信息同步；PNC 反向依赖修复
  - ltc: zs32-allinone
    owner: ou_f9620d8c753df409e3068ddd0e8d26f9
    weekly_progress: 联调开发中；App 1+n 开发中
  - ltc: zs32-ecu
    owner: ou_f9620d8c753df409e3068ddd0e8d26f9
    weekly_progress: ReleaseNote Luna6_LC-Develop-20260509_79
  - ltc: btet
    owner: ou_b1ee4d42208d99f1db8142a8c983ca0d
    weekly_progress: 4.0 版本集成转测
  - ltc: ft
    owner: ou_43dce79f6e7971b1507f42ad74c73773
    weekly_goal: V4.2.0 版本发布（Bsp v8→v10/mcu→sdk1.0、热拔插/出流问题、doip 启动时间优化、日志模块 bug、isp hx11/e245 标定、新增泊车 topic 联调、bug 修复、自动化台架、时间同步）
    weekly_progress: bsp v8→v10 完成；热拔插/出流问题解决；新增泊车信号 topic 联调；日志模块 bug 修复；时间同步已知问题进行中；时间同步功能上线 delay
  - ltc: mmc
    owners: [ou_ee5b2fa0e6fc5e60362376fa07abeea2, ou_8c952c6e8406342121b7bb5e6a615628]
    weekly_progress: V3.0.0 内部版本转测；进场版本 V3.0.2 集成
  - ltc: zp22
    owners: [ou_b1ee4d42208d99f1db8142a8c983ca0d, ou_f9620d8c753df409e3068ddd0e8d26f9]
    weekly_progress: 分支并线已完成
  - ltc: ecarx-kx21
    owner: ou_87ece67c54c636362c4020ff0040592b
    weekly_progress: ""
sub_modules:
  - id: auto-efficiency
    name: 自动化能效提升专项
    owners: [ou_d021a8b922e51bc09a5b5ca69a319557, ou_2d8560390427c2012f48d06af63901da]
    weekly_goal: FT HIL 流水线上线；ID4 性能流水线上线
    weekly_progress: FT HIL 自动化测试框架适配；FT 功能激活 ica/aeb 触发台架测试；CICD 自动化流水线适配/调试；功能激活 case 适配
```

### 6.9 感知集成 (pdt-perception)

```yaml
id: pdt-perception
scope: pdt
group: 集成
name: 感知集成
order: 9
owners:
  - ou_b1ee4d42208d99f1db8142a8c983ca0d
  - ou_9d343f69514709805d17341af8640d53
monthly_goal: []
status_hint: green
sub_items:
  - { id: param2-switch, name: param2 切换 }
weekly_progress: |
  进行中：param2 切换
risk_note: ""
```

### 6.10 主线/泊车集成 (pdt-mainline-parking)

```yaml
id: pdt-mainline-parking
scope: pdt
group: 集成
name: 主线/泊车集成
order: 10
owners:
  - ou_51d8d0fd13abbd9cf6673553bb3abc63
  - ou_9f233ef7fbf2dd598cd5187eba0596e1
  - ou_ee5b2fa0e6fc5e60362376fa07abeea2
monthly_goal: []
status_hint: red    # HMI/HDE 标红
sub_items:
  - id: mainline-integration
    name: 主线集成
    owners: [ou_0b0aafc13279faa9245e803bcd2a3b02]
    weekly_goal: 实车开环通路打通
  - id: parking-perception
    name: 泊车感知
    owners: [ou_ee5b2fa0e6fc5e60362376fa07abeea2]
    weekly_goal: zs32 泊车实车功能闭环
    weekly_progress: id4 泊车手台搜车位等待 hde 联调；id4 泊车感知诊断功能开发中
  - id: hmi-hde
    name: HMI/HDE
    owners: [ou_9f233ef7fbf2dd598cd5187eba0596e1, ou_41b9f6003c87efa1ef943a0bd9284511]
    status_hint: red
risk_note: HMI/HDE 标红
```

### 6.11 软件底座-A 核系统及底软 (ltc-*-acore-os)

```yaml
id_pattern: ltc-{ltc_id}-acore-os
scope: ltc
group: 硬件和底软
name: 软件底座 - A 核系统及底软
order: 11
owners: [ou_626d8eaf98cbfb6add0474ac1eb14723]
monthly_goal:
  - 小域控 bringup
  - DV 软件开发
  - 信息安全开发
status_hint: red   # BTET 与 MMC 行内标红
ltc_breakdown:
  - ltc: ay7
    weekly_progress: ""
  - ltc: byd
    weekly_progress: ""
  - ltc: ft
    owner: ou_84ddecb7a8befdc338a99147c12e96de
    weekly_progress: |
      norflash 分区对齐修改完成，提供给 ft 验证写保护
      cpu loading 高，定位到 /app/init.sh / /app/ft_app/app_start.sh 启动脚本拉起的服务占用高
      soc 卡死问题，FT 已合入 safetylib 版本，偶发 mcu 启动流程异常未执行到拉起 acore，查看 mcu 启动异常中
      tcp 重连超时（需求 15s，实测 26s），优化 ft 服务初始化到 16s
      v10 基线升级，新适配摄像头相关基线发布中
      禁止启动阶段进入 uboot 菜单，调试中
  - ltc: btet
    owner: ou_0b43891f8f9841c4cc6183cb9740c62e
    status_hint: red
    weekly_goal: PV 版本发版
    weekly_progress: PV 版本发版完成
  - ltc: zs32-allinone
    owner: ou_abf27289e9906edb0404a7943160dbc8
    weekly_progress: ""
  - ltc: zs32-ecu
    owner: ou_b645ce9f87dbc0a53b3271a188443140
    weekly_goal: idps 开发 / 内仓 CICD 打通
    weekly_progress: idps 开发完成已同步外仓给 ME；内仓 CICD 打通完成
  - ltc: mmc
    owner: ou_e4e35914e61b024dc482111de5217064
    status_hint: red
    weekly_progress: v3.0.0 验证发布；Pv 2.2.2 验证完成及发布；pv2.6 功能验证中
```

### 6.12 软件底座-MCU (ltc-*-mcu)

```yaml
id_pattern: ltc-{ltc_id}-mcu
scope: ltc
group: 硬件和底软
name: 软件底座 - MCU
order: 12
owners: [ou_e95e84006454dea6d717499ed55d8bf3]
monthly_goal:
  - 开发环境同步
  - ETAS 专项
  - 小域控 bringup 版本
status_hint: green
ltc_breakdown:
  - ltc: ay7
    owner: ou_e95e84006454dea6d717499ed55d8bf3
    weekly_progress: |
      JIRA-5673 eol 标定压测：hardware reset 引起的 ecu 复位 / power off 硬件掉电引起复位
      JIRA-5679 偶现 mbdiso 报，未复现，与质量沟通后走降级流程
  - ltc: byd
    owners: [ou_d219b269c7c29cef281b39b27fb5e78d, ou_2cbd4663d3dc282bee2069740e643964]
    weekly_progress: bringup 软件开发；DV 软件开发；BYD 出差联调中——串口刷写成功，Norflash 启动失败排查中
  - ltc: btet
    owner: ou_6b940c7d25feee08901eb2ae63731a0e
    weekly_progress: |
      安全日志开发；国标诊断 ID 与原诊断 ID 共用诊断服务列表
      BTETJ6-50/86 需求变更已流转；BTETJ6-100 cantp 参数配置已修复
      V4.0 jira 修复进行中
  - ltc: zs32-allinone
    owners: [ou_17d49a8c66ea62ac5812f187bd4ec3ae, ou_d219b269c7c29cef281b39b27fb5e78d]
    weekly_progress: |
      TR 文档和 SWR 完成；EOL/售后标定链路联调
      报文 timeout DTC 报出机制调整
      DID B0D2 网络 DoS 攻击记录功能完善
      DID B008 内部故障状态长度 80→100 字节
      DID CF06 回复 NRC10 问题修复
      RTE/VOA/VIA 接口表更新；Monitor 需求；Jira 分析修复
  - ltc: ft
    owners: [ou_996338561a87def0ced6d52281f03da8, ou_54e40be083adb2771715aabe2b981163]
    weekly_progress: |
      kx21 RTE 支持 XCP 注入，follow 原 AY7 测试方法
      kx21 RTE V4.3.0 更新，添加 ICCdebug/ACCdebug
      kx21 Vehio 添加 ICCdebug/ACCdebug 下行调试
      客户侧切分区行为分析报告
      139/141 车无法控车 — 接线问题，从原线束破拆
      SOC 无法启动初步排查结论已出
      SDK100 升级测试支持
      kx21 Monitor/PecpIn 小 V 文档完成
      实车 trigger 上报 failed — CAN2IPC 2 合 1 时 CAN Frame count 逻辑问题，重新出包验证中
  - ltc: mmc
    owner: ou_7f23e55a47499e83119f3fa68a6b52e0
    weekly_progress: |
      31 服务权限区分，修复标定问题
      0x3B 服务修复；S3 超时机制调整
      V3.0.0 软件测试问题澄清
      Jira 修复和流转：38/39/44/47/57-71
      PV 软件开发和联调，欠压/过压无法关闭通讯和诊断修复，电压阈值调整
      Monitor RTE 接口开发完成
      数采 IPC 时间同步方案开发完成待联调（从 A 核获得时间源）
      进行中：Monitor / 热保护 / 看门狗 / 小 V 文档 / docan 联调压测
  - ltc: zs32-ecu
    owner: ou_54e40be083adb2771715aabe2b981163
    weekly_goal: V2.0 软件开发
    weekly_progress: 算法查找下行链路问题已查到，已同步 ME；Monitor 模块代码开发完成；测试 Monitor 模块输入输出逻辑
```

### 6.13 数采专项 (pdt-data-collection)

```yaml
id: pdt-data-collection
scope: pdt
group: 工具链与专项
name: 数采专项
order: 13
owners:
  - ou_6a019448419b24a3cc3751ede1d89a36
  - ou_4d93967a8fe4b987011a4c023d948ef1
  - ou_2ed77a441c1cf8ce502e205c3aee7220
monthly_goal:
  - AY7 数采开发
status_hint: green
sub_items: []
weekly_progress: ""
risk_note: ""
```

### 6.14 标定 (pdt-calibration)

```yaml
id: pdt-calibration
scope: pdt
group: 工具链与专项
name: 标定
order: 14
owners: [ou_e6d3b8112f03ce5859fc5c1b1c80c5b5]
monthly_goal:
  - "[done] eol 交付，产线联调"
  - "[done] online 售后在线标定流程适配"
  - "[done] online 标定性能评估"
  - "[done] paramcheck 交付"
  - 车辆标定参数维护
status_hint: green
sub_items:
  - { id: param1-to-param2-mcap, name: param1→param2 mcap 转换工具 }
  - { id: front-mono-merge, name: front 切 front_mono 合入 }
  - { id: saic-aftersales, name: 上汽售后背景标定光流算法 }
  - { id: geely-test, name: 吉利测试用例 }
  - { id: kx21-mmc-zs32-design, name: kx21/mmc/zs32 小域控 cb / 概设 / 详设 }
  - { id: zs32-ecu-cal, name: zs32 小域控标定联调 }
weekly_progress: |
  已完成：mcap 转换工具；front 切 front_mono 主线合入；上汽售后背景标定光流算法实车验证；吉利测试用例与问题修复
  进行中：kx21/mmc/zs32 小域控设计文档；zs32 小域控与 ME 锁需求/赋能/开发；zs32 小域控标定联调
risk_note: ""
```

### 6.15 回灌 (pdt-replay)

```yaml
id: pdt-replay
scope: pdt
group: 工具链与专项
name: 回灌
order: 15
owners:
  - ou_a9085a40fbafbe2957ed1bdcee2d3705
  - ou_f9620d8c753df409e3068ddd0e8d26f9
monthly_goal:
  - "[done] J6B PAC 集群感知回灌"
  - "[done] J6B PAC 集群脱敏回灌"
  - "[done] LC 合线后 docker gpu 回灌 & 云端回灌"
  - "[done] PNC 开环回灌上云"
status_hint: green
sub_items:
  - { id: drive-replay, name: 行车回灌 }
  - { id: param2-cloud-replay, name: param2 云端回灌 }
weekly_progress: |
  进行中：感知回灌适配切换 param2
risk_note: ""
```

### 6.16 人力/非人力资源 (pdt-resources)

```yaml
id: pdt-resources
scope: pdt
group: 资源
name: 人力/非人力资源
order: 16
owners: [ou_5585cc420bde9bdf016f8367fb20bac0]
monthly_goal: []
status_hint: green
sub_items: []
weekly_progress: ""
risk_note: ""
```

---

## 7. PDT lead

| open_id | 角色 | 备注 |
|---|---|---|
| `ou_c7bf1dca0d400e9fe9b2539a20cbf400` | PDT lead | 周报开头 mention 的负责人，亦 owner of 开源框架/协议 qnx 迁移模块 |

---

## 8. 待解析人员表（open_id → 姓名）

所有出现过的 owner open_id 去重，按出现频率排序。建议落 data-luna6 前通过通讯录（contact API）或飞书 wiki `SwnPwWOpuiqnyikY5XOcgVHxnyf`（Luna6 各项目软件领域对接人）批量解析为姓名后再回填运行时数据库；本文件只保留 open_id 即可，姓名由后端 API 运行时解析。

```text
ou_b0ec727bdd0ea2fc9d7ffce5245a1737   # 性能专项 owner
ou_c4433a950aebfa7ebcdd13620ee6aecb   # 开发环境 lead
ou_f62bc6e6034dfba1e82eef562bb75e6c
ou_f12c0a626727a06bc906a7da9022396d
ou_8328f796183de2c6872d9849090fd96c
ou_f3ea63f9f05ea0e0730692e1be3269e6
ou_e4814d969b5108b8f11893107daa27ce   # Ut owner
ou_c7bf1dca0d400e9fe9b2539a20cbf400   # PDT lead / qnx 迁移
ou_f90be8f1191e284ecf437a87e3464092   # ROS2 / Gateway / DVR
ou_6513ec393c67947adf468ffe71ac4e2c   # ROS2 适配 / DVR
ou_87ece67c54c636362c4020ff0040592b   # 基础服务 / MMC / ECarx KX21
ou_2a65626de9196c1ff374c71dc81a94f0   # 基础服务
ou_cfa2107ad7b43c2f4fa578d3e8772bca   # 基础服务 - 主线 / AY7
ou_34be37dee83dfbc452d03a8b13fff9b7   # 基础服务 - BTET
ou_658540583f0083b8f2d15314bbcf4348   # 基础服务 - ZS32 一体机/小域控
ou_d876d1bca4aeb42d1d13f9a08146ab11   # 基础服务 - FT
ou_4d93967a8fe4b987011a4c023d948ef1   # 数据工具 / 数采 / 数据回传
ou_6caaa36a550febdc00758ef45ebc33b8   # AY7 HDE
ou_c40504df5ee4683e43c2ed31e5a406ff   # AY7 HDE / ZS32 小域控
ou_6a019448419b24a3cc3751ede1d89a36   # 数据回传 / 数采
ou_38e3ae26c22830f586bcb2643c4c40b3   # ZS32 一体机 HDE
ou_43a6d27bd8d7a5a426a7d8380bba99ac   # 模型推理
ou_ed4ae550cfc4019866253c443789496f   # 模型推理
ou_201c2467a7df5abc9479e3ab76dd8431   # 模型推理 - KX21 联调
ou_f9620d8c753df409e3068ddd0e8d26f9   # 全栈规控 AY7/ZS32 / 回灌
ou_43dce79f6e7971b1507f42ad74c73773   # 全栈规控 FT
ou_ee5b2fa0e6fc5e60362376fa07abeea2   # 全栈规控 MMC / 主线/泊车集成 / 泊车感知
ou_20868fffe17b4eab496fc12a16719835   # 全栈规控
ou_b1ee4d42208d99f1db8142a8c983ca0d   # 全栈规控 BTET / 感知集成
ou_8c952c6e8406342121b7bb5e6a615628   # 全栈规控 MMC
ou_d021a8b922e51bc09a5b5ca69a319557   # 自动化能效专项
ou_2d8560390427c2012f48d06af63901da   # 自动化能效专项
ou_9d343f69514709805d17341af8640d53   # 感知集成
ou_51d8d0fd13abbd9cf6673553bb3abc63   # 主线集成
ou_9f233ef7fbf2dd598cd5187eba0596e1   # 主线集成 / HMI/HDE
ou_0b0aafc13279faa9245e803bcd2a3b02   # 主线集成
ou_41b9f6003c87efa1ef943a0bd9284511   # HMI/HDE
ou_626d8eaf98cbfb6add0474ac1eb14723   # 软件底座 A 核 lead
ou_84ddecb7a8befdc338a99147c12e96de   # A 核 - FT-KX21
ou_0b43891f8f9841c4cc6183cb9740c62e   # A 核 - BTET
ou_abf27289e9906edb0404a7943160dbc8   # A 核 - ZS32
ou_b645ce9f87dbc0a53b3271a188443140   # A 核 - ZS32 小域控
ou_e4e35914e61b024dc482111de5217064   # A 核 - MMC
ou_e95e84006454dea6d717499ed55d8bf3   # MCU lead / MCU-AY7
ou_d219b269c7c29cef281b39b27fb5e78d   # MCU - BYD / ZS32
ou_2cbd4663d3dc282bee2069740e643964   # MCU - BYD
ou_6b940c7d25feee08901eb2ae63731a0e   # MCU - BTET
ou_17d49a8c66ea62ac5812f187bd4ec3ae   # MCU - ZS32
ou_996338561a87def0ced6d52281f03da8   # MCU - FT/自研小域控
ou_54e40be083adb2771715aabe2b981163   # MCU - FT/自研小域控 / ZS32 小域控
ou_7f23e55a47499e83119f3fa68a6b52e0   # MCU - MMC
ou_2ed77a441c1cf8ce502e205c3aee7220   # 数采专项
ou_e6d3b8112f03ce5859fc5c1b1c80c5b5   # 标定
ou_a9085a40fbafbe2957ed1bdcee2d3705   # 回灌
ou_5585cc420bde9bdf016f8367fb20bac0   # 人力/非人力资源
ou_8bc92da4f244cd1ca0b2ecf1d6a1810d   # 基础服务 MMC 差分刷写（待确认归属）
```

共 53 个 open_id 待解析。

---

## 9. 关联资源链接

| 类型 | 名称 | token |
|---|---|---|
| wiki | 001 白云山 AY7 客户需求 | `CJyCwaMytiLFG0khk4Ac25CPndd` |
| wiki | Luna6B 系统架构总体设计_AY7_V1.0-WIP | `IiYzw5UJdiqloMkDnh8c9hTDnJd` |
| wiki | Luna6 各项目软件领域对接人（owner 解析源） | `SwnPwWOpuiqnyikY5XOcgVHxnyf` |
| wiki | AY7 交付功能清单 V0.5_0917 | `QqpiwifZli9OwQkjhsxcIEiwnTh` |
| wiki | HC-IPD-P01-W06 PDT 运作管理规范 | `PN0HwmobwiSLKNkKq1Ycmga6nlc` |
| wiki | QNX Trace 分析工具 | `HXpcwyS4XiEVvuk3xvZc0VGtn5e` |
| wiki | 回灌 - mcap 素材 migration 转换 | `Nof4wJ8Q0iQug5k5IwbcioBonFe` |
| wiki | model_inference MISRA 和 CERT 问题分析 | `RvVUwGaZ8iF3gQkXBRZcDm2Cn5d` |
| wiki | [TSR/TLR] Luna-V3.0 | `TW82wUysbi7TW4k15ENcsMp7ngh` |
| wiki | 空气悬架功能模型输入输出一致性比较 | `WvMnwT9nFir923kkdkocD9Omnjb` |
| wiki | Luna ltc 改制车标定软件版本需求 | `F3P1wA3vbimErxk6natcM86sn8x` |
| wiki | CR 评审材料 pnc 回灌剥离 | `RzX1wb7xiiG0czkKlP4csQ7vnVh` |
| bitable | 待办（5/20） | `SGC0bLnJIa4K0Ps7B65cn2WMnZg_tblAXlO1mPUzFyku` |
| bitable | 待办（5/13） | `TGnbb6IqqaEKn7sCGQacvVocnwb_tblb4phDB1t7DzAv` |
| whiteboard | 人员阵型（5/20） | `SBGjwlHobhcL0wblTsccDoQenkb` |
| whiteboard | 人员阵型（5/13） | `JnB6w18tLhLldHbeYeVciwQwnRe` |
| whiteboard | 产品线核心团队 | `WDOKwyen6hN3YCb3Sy2cJSGjnZf` |
| whiteboard | 运作机制 | `S1klwu9lfhxbQebR3bncAnJnnmc` |
| sheet | 会议地图 | `J1sdsgIb5hy81QtfgTjcoUNxnpb_PdcLan` |
| docx | ReleaseNote Luna6_LC-V9.0.0-WL19-20260511 | `KDtJdFVJPoCn8Dxcx3qcwZlGnnd` |
| wiki | ReleaseNote Luna6_LC-Develop-20260509_79 | `AhdzwEshxiP8uXkYx2kc7V2CnpA` |

---

## 10. 回填指引

未来落 `data-luna6` 分支时按下表 1:1 翻译：

| 本文件节 | 目标 JSON 文件 | 翻译规则 |
|---|---|---|
| 2 PDT | `design/pdt.json` | 整段对象转 JSON，updated_at 用回填当日时间戳 |
| 3 里程碑 | `design/pdt.json::milestones[]` | yaml 列表转 JSON 数组 |
| 5 LTC 清单 | `design/ltcs.json` | 数组，order 保留；created_at/updated_at 用回填当日 |
| 6 模块（scope:pdt 类） | `design/modules.json` | 直接对象，1 个模块 1 条记录 |
| 6 模块（scope:ltc 类，id_pattern 写明的） | `design/modules.json` | 对每个 ltc_breakdown 项展开成 1 条 `modules` 记录，`id` 套用 id_pattern，`ltc_id` 填 ltc 字段，`owner_open_id` 取该 ltc 行 owner，`sub_items` 取该模块通用 sub_items |
| 6 status_hint / 6 risk_note | `design/module_status.json` | status_hint → module_color；risk_note → risk_note；kpi_values 暂留空；不为 green 的模块必须填 risk_note（已遵循）|
| 6 weekly_progress / monthly_goal | `module_status.json::metadata` 或 `module_updates.jsonl` 初始事件 | 建议作为首条 status_update 写入 jsonl 历史，而非塞进 module_status 主表 |
| 4 运作机制 / 7 PDT lead / 9 关联资源 | （不入运行时数据） | 仅参考，供 PDT 例会节奏对齐与 owner 名字解析 |
| 8 open_id 表 | 运行时通讯录解析 | 不入 JSON；后端 `/api/contact/resolve` 动态解析 |

### 落 data-luna6 流程（待执行，本轮不做）

```bash
# 1. 切数据分支
git checkout --orphan data-luna6   # 或基于现有空模板分支
git rm -rf .
mkdir -p design

# 2. 按本文件第 2/3/5/6 节写 4 个 JSON
$EDITOR design/{pdt,ltcs,modules,module_status}.json

# 3. 校验
python3 ../project_manage_dashboard/design/validate_data_files.py

# 4. 推送
git add design/
git commit -m "seed: Luna 6 PDT 初始数据（来自 wiki 2026-05-22 抓取）"
git push -u origin data-luna6

# 5. 在部署机挂 worktree 跑实例
git worktree add /srv/pmd-instances/luna6 data-luna6
DATA_DIR=/srv/pmd-instances/luna6/design ./app/backend/start-instance.sh
```

### 落数据前需澄清的悬挂问题

1. PDT 里程碑日期：26Q2 没有具体日，按 2026-06-30 兜底，是否替换？
2. `ou_8bc92da4f244cd1ca0b2ecf1d6a1810d`（MMC 差分刷写）归属模块未明确，待问 owner
3. 多 owner 时 `owner_open_id` 只能填一个还是允许数组？当前 schema 是单值，多 owner 时取第一个，其余写 `metadata.extra_owners`
4. 标定 / 回灌的「已删除线月度目标」是否需要保留作为「已完成」展示？当前以 `[done]` 标注
5. zp22 / ecarx-kx21 / byd 三个 LTC 周报多数为空，是否需要在 modules.json 里也保留空记录占位？建议保留以便 owner 后续填报

---

## 11. 第二轮扩展抓取（2026-05-22 追加）

第二轮从第 9 节链接中抓取了 6 份资源，新增/补充信息归入 11~16 节。

### 11.1 抓取结果汇总

| Wiki / Bitable | docx/obj_token | dump 路径 | 状态 | 价值 |
|---|---|---|---|---|
| `SwnPwWOpuiqnyikY5XOcgVHxnyf` 项目集软件阵型 | `VJ3NdQAxqo2txPxqN4bc3xafn4f` | `/tmp/luna6_doc4.md` | 成功 | 17 个 open_id → 姓名解析；硬件形态总览；运作要点 |
| `PN0HwmobwiSLKNkKq1Ycmga6nlc` PDT 运作管理规范 | — | — | **权限拒绝** | user/bot 均无权限，需联系所有者授权 |
| `CJyCwaMytiLFG0khk4Ac25CPndd` AY7 客户需求 | `NNW5dVzi8oXBMex4xuHcRcZTnME` | `/tmp/luna6_doc6.md` | 成功 | 49×13 大表，AY7 功能清单；10 个未关联 open_id 的负责人姓名 |
| `QqpiwifZli9OwQkjhsxcIEiwnTh` AY7 交付功能清单（实为 V1.0_1029） | `MaDssXPL2hACtyt5vXycPpqMnpe` | `/tmp/luna6_doc7.md` | 成功 | **13 个版本里程碑** + 4 大功能模块层级 + owner |
| `IiYzw5UJdiqloMkDnh8c9hTDnJd` Luna6B 系统架构（实为 V1.4） | `OvBxdXVcmoFwS1x1uDkc7V7Unoh` | `/tmp/luna6_doc8.md` | 成功 | 19541 行；8 功能模块 + 14 平台模块 + Safety 三层 |
| `SGC0bLnJIa4K0Ps7B65cn2WMnZg/tblAXlO1mPUzFyku` 5/20 待办 | — | `/tmp/luna6_doc9.md` | 空表 | 仅 1 条 null 记录，5 字段（任务/负责人/DDL/进展/状态）；无模块归属字段，**不引入看板** |

### 11.2 待补抓取（下一轮）

- `FWmGwVJITiGyVlkESjbclFg2n6n` — 20260312 研发领域主线及交付项目接口人（补齐剩余 36 个 open_id 姓名）
- whiteboard: `IqCrw8ps3hrNUnbLhu2c1oSvnHg`（软件阵型）/ `C54JwcA6thFXj0bQYd8cBOMNnvc`（主线阵型）/ `Z4cVwrcA6hMyaMbu5T8cP3MTnvb`（SE 阵型）— 通过 lark-whiteboard skill
- `PN0HwmobwiSLKNkKq1Ycmga6nlc` — 申请权限后重抓
- AY7 系统架构子文档（感知/预测/行车规控/主动安全规控/泊车规控）— 在 luna6_doc8 内有 mention-doc token，按需求深入再抓
- `C43QwbZLaifOnQkFVlhcjsJFnUe` 复制项目-需求管理 CB 策略
- `Gznyw4Lo7iMLRFksO6YcT9XsnUf` 项目集版本计划

---

## 12. 人员表（已解析 17 人 + 待解析）

### 12.1 已解析 open_id → 姓名 → 角色

来源：`SwnPwWOpuiqnyikY5XOcgVHxnyf` + `lark-cli contact +get-user`。

| open_id | 姓名 | 主要角色（verbatim） |
|---|---|---|
| `ou_b1ee4d42208d99f1db8142a8c983ca0d` | **安竞轲** | BTET 集成/版本经理；ZS32 小域控集成；感知集成 |
| `ou_ee5b2fa0e6fc5e60362376fa07abeea2` | **袁宾** | MMC 集成/版本经理；主线/泊车集成；泊车感知 |
| `ou_f9620d8c753df409e3068ddd0e8d26f9` | **杨云航** | ZS32 一体机集成；全栈规控 AY7/ZS32；回灌 |
| `ou_43dce79f6e7971b1507f42ad74c73773` | **石建** | 吉利 KX21 集成；全栈规控 FT |
| `ou_acd1671d174190470576b4bb93bdcaa2` | **冯智** | AY7/吉利 KX21 研发开发进展版本经理（项目集软件阵型文档 Owner） |
| `ou_f35203920af972de99683e6c7b173e67` | **薛文昊** | BTET 956D/957D 研发开发进展版本经理 |
| `ou_8c192eb2fbca173dfabe24f4f6c832c2` | **熊梦荣** | BTET SR/功能 SE |
| `ou_992689dbee0de693ec62cea13bd018e3` | **夏斌** | BTET 软件 SE |
| `ou_c682883e32f02cd54bf1a0ea528d19de` | **黄治伟** | MMC SR |
| `ou_daa708debfbe3e67f0d47a97120cc6cf` | **耿世林** | MMC 集成；MMC RVR 研发开发进展版本经理 |
| `ou_c7f60c76681cb13473fa92e1802223c4` | **常志超** | ZS32 一体机 SR；ZS32 小域控 / ZP22 SR |
| `ou_319bc65ed7710a121b1ef1a5a1a662d5` | **海江涛** | ZS32 一体机集成；ZS32 PHEV 研发开发进展版本经理 |
| `ou_58663aa5033c353bd78ab9d470702ab7` | **颜意林** | 吉利 KX21 SR:功能 |
| `ou_d28db185d06a73d4e00e9a7daf9358aa` | **何坤** | 吉利 KX21 系统 SR |
| `ou_f891d532ef752b2d47a13691954b3ef2` | **宋超** | ZS32 小域控集成 |
| `ou_60e33496f8f78b082dbec6a51568a9b8` | **张冠英** | 功能/法规要求接口人 |
| `ou_8c8f69bf16fec46cc4e5adb7ad0eb7b6` | **徐宁** | 信息安全需求 SE（AY7 信息安全） |

### 12.2 AY7 文档中出现的姓名（open_id 未关联，需后续映射）

来源：`QqpiwifZli9OwQkjhsxcIEiwnTh` AY7 交付功能清单 + `CJyCwaMytiLFG0khk4Ac25CPndd` AY7 客户需求。

| 姓名 | 角色（AY7 上下文） |
|---|---|
| **方维才** | 行车功能 / 人机交互（AY7 HCT 责任人 = `ou_3ac6dabdb5a84612384e4be3e8f574fe`） |
| **刘琨** | 数据回传 |
| **方云蒙** | DVR 推流 / 产线测试 / 时间同步 / 日志服务 / 存储 |
| **程昊天** | OTA / 通讯 / 电源管理 / 温度管理 / 整车配置字 |
| **朱志玲** | 传感器 |
| **王凌霄** | 标定 |
| **陈亦真** | 诊断 / 电源管理 / 温度管理 / 整车配置字 |
| **任少波** | 数采 / PAC 回灌 |
| **荣芩** | 功能安全 / 预期功能安全 |

### 12.3 第一轮 53 个 open_id 解析进度

已解析 16 个（第 12.1 节中扣除徐宁因徐宁出现在第一轮性能模块中 `ou_b0ec727bdd0ea2fc9d7ffce5245a1737` 与第二轮的 `ou_8c8f69bf16fec46cc4e5adb7ad0eb7b6` 是同名不同人/或同人不同账户，**待核**）。剩余 ~37 个待通过下一轮抓 `FWmGwVJITiGyVlkESjbclFg2n6n` 或直接调通讯录解析。

---

## 13. AY7 完整版本里程碑（取代第 3 节兜底日期）

来源：`QqpiwifZli9OwQkjhsxcIEiwnTh` 交付功能清单 V1.0_1029，sheet `67ef7e` 第 1-6 行。

```yaml
# 用于 pdt.json::milestones[]（如选「3 节战略目标 + AY7 节点」组合）
# 或单独作为 modules[ltc-ay7-*].metadata.version_plan

- name: PT0 S.D00 Bring-Up
  date: 2025-09-19
  type: version
  metadata: { knowing_version: G010v1, hct_version: V0.0.1 }

- name: PT0 S.E00 PT1-1 装车 / preDV
  date: 2025-09-26
  type: version
  metadata: { knowing_version: G010v2, hct_version: V1.0.0 }

- name: PT0 S.F00 PT1-2 装车 / 行泊车可激活
  date: 2025-10-15
  type: version
  metadata: { knowing_version: G020v1, hct_version: V1.1.0 }

- name: PT1-1 S.F01 功能迭代
  date: 2025-10-30
  type: version
  metadata: { knowing_version: G020v2, hct_version: V2.0.0 }

- name: PT1-2-1 S.F02 内部测试 & 外部联调（全功能）
  date: 2025-11-15
  type: version
  metadata: { knowing_version: G020v3, hct_version: V3.0.0 }

- name: PT1-2 S.F03 首版性能软件（PT2 装车，性能 60%）
  date: 2025-11-30
  type: version
  metadata: { knowing_version: G030v1, hct_version: V4.0.0 }

- name: PT1-2 S.F04 性能迭代（性能 80%）
  date: 2025-12-30
  type: version
  metadata: { knowing_version: G040v1, hct_version: V5.0.0 }

- name: PT2 S.F05 性能优化（性能 100%）
  date: 2026-01-30
  type: version
  metadata: { knowing_version: G050v1, hct_version: V5.1.0 }

- name: PT2 S.F06 Pre-SOP（性能 100%）
  date: 2026-02-28
  type: TR
  metadata: { knowing_version: G060v1, hct_version: V5.2.0 }

- name: PT2 S.000 软件冻结 / SOP
  date: 2026-03-07
  type: SOP
  metadata: { knowing_version: G070v1, hct_version: V6.0.0 }

- name: OTA1 S.001
  date: 2026-05-07
  type: OTA
  metadata: { knowing_version: G080v1 }

- name: OTA2 S.002
  date: 2026-07-07
  type: OTA
  metadata: { knowing_version: G090v1 }

- name: OTA3 S.003
  date: 2026-09-07
  type: OTA
  metadata: { knowing_version: G100v1 }
```

**SOP 起点确认为 2026-03-07**（与 PDT 战略目标"26 年 Q2 前量产"对齐）。

---

## 14. AY7 功能层级（modules.json 校验/扩展依据）

来源：AY7 交付功能清单 V1.0_1029。可作为 `ltc-ay7-*` 各模块的 `sub_items` 种子，或独立作为 AY7 LTC 下的 `vehicle_functions.json` 扩展数据。

```yaml
01_VehicleFunctions:
  01-01_行车功能:
    owner: 方维才
    01-01-01_主动安全辅助: [AEB, FCW, LDW, LDP, TSR, IHBC, AES, ESA, RCTA_RCTB]
    01-01-02_巡航辅助: [ACC, ICA]
    01-01-03_行车NOA类: []
    # 已删除/灰: ELKA / BSD / DOW / RCW
  01-02_泊车功能:
    owner: 知行（外部）
    items: [FAPA 融合泊车辅助, RPA 遥控泊车, CPA 指尖泊车, RAEB 后向主动紧急制动]
  01-03_人机交互:
    owner: 方维才

02_Software:
  02-01_App:
    02-01-01_数据回传: { owner: 刘琨 }
    02-01-02_DVR推流: { owner: 方云蒙 }
    02-01-04_产线测试软件: { owner: 方云蒙 }
  02-02_Bashtech:
    02-02-01_OTA: { owner: 程昊天, sub: [Recovery] }
    02-02-02_时间同步: { owner: 方云蒙 }
    02-02-03_日志服务: { owner: 方云蒙 }
    02-02-04_通讯: { owner: 程昊天 }
    02-02-05_传感器: { owner: 朱志玲 }
    02-02-06_标定: { owner: 王凌霄 }
    02-02-07_诊断: { owner: 陈亦真, sub: [诊断事件] }
    02-02-08_存储: { owner: 方云蒙 }
    02-02-12_电源管理: { owner: 陈亦真, sub: [安全下电, 低功耗] }
    02-02-13_温度管理: { owner: 陈亦真 }
    02-02-14_整车配置字: { owner: 陈亦真 }

03_Safety:
  03-00_功能安全: { owner: 荣芩 }
  03-01_信息安全: { owner: 徐宁 }
  03-01_预期功能安全: { owner: 荣芩 }   # 注：原表两个 03-01 编号冲突，按原文保留

04_Others:
  04-01_数采功能:
    owner: 任少波
    04-01-01_ID4_主线车: {}
    04-01-02_AY7_交付车: {}
  04-02_回灌仿真:
    04-02-01_PAC卡: { owner: 任少波 }
    04-02-02_小域控: {}
    04-02-03_x86: {}
  04-03_台架长稳: {}
  04-04_领域基建: {}
```

**与 modules.json 的关系**：本结构粒度比 modules.json 细一层。建议作为 **AY7 LTC 私有功能清单** 单独存放（如 `design/ay7_features.json`，未来扩展 schema 时再纳入），不冲击 modules.json 当前的 16 模块设计。

---

## 15. Luna6B 系统架构 — 用于校验 modules.json 颗粒度

来源：`IiYzw5UJdiqloMkDnh8c9hTDnJd` Luna6B_系统架构总体设计_AY7_V1.4。

### 15.1 功能架构层（8 大功能模块）

```yaml
- Perception     # 感知系统
- Prediction     # 预测
- Driving        # 行车规控
- ActiveSafety   # 主动安全规控
- Parking        # 泊车规控
- StateMachine   # 状态机（行泊切换 / 行车 / 泊车 / ADAS）
- HMI
- Calibration    # 标定（EOL / 售后 / 背景）
```

### 15.2 软件平台/基础架构层（14 模块）

```yaml
- SensorLogicArch   # Camera/Radar/USS/DVR
- TimeSync          # 含曝光同步
- SystemState       # 含哨兵模式
- Log
- Storage           # 含分区
- Diagnosis         # 外设/功能应用/软件应用/外部状态/系统环境/通讯
- OTA               # 刷写及升级（Recovery 变砖恢复）
- PowerManagement
- ThermalManagement # 结温/SOC 板温/MCU 板温
- Communication     # IPC / ROS2 / RTE / CAN / ETH(SOMEIP/DoIP)
- ConfigField       # 配置字管理
- DVSoftware        # DV 软件需求及架构设计
- CalibrationSW     # 标定（软件侧）
- VersionManagement
```

### 15.3 Safety 三层

```yaml
- Level1_FunctionLayer: [SensorSubsys, SensorProcess, Perception, Calibration, PlanControl, VehicleControl]
- Level2_FunctionMonitor: []
- Level3_ControllerMonitor: [ROM/RAM Check, MemoryIsolation, ProgramFlowMonitor, ProcessorFaultDetection, CommCheck, HardwareModuleMonitor]
- SafetyStateMachine
```

### 15.4 部署边界（不是模块边界）

- **R 核 (MCU)**：实时安全 / 状态机 / 诊断 / 通讯
- **A 核 (SOC)**：存储 / log / 上层应用 / HMI / 外部通讯
- **核间通讯**：IPCF（多核异构）+ ROS2（A 核进程间）+ RTE
- **结论**：modules.json 中「软件底座-A 核」「软件底座-MCU」**不是功能模块**而是部署平面。同一功能（如「诊断」「通讯」「电源管理」）会同时在 R 核与 A 核实现。

### 15.5 对 modules.json 的影响评估

| 现 modules.json | 系统架构对应 | 评估 |
|---|---|---|
| 性能专项 / Ut / 数采专项 / 标定 / 回灌 | 工具链类，架构图未覆盖 | 保留，是 PDT 横向 |
| qnx 迁移 / 基础服务迁移 / 数据工具迁移 | 平台层 Communication / OTA / Sensor 等的迁移视图 | 保留，"迁移"是阶段性专项 |
| 模型推理 / 感知集成 / 主线-泊车集成 | Perception / Prediction / Driving / Parking 的实现侧 | 保留 |
| 全栈规控集成 | Driving + ActiveSafety + Parking 的版本集成 | 保留 |
| 软件底座-A 核 / 软件底座-MCU | 跨多个平台层模块的部署聚合 | **建议保留但备注**：这是部署视角，跨 14 平台模块 |
| **缺失**：StateMachine、HMI（独立模块）、TimeSync、PowerMgmt、ThermalMgmt、Diagnosis、Storage、ConfigField、SafetyMonitor、Information Security | — | 这些功能在 AY7 文档中有独立 owner（程昊天/陈亦真/方维才/徐宁/荣芩），但当前 modules.json 未单列。**取舍**：周报视角下它们被吸进「基础服务迁移」「软件底座」；产品视角下应单列。建议未来按"功能模块视图"重构 modules.json 时引入 |

---

## 16. 硬件形态总览（LTC metadata 扩展依据）

来源：`SwnPwWOpuiqnyikY5XOcgVHxnyf` 项目集软件阵型。

| LTC | Tier1 | OEM | 车型 | 配置 | 模组 | 量产地 | 法规 |
|---|---|---|---|---|---|---|---|
| 主线 ID4 | 小域控 A | 知行 | 大众 ID4 | — | — | — | — |
| AY7（白云山） | 小域控 A | 知行 | 广汽 紧凑 SUV | 5V1R | X8D+817 | 中国 | — |
| ZS32 PHEV 一体机 C | 联创 / aumovio | 上汽 | BZ5 956D & BZ3 957D | 1V3R+1V1R | 1V1R | — | — |
| BTET 一体机 A | 大陆 / 联创 | 上汽 MG ZS | 1V2R | — | — | 欧/UK/AUS/南非/以色列/HK/土耳其/墨西哥/中东/南美/新马 | ENCAP 2027 四星 |
| MMC 一体机 A | 大陆 | 三菱 | RVR | 1V | — | 北美 | ENCAP2016+UN R48+FMVSS108 |
| 吉利 KX21 小域控 B | FT | 吉利 | — | 5V3R | — | 中国 | — |
| ZS32 小域控 C | minieye | 上汽 | — | — | — | — | — |

潜在 AY7 同平台未定点 LTC：AY3 / T51 / T75 / T68 / T09。

预算规则：AY7 和 ZS32 走 LUNA6 PDT，其他独立预算；资产类（单价>1 万走 ECR）都走 PDT。

---

## 17. 二轮抓取新增的悬挂问题

6. **PDT 运作管理规范无权限**：当前账号 sbeal@leomail.tamuc.edu / 冯智账号对 wiki `PN0HwmobwiSLKNkKq1Ycmga6nlc` 无读权限。是否申请加入该知识库？
7. **AY7 真实版本** 是 V1.0_1029（文档名）而非第 1 节记录的 V0.5_0917。第 9 节关联资源表已用旧名，是否更名？
8. **5/20 待办 bitable 空表**：当前不引入看板。等团队真用起来并补"所属模块"字段后再评估。
9. **AY7 详细模块（第 14 节）与 modules.json 是否合并**：当前 modules.json 是 PDT 周报视角，AY7 详细模块是产品功能视角。建议作为 LTC 私有功能清单分开存放。
10. **17 个 open_id 名字解析后**，是否在 modules.json 落地时也写一份缓存到 `design/contact_cache.json`（参考 oversea_projects 命名）减少运行时调用？
11. **徐宁是同一人吗**：`ou_b0ec727bdd0ea2fc9d7ffce5245a1737`（性能专项 owner，第 1 轮）与 `ou_8c8f69bf16fec46cc4e5adb7ad0eb7b6`（信息安全 SE，第 2 轮）— 两个 open_id 不同但都被引用为"徐宁"。需通讯录核对（不同 tenant？或同名不同人）。
