# 通用 xlsx 内容导出：python dump_xlsx.py <in.xlsx> <out.txt>
import sys, io, openpyxl

src, dst = sys.argv[1], sys.argv[2]
out = io.open(dst, 'w', encoding='utf-8')
wb = openpyxl.load_workbook(src, data_only=True)
out.write('sheets: %s\n' % wb.sheetnames)
for ws in wb.worksheets:
    out.write('\n######## SHEET: %s  dims=%s  state=%s ########\n' % (ws.title, ws.dimensions, ws.sheet_state))
    mr = [str(r) for r in ws.merged_cells.ranges]
    if mr:
        out.write('merged: %s\n' % mr[:40])
    for row in ws.iter_rows():
        vals = [('' if c.value is None else str(c.value).replace('\n', ' / ')) for c in row]
        line = ' | '.join(vals).rstrip(' |')
        if line.strip():
            out.write('R%d: %s\n' % (row[0].row, line))
out.close()
