# 金额三算校验（规则 5/7）：单价×数量=合价、行项和=总计、同名分组分裂
# 用法: python check_amounts.py <quotation.xlsx> <qty_col> <unit_price_col> <total_price_col> [header_rows] [name_col]
# 例: python check_amounts.py quote.xlsx 15 16 17 2 7
# 列号为 1-based；header_rows 为表头占用的行数（数据从其下一行开始）
import sys, io, openpyxl

def main():
    src = sys.argv[1]
    qc, uc, tc = int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
    header_rows = int(sys.argv[5]) if len(sys.argv) > 5 else 1
    nc = int(sys.argv[6]) if len(sys.argv) > 6 else None
    dst = src.rsplit('.', 1)[0] + '_amount_check.txt'

    wb = openpyxl.load_workbook(src, data_only=False)
    wbv = openpyxl.load_workbook(src, data_only=True)
    out = io.open(dst, 'w', encoding='utf-8')

    for name in wb.sheetnames:
        ws, wsv = wb[name], wbv[name]
        rows, bad = 0, []
        sum_reported, sum_correct = 0.0, 0.0
        by_group = {}
        for r in range(header_rows + 1, wsv.max_row + 1):
            qty, unit, tot = wsv.cell(r, qc).value, wsv.cell(r, uc).value, wsv.cell(r, tc).value
            if qty is None and unit is None and tot is None:
                continue
            try:
                qty_f, unit_f, tot_f = float(qty or 0), float(unit or 0), float(tot or 0)
            except (TypeError, ValueError):
                continue  # 文本行（如合计行）跳过，单独提示人工核
            rows += 1
            correct = qty_f * unit_f
            sum_reported += tot_f
            sum_correct += correct
            if nc:
                g = str(wsv.cell(r, nc).value or '').strip().upper()
                by_group[g] = by_group.get(g, 0) + qty_f
            if abs(correct - tot_f) > 0.01:
                bad.append((r, qty, unit, tot, correct, ws.cell(r, tc).value))

        out.write('=== SHEET: %s ===\n' % name)
        out.write('数据行: %d | 合价错误行: %d\n' % (rows, len(bad)))
        out.write('报表合计: %s | 正确合计: %s | 差额: %s\n' % (
            format(sum_reported, ',.2f'), format(sum_correct, ',.2f'),
            format(sum_correct - sum_reported, ',.2f')))
        for b in bad[:30]:
            out.write('  [红] R%d qty=%s unit=%s 报表合价=%s 应为=%.2f (单元格内容: %r)\n' % b)
        if len(bad) > 30:
            out.write('  ... 其余 %d 行略\n' % (len(bad) - 30))
        if nc and by_group:
            out.write('分组数量（已归一 strip/大写）:\n')
            for g, q in sorted(by_group.items(), key=lambda x: -x[1]):
                out.write('  %-50s %s\n' % (g, format(q, ',.0f')))
        out.write('\n')
    out.write('提示：若全表无总计行，需人工确认总额从未被核算（高危）。\n')
    out.close()
    print('report -> %s' % dst)

main()
