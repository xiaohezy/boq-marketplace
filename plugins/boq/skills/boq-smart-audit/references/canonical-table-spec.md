# 平台标准输出表格规范（Canonical Table Spec v1）

## 设计意图

厂家报价格式、业主询价格式、人工汇总格式各不相同——平台的终态输出必须是**一张表走天下**：
从询价到比价、从合同到报关、从订舱到清关，所有下游环节要的字段在一次解析后全部备齐。

## 字段分组（5 组 24 列）

### A. 标识组（解析必填）
| 列 | 说明 | 来源 |
|---|---|---|
| item_id | 平台内唯一编号 | 生成 |
| source_ref | 源文件行号/ITEM REF | 解析 |
| equipment_tag | 设备位号（归一化后） | 解析+归一 |
| category | 品类（A1 板换/B6 中压柜…） | 解析 |
| description_raw | 源描述原文 | 解析 |

### B. 技术参数组
| 列 | 说明 |
|---|---|
| spec_model | 规格型号（厂家选型后回填） |
| params_json | 参数键值（流量/扬程/功率/尺寸，带单位） |
| qty / unit | 数量与单位（套装双记：sets + units_per_set） |
| brand / origin | 品牌 / 产地（报价阶段回填） |

### C. 商务组
| 列 | 说明 |
|---|---|
| unit_price / currency | 单价与币种（保留原始币种+换算基准） |
| price_term | EXW/FOB/CIF/DDP（**不同条款禁止直接比价**） |
| lead_time | 交期 |
| validity | 报价有效期 |
| gap_flags | 待核价/TBD/暂估 标记 |

### D. 海关物流组（用户明确要求，平台差异化字段）
| 列 | 说明 | 备注 |
|---|---|---|
| hs_code | 海关编码（建议 10 位） | 设备类可由品类规则预填候选，人工确认 |
| hs_description | 报关品名（中英文） | 与 hs_code 联动 |
| package_dim | 单件包装尺寸 L×W×H (mm) | 订舱/装箱计算 |
| gross_weight / net_weight | 毛重/净重 (kg) | 运费与吊装 |
| hazmat_flag | 是否危化品/危险品（Y/N/待确认） | 含制冷剂设备、电池、油类常踩 |
| special_transport | 超限/温控/防潮等特殊运输要求 | |

### E. 合规与溯源组
| 列 | 说明 |
|---|---|
| certs | 认证要求（SASO/SABER/CE/WaterMark…，沙特项目实测刚需） |
| audit_flags | 10+1 条校验规则命中的标记（红/黄） |
| source_files | 该行的全部来源文件清单 |
| confirm_status | 待人工确认/已确认 |

## 生成规则

1. 解析 BOQ 后 A/B/E 组先填；报价对账后 C 组填；**D 组在品类模板里预置候选值**（如"板式换热器→HS 84195000 候选、非危化品"），解析时自动带出、人工确认。
2. D 组任何字段空缺时报告必须列"物流信息缺口清单"——危化品误判的代价是整柜扣关。
3. 输出 xlsx 时按组分色带，audit_flags 非空的行整行标色。
