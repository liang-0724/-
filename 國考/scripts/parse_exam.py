import re, html, sys, json
def parse(path):
    s = open(path, encoding='utf-8', errors='replace').read()
    # split into table rows
    rows = re.findall(r'<tr[^>]*>(.*?)</tr>', s, re.S)
    out = []; cur = None
    for r in rows:
        text = html.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', r))).strip()
        links = [html.unescape(l) for l in re.findall(r'href="([^"]*wHandExamQandA_File[^"]*)"', r)]
        if not links and text and ('_' in text) and len(text) < 80:
            cur = text; continue
        if links and cur:
            q = [l for l in links if 't=Q' in l]; a = [l for l in links if 't=S' in l]; m = [l for l in links if 't=M' in l]
            subj = re.split(r'\s+試題', text)[0].strip()
            out.append(dict(cls=cur, subject=subj, q=q[0] if q else None, s=a[0] if a else None, m=m[0] if m else None))
    return out
if __name__ == '__main__':
    res = parse(sys.argv[1])
    for x in res:
        if len(sys.argv) < 3 or sys.argv[2] in x['cls']:
            print(json.dumps(x, ensure_ascii=False))
