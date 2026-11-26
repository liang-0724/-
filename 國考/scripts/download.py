"""Download PT exam question/answer PDFs for given exam codes.
usage: python3 -I download.py <workdir> <code> [<code> ...]"""
import sys, os, json, re, subprocess, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parse_exam import parse
BASE = 'https://wwwq.moex.gov.tw/exam/'
SUBJ = [('基礎學', '1_物理治療基礎學'), ('概論', '2_物理治療學概論'), ('技術學', '3_物理治療技術學'),
        ('神經', '4_神經疾病物理治療學'), ('骨科', '5_骨科疾病物理治療學'), ('心肺', '6_心肺與小兒疾病物理治療學')]
def fetch(url, out):
    for i in range(4):
        r = subprocess.run(['curl', '-sS', '-m', '120', '-o', out, '-w', '%{http_code} %{content_type}', url], capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.startswith('200'):
            return r.stdout
        time.sleep(3 * (i + 1))
    return 'FAIL ' + r.stdout + r.stderr
work = sys.argv[1]; os.makedirs(work + '/raw', exist_ok=True)
manifest = []
for code in sys.argv[2:]:
    page = f'{work}/e{code}.html'
    if not os.path.exists(page) or os.path.getsize(page) < 5000:
        print(code, 'page', fetch(f'{BASE}wFrmExamQandASearch.aspx?y={int(code[:3])+1911}&e={code}', page), flush=True)
    rows = [r for r in parse(page) if '物理治療師' in r['cls']]
    if not rows:
        print(code, 'NO PT CLASS', flush=True); continue
    for r in rows:
        key = next((k for kw, k in SUBJ if kw in r['subject']), None)
        if key is None:
            print(code, 'UNMAPPED', r['subject'], flush=True); continue
        ent = dict(code=code, cls=r['cls'], subject=r['subject'], key=key)
        for t in ('q', 's', 'm'):
            if not r[t]: continue
            out = f'{work}/raw/{code}_{key}_{t}.pdf'
            if not (os.path.exists(out) and open(out, 'rb').read(4) == b'%PDF'):
                st = fetch(BASE + r[t], out)
            else:
                st = 'cached'
            ok = os.path.exists(out) and open(out, 'rb').read(4) == b'%PDF'
            if not ok and os.path.exists(out): os.remove(out)
            ent[t] = out if ok else None
            if t != 'm' and not ok: print(code, key, t, 'NOT PDF', st, flush=True)
        manifest.append(ent)
        print(code, key, {t: bool(ent.get(t)) for t in 'qsm'}, flush=True)
json.dump(manifest, open(f'{work}/manifest_{"_".join(sys.argv[2:])[:40]}.json', 'w'), ensure_ascii=False, indent=1)
