# 数据模型与 RLS 设计套路

## 表设计通用套路

- `owner_id TEXT NOT NULL DEFAULT auth.uid()`——owner 由服务端决定，客户端不送；TEXT 不是 uuid（auth.uid() 返回文本）。
- 每表 `created_at TIMESTAMPTZ NOT NULL DEFAULT now()`；列表展示加 `owner_name`（仅显示，绝不参与权限）。
- 业务外键用普通字段（如 task_id），级联靠应用层纪律，不迷信外键约束。
- **审计表只 INSERT**：logs 类表仅授权 SELECT+INSERT，状态可重放、历史不可改。

## RLS 两道门（缺一门就是 42501）

1. `GRANT ... TO authenticated`（表级门票）
2. `CREATE POLICY ...`（行级门票）

逐条 exec_sql mode=migrate 执行（单语句限制）。PostgreSQL 无 `CREATE POLICY IF NOT EXISTS`，先 `DROP POLICY IF EXISTS` 保证幂等。

## 三角色平台的实战 RLS 模板

```sql
-- ① 可见性函数（SECURITY DEFINER 绕过 RLS 做跨表判定；只读、入参校验）
CREATE OR REPLACE FUNCTION can_view_task(tid BIGINT)
RETURNS BOOLEAN LANGUAGE sql SECURITY DEFINER STABLE AS $$
  SELECT NOT is_supplier_user(auth.uid())                              -- 非供应商看全部
      OR EXISTS (SELECT 1 FROM task_logs                                -- 供应商只看派给自己的
                 WHERE task_id = tid AND action = '已派单'
                 AND detail::jsonb ->> 'sid' = supplier_id_of(auth.uid())::text)
$$;
-- ② 主表：读走函数，写限 owner（或负责人）
CREATE POLICY tasks_read ON quote_tasks FOR SELECT TO authenticated USING (can_view_task(id));
CREATE POLICY tasks_write ON quote_tasks FOR INSERT TO authenticated WITH CHECK (owner_id = auth.uid());
-- ③ 报价表：供应商只看自己的，员工看全部；写入限本人供应商身份
-- ④ 日志表：SELECT 同主表可见性，INSERT 全员，UPDATE/DELETE 不授权
```

要点：
- **is_supplier_user 判定走档案表**（suppliers.contact = 登录邮箱），不走前端传参。
- 供应商门户绑定也是同一个 contact=email 机制：注册→批准→自动建档（contact=邮箱）→登录即进门户，全程无人工关联。
- 多对多派单不建中间表，用 logs 折叠（已派单/取消派单 事件流算当前在派集合）——免建表且天然留痕；数据量大后再升级实体表。

## 账号体系：日志状态机（免建账号表）

用 task_id=0 的账号日志折叠出人员状态：
- `账号申请` {email, apply_type: staff|supplier, company} → pending
- `账号批准` {email, role, company, by} → active（批准供应商时**同步在 suppliers 建档**，contact=email）
- `账号停用/启用` → disabled/active
折叠规则：按 created_at 顺序重放，最后一个生效事件决定当前状态。第一个账号可自助成为管理员（bootstrap，仅一次机会）。

## 迁移纪律

- DDL 全走服务端 migrate 通道；应用代码永不跑 DDL。
- 危险操作（DROP/TRUNCATE/无 WHERE DELETE/启用 RLS 于存量表）必须先列影响面并获用户确认。
- 排错：42501=缺 GRANT 或 POLICY；42P01=表不存在；23505=唯一冲突；HTTP 401=网关凭证问题（不是 RLS 能修的，别乱放权）。
