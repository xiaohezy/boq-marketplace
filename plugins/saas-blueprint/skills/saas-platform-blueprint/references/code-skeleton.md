# 关键代码骨架（可直接改写复用）

## ① 登录页：验证码 + 密码 + 注册 + 忘记密码 四表单

```html
<div class="auth-tabs">
  <button id="tabLoginOtp" class="active">验证码登录</button>
  <button id="tabLoginPw">密码登录</button>
  <button id="tabSignup">注册</button>
</div>
<!-- formLoginOtp: #loEmail #loCode #loSend(发送,60s冷却) #loBtn -->
<!-- formLoginPw:  #lpEmail #lpPass #lpBtn #goForgot -->
<!-- formSignup:   #suEmail #suCode #suSend #suPass(设密码) #suBtn -->
<!-- formForgot:   #fpEmail #fpCode #fpSend #fpPass #fpBtn -->
```

骨架逻辑：
- OTP 发送后按钮冷却 60s；**只认最新一条码**（报错文案里告诉用户）。
- 注册 = 验证码校验 + 设密码，一次完成；之后全部密码登录（自动化验收/诊断免 OTP）。
- 登录后第一跳不是主页，是**角色判定**（见②）。

## ② 角色判定与申请审批（gate 流）

```js
async function checkAccount() {
  const people = foldAccountLogs(await fetchAccountLogs()); // 日志状态机折叠
  const me = session.user.email, mine = people[me];
  if (mine && mine.status === "active") {
    if (mine.role === "supplier") {
      const sup = await findSupplierByContact(me);          // 档案表 contact=email
      if (sup) { enterSupplierMode(sup); return "supplier"; }
      return gate("供应商身份待绑定", "请联系管理员把供应商「联系方式」改为：" + me);
    }
    showStaff(); return "staff";                            // admin 额外见账号审批页签
  }
  if (mine && mine.status === "pending") return gate("申请已提交，等待审批");
  return renderOnboarding();                                 // 选类型(员工/供应商)+公司名 → 写「账号申请」日志
}
// 管理员批准：acctApprove(email, role, company)
//   写「账号批准」日志；role=supplier 时 suppliers 查无 contact 则自动建档
```

## ③ 审计留痕

```js
async function writeLog(taskId, action, detail) {
  await cloud.database.from("task_logs").insert({
    task_id: taskId, action, detail: typeof detail === "string" ? detail : JSON.stringify(detail),
    owner_name: session.user.email || ""
  });
}
// 状态机全靠它：AI解析建档 → 复核通过 → 已派单 → 选定中标 → 首答交付 → 履约里程碑
// 页面状态（在派集合/中标者/里程碑完成度）= 按时间重放日志折叠，不冗余存状态字段
```

## ④ AI 解析链路（LLM 接入套路）

- `response_format:{type:'json_object'}` + 流式累积 + **剥围栏容错**（实测 1/160 概率带 ``` 围栏）。
- 大输入分批（≤200 行/批）→ 逐批校验（条数 + id 集合双重）→ 增量写缓存 → 全部通过才写库。
- 客户端先预过滤噪声行再送模型；单元格截 80 字、列宽按表宽自适应（≤26 列）。
- 多模型下拉**按 id 去歧**（同名模型 hy3/hy3-x 实测坑）。
- 视觉通道：扫描件/图片走 `image_url` base64 多模态消息，PDF 先渲 150dpi 页图。
- 解析结果先**体检**（重复描述/数量缺失/单位缺失/REF 重复/整百数量指纹）再入库。

## ⑤ 通用小组件

```js
const esc = s => String(s == null ? "" : s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
function toast(msg, type) { /* 3s 自动消失，ok/err 两色 */ }
function errMsg(e) { /* 英文报错 → 中文可操作文案映射表，兜底 e.message */ }
// 弹窗：modal-mask 全屏遮罩 + 点遮罩关闭 + close-x；body 由异步数据渲染，操作后 refresh 局部刷新
```

## ⑥ 批量数据资产化管线（历史数据 → 底座表）

平台上线后常需要把历史文件（报价单/台账/合同）灌成数据资产。实测管线（230 文件 → 719 行入库）：

```
① 全文提取（python: openpyxl/xlrd/pymupdf/python-docx → 每文件一个 txt，幂等跳过已提取）
② LLM 逐文件结构化（json_object 流式 + 剥围栏；只提取目标字段，无价格/无内容输出空）
③ 每文件缓存 json（断点续跑、失败重跑零成本）
④ 3 并发 + 失败重试 1 次
⑤ 写库前冒烟：手工插 1 条验证 RLS/GRANT 通路，再放量
⑥ 50 条/批 insert；全成功后写 _inserted.flag 防重复入库
⑦ 产出按维度统计报告（品类/来源/质量完整率）
```

- 扫描件/图片走视觉通道（image_url base64，PDF 先渲 150dpi 页图）。
- 底座表设计：来源文件/来源目录字段必备（可回溯、可按源清理）；标注"历史数据，非实时行情"。

## ⑦ Node 端服务端脚本骨架（诊断/修复/批量入库）

```js
// 在 Node 里跑浏览器 SDK：window/localStorage 垫片 + eval SDK 全局包 + fetch 注入 Origin/UA
globalThis.window = globalThis;
globalThis.localStorage = { _s:{}, getItem(k){...}, setItem(k,v){...}, removeItem(k){...} };
eval(fs.readFileSync("_wbsdk.global.js", "utf8"));
globalThis.fetch = (url, opts={}) => { /* 强制 Origin 头 */ };
// signInWithPassword 密码登录（免 OTP）→ database 读写 / llm 调用
// 用于：存量修复、批量入库、服务端核验、冒烟测试
```
