# 附录：外贸智能报价平台实战手册（蓝图原型机）

平台：https://trade-quote.app.workbuddy.host/ （appId wbapp_1nhaHWNh4YSSZxh3iV8Plq，复用此 id 发布保域名）
业务闭环：客户询价单（BOQ）→ AI 解析建档 → 复核确认 → 分类派单 → 供应商在线报价 → 比价定标 → 客户报价单 → 履约跟踪 → 48h 首答报告。旁路：合同 AI 审核、价格基准、物流询价比价。

## 数据模型实例（7+1 表）

- `quote_tasks`：file_name/project/category(可为「混合品类」)/currency/priority/item_count/status(pending_review→confirmed→rfq_sent→awarded→completed)/file_path/image_paths[]/assignee_name/owner_id
- `quote_items`：task_id + item_ref/description/description_cn/category(逐条)/specs/qty/unit/sort_order
- `suppliers`：name/categories[]/certs[]/region/avg_response_days/rating/**contact（=登录邮箱，门户绑定关键）**
- `supplier_users`：user_id/supplier_id/email（登录后按邮箱自动绑定写行）
- `supplier_quotes`：task_id+supplier_id+item_id 唯一约束，unit_price/lead_days/remark，upsert
- `task_logs`：审计与状态机之源（SELECT+INSERT only）
- `price_history`：历史报价底座（719 行/32 品类，品名中英/规格/单价/币种/贸易术语/供应商/日期/来源文件；全员读、写入限 owner）

## 关键业务套路

- **品类是派单的枢轴**：quote_items 逐条品类 ↔ suppliers.categories 中文名对齐；新增品类必须同步补供应商品类，否则匹配失序。
- **派单排序**：品类匹配优先，再按评分；多选派单；已在派的默认勾选跳过。
- **比价视图**：行内最低价绿色高亮、报价覆盖率警示（<95% 总价失真）、可信度 A/B/C（规则 25/29/34 指纹）、实战锚点偏离 ±10% 标红、**同源报价检测（规则 14：两两单价一致率 ≥70% 亮红牌）**。
- **定标复算**：总价 = Σ(单价×数量) 按行重算，验收时与手算对到分。
- **预算参考**：AI 估算 FOB 区间必须标注"非实时行情"；price_history 沉淀后逐步替换为真实锚点。
- **HS 编码**：HS_LIB 23 品类内嵌（boq-smart-audit 资产），明细行自动挂候选码徽章 + 危险品⚠。
- **文件归档**：原文件 `shared/<uid>/boq/`（团队共享可读）、参考图 `shared/<uid>/boq-img/`（含 JSZip 抽取的 Excel 内嵌图），下载走 createSignedUrl(s)。

## 三角色视角

| 角色 | 入口 | 能做什么 |
|---|---|---|
| 管理员 | 密码/验证码登录 | 全部功能 + 账号审批页签（批准供应商自动建档） |
| 员工 | 同上 | 建任务/复核/派单/比价/定标/履约/合同审核 |
| 供应商 | 注册→申请→批准→登录 | 只看派给自己的任务、在线报价（只看到自己的报价） |

## 已验收清单（2026-10-04/05 全链路自动化验收）

登录双通道、三角色页面权限、申请审批流、派单/报价/比价/定标全链路（金额复算一致）、履约里程碑、EN 切换、合同审查（2.5 分钟 12 项风险，抓住故意埋的价格陷阱）、真实邮箱 E2E（Agent Mail OTP 握手）。
P 级问题与修复记录见 precision-test/平台验收报告-2026-10-04.md。

## 解析链路依赖

BOQ 解析/校验/比价的领域知识全在 `boq-smart-audit` 技能（规则库 22 条 + 缩写词表 + 格式目录 + 平台坑位清单），两技能互为上下游：本技能管"平台怎么跑"，它管"单子怎么算对"。
