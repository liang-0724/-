"""Build GoodNotes-ready PDFs organised by subject.
usage: python3 -I build.py <workdir> <outdir>"""
import sys, os, json, glob, io
from pypdf import PdfReader, PdfWriter
from pypdf.annotations import Link
from pypdf.generic import Fit
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
pdfmetrics.registerFont(TTFont('WQY', '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc', subfontIndex=0))
SESSION = {'105020': (105, 1), '105100': (105, 2), '106020': (106, 1), '106100': (106, 2), '107020': (107, 1), '107100': (107, 2),
           '108030': (108, 1), '108100': (108, 2), '109020': (109, 1), '109100': (109, 2), '110020': (110, 1), '110100': (110, 2),
           '110101': (110, 2), '111020': (111, 1), '111100': (111, 2), '112020': (112, 1), '112100': (112, 2), '113020': (113, 1),
           '113090': (113, 2), '114020': (114, 1), '114090': (114, 2), '115020': (115, 1), '115090': (115, 2)}
NAME = {'1_物理治療基礎學': '物理治療基礎學（解剖學、生理學、肌動學與生物力學）',
        '2_物理治療學概論': '物理治療學概論（物理治療史、倫理學、行政管理學）',
        '3_物理治療技術學': '物理治療技術學（電療學、熱療學、操作治療學、輔具學）',
        '4_神經疾病物理治療學': '神經疾病物理治療學',
        '5_骨科疾病物理治療學': '骨科疾病物理治療學',
        '6_心肺與小兒疾病物理治療學': '心肺疾病與小兒疾病物理治療學'}
work, outdir = sys.argv[1], sys.argv[2]
ents = {}
for mf in glob.glob(f'{work}/manifest_*.json'):
    for e in json.load(open(mf)):
        if e.get('q') and (e.get('s') or e.get('m')):
            ents[(e['code'], e['key'])] = e
by_subj = {}
for (code, key), e in ents.items():
    y, n = SESSION[code]
    by_subj.setdefault(key, []).append((y, n, e))
summary = {}
for key, lst in sorted(by_subj.items()):
    lst.sort(key=lambda t: (t[0], t[1]), reverse=True)   # newest first
    short = key.split('_', 1)[1]
    single_dir = f'{outdir}/單份/{key}'; os.makedirs(single_dir, exist_ok=True)
    # --- single-exam files (questions + answer key) ---
    for y, n, e in lst:
        w = PdfWriter()
        w.append(e['q'], outline_item='試題')
        w.append(e.get('m') or e['s'], outline_item='標準答案（含更正）' if e.get('m') else '標準答案')
        w.add_metadata({'/Title': f'{y}年第{n}次 {short}'})
        w.write(f'{single_dir}/{y}-{n}_{short}.pdf')
    # --- merged file: cover + all exams, newest first ---
    rows, page = [], 1
    for y, n, e in lst:
        qn = len(PdfReader(e['q']).pages); an = len(PdfReader(e.get('m') or e['s']).pages)
        rows.append((y, n, e, page, qn, page + qn, an)); page += qn + an
    buf = io.BytesIO(); c = canvas.Canvas(buf, pagesize=A4); W, H = A4
    c.setFont('WQY', 20); c.drawString(50, H - 70, '物理治療師國考｜歷屆試題')
    c.setFont('WQY', 15); c.drawString(50, H - 98, NAME[key])
    c.setFont('WQY', 9.5); c.setFillGray(0.35)
    c.drawString(50, H - 120, f'{lst[-1][0]}–{lst[0][0]} 年，共 {len(lst)} 次考試｜新到舊排列｜每份試題後面附標準答案（有更正者採考選部更正答案）')
    c.drawString(50, H - 135, '資料來源：考選部考畢試題查詢平臺 wwwq.moex.gov.tw　　點下方「試題 / 答案」可直接跳頁')
    c.setFillGray(0); links = []
    top = H - 175; lh = min(26, (top - 60) / max(len(rows), 1))
    c.setFont('WQY', 12)
    for i, (y, n, e, qp, qn, ap, an) in enumerate(rows):
        yy = top - i * lh
        if i % 2 == 0:
            c.setFillGray(0.95); c.rect(45, yy - 7, W - 90, lh, stroke=0, fill=1); c.setFillGray(0)
        c.drawString(55, yy, f'{y} 年　第{"一二"[n-1]}次')
        c.setFillColorRGB(0.1, 0.3, 0.7)
        c.drawString(250, yy, f'試題  p.{qp + 1}'); c.drawString(390, yy, f'答案  p.{ap + 1}')
        c.setFillGray(0)
        links.append(((245, yy - 6, 360, yy + lh - 8), qp)); links.append(((385, yy - 6, 500, yy + lh - 8), ap))
    c.showPage(); c.save(); buf.seek(0)
    w = PdfWriter(); w.append(PdfReader(buf), outline_item='目錄')
    for y, n, e, qp, qn, ap, an in rows:
        parent = w.add_outline_item(f'{y}年第{n}次', qp)
        w.append(e['q']); w.add_outline_item('試題', qp, parent=parent)
        w.append(e.get('m') or e['s']); w.add_outline_item('答案', ap, parent=parent)
    for rect, target in links:
        w.add_annotation(page_number=0, annotation=Link(rect=rect, target_page_index=target, fit=Fit.fit()))
    w.add_metadata({'/Title': f'物理治療師國考 {short} 歷屆試題 {lst[-1][0]}-{lst[0][0]}'})
    os.makedirs(f'{outdir}/合併版', exist_ok=True)
    out = f'{outdir}/合併版/{key}_歷屆試題_{lst[-1][0]}-{lst[0][0]}.pdf'
    w.write(out)
    summary[key] = dict(n=len(lst), pages=page, exams=[f'{y}-{n}' for y, n, _ in lst], file=out)
    print(key, len(lst), 'exams', page, 'pages', os.path.getsize(out) // 1024, 'KB', flush=True)
json.dump(summary, open(f'{work}/summary.json', 'w'), ensure_ascii=False, indent=1)
