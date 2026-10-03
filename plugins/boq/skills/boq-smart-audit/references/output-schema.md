# 行项 JSON Schema（结构化输出）

LLM 解析 BOQ 后的标准输出格式：

```json
{
  "source_file": "Heat Exchanger-BOQ.xlsx",
  "sheet": "HEAT EXCHANGERS",
  "category": "HVAC INSTALLATION / COMMON AREA",
  "currency": "US$",
  "line_items": [
    {
      "row": 10,
      "item_ref": "B",
      "equipment_tag": "HEX-C1",
      "description": "Ref. HEX-C1 (Flow rate 40.61 L/S)",
      "service": "cooling",
      "zone": null,
      "qty": 3,
      "unit": "No",
      "set_info": null,
      "params": { "flow_rate_Ls": 40.61 },
      "scope": "Supply and installation of plate heat exchangers - cooling including ..."
    }
  ],
  "implicit_items": [
    {
      "source_row": 6,
      "keyword": "including thermostat",
      "extracted_item": "温控器",
      "note": "无对应行项，需与报价核对是否含配"
    }
  ],
  "total_qty": 17,
  "notes": [
    "item_ref 'C' 重复出现（R12/R16）",
    "冷却侧位号 HEX-C1/C2 缺 R 前缀（报价写作 HEX-R-C1/C2）"
  ]
}
```

## 字段说明

- `row`：源文件行号（必填，一切溯源靠它）
- `set_info`：套装设备填 `{"sets": 1, "units_per_set": 3, "duty": 2, "standby": 1}`；非套装填 null
- `params`：流量/扬程/功率/尺寸等，键名用 `名称_单位`（如 `head_m`、`flow_rate_Ls`、`size_mm`）
- `scope`：该行项所属的 scope 段落原文（截取）
- `implicit_items`：从 scope/描述文字抽出的隐含实物，不进 total_qty
- `notes`：源文件异常，只记录不修正

## 位号归一化函数（对账用）

```python
import re
def norm(tag):
    t = re.sub(r'\s+', '', tag).upper().replace('－', '-')
    if re.fullmatch(r'HEX-C\d', t):      # 缺块前缀的冷却侧位号
        t = 'HEX-R-' + t[4:]
    return t
```

按品类扩展归一规则，新规则必须在报告 notes 中声明。
