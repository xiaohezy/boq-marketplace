# 金标准对照（工作流第 4 步）：AI 解析 JSON vs 人工汇总/厂家报价 xlsx
# 用法: python compare_gold.py <ai_parse.json> <gold.xlsx> <tag_col> <qty_col> <first_data_row> [sheet_idx]
# 输出 compare_gold_report.txt 到 ai_parse.json 同目录
# 位号归一规则按品类扩展（见 references/output-schema.md），新增规则须写入报告 notes
import sys, os, re, json, io, openpyxl

def norm(tag):
    t = re.sub(r'\s+', '', str(tag)).upper().replace('－', '-').replace('&amp;', '&')
    if re.fullmatch(r'HEX-C\d', t):
        t = 'HEX-R-' + t[4:]
    return t

def main():
    ai_path, gold_path = sys.argv[1], sys.argv[2]
    tc, qc, first_row = int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
    sheet_idx = int(sys.argv[6]) if len(sys.argv) > 6 else 0
    dst = os.path.join(os.path.dirname(ai_path) or '.', 'compare_gold_report.txt')
    out = io.open(dst, 'w', encoding='utf-8')

    ai = json.load(open(ai_path, encoding='utf-8'))
    items = ai['line_items']

    wb = openpyxl.load_workbook(gold_path, data_only=True)
    ws = wb.worksheets[sheet_idx]
    gold = {}
    for row in ws.iter_rows(min_row=first_row, values_only=False):
        tag = row[tc - 1].value
        qty = row[qc - 1].value
        if tag is None or qty is None:
            continue
        try:
            gold.setdefault(norm(tag), {'tag_raw': str(tag), 'qty': 0})
            gold[norm(tag)]['qty'] += int(float(qty))
        except (TypeError, ValueError):
            pass

    ai_map = {}
    for it in items:
        ai_map.setdefault(norm(it['equipment_tag']), []).append(it)

    matched, qty_err, missing = 0, [], []
    for k, g in gold.items():
        if k in ai_map:
            ai_qty = sum(i['qty'] for i in ai_map[k])
            if ai_qty == g['qty']:
                matched += 1
            else:
                qty_err.append((g['tag_raw'], ai_qty, g['qty']))
        else:
            missing.append(g['tag_raw'])
    extra = [i['equipment_tag'] for k, v in ai_map.items() if k not in gold for i in v]

    out.write('=== 金标准对照报告 ===\n')
    out.write('AI: %s\nGOLD: %s\n\n' % (ai.get('source_file'), os.path.basename(gold_path)))
    out.write('行项+数量匹配: %d/%d\n' % (matched, len(gold)))
    out.write('数量不符(AI/GOLD): %s\n' % (qty_err or '无'))
    out.write('AI 漏项: %s\n' % (missing or '无'))
    out.write('AI 多项: %s\n' % (extra or '无'))
    out.write('AI 总台数: %d | GOLD 总台数: %d\n' % (
        sum(i['qty'] for i in items), sum(g['qty'] for g in gold.values())))
    if ai.get('notes'):
        out.write('\n源文件异常:\n')
        for n in ai['notes']:
            out.write('* %s\n' % n)
    if ai.get('implicit_items'):
        out.write('\n隐含行项（需与报价核对）:\n')
        for im in ai['implicit_items']:
            out.write('* R%s %s -> %s\n' % (im.get('source_row'), im.get('keyword'), im.get('extracted_item')))
    out.close()
    print('report -> %s' % dst)

main()
