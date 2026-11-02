"""產生離線字典 dict/*.json
來源：ECDICT（MIT，skywind3000/ECDICT）提供中文意思、詞性、詞形；
      CMUdict（BSD，cmusphinx/cmudict）提供美式發音，轉成 KK 音標。
用法：python3 tools/build_dict.py <ecdict.csv> <cmudict.dict> <輸出資料夾>
"""
import csv, json, re, sys, collections, pathlib
from opencc import OpenCC

ecsv, cmuf, outdir = sys.argv[1], sys.argv[2], pathlib.Path(sys.argv[3])
cc = OpenCC('s2twp')

# ---------- CMU → KK ----------
V = {'AA':'ɑ','AE':'æ','AO':'ɔ','AW':'aʊ','AY':'aɪ','EH':'ɛ','EY':'e','IH':'ɪ','IY':'i','OW':'o','OY':'ɔɪ','UH':'ʊ','UW':'u'}
C = {'B':'b','CH':'tʃ','D':'d','DH':'ð','F':'f','G':'g','HH':'h','JH':'dʒ','K':'k','L':'l','M':'m','N':'n','NG':'ŋ',
     'P':'p','R':'r','S':'s','SH':'ʃ','T':'t','TH':'θ','V':'v','W':'w','Y':'j','Z':'z','ZH':'ʒ'}
ONSETS = {'pl','pr','bl','br','tr','dr','kl','kr','gl','gr','fl','fr','θr','ʃr','sp','st','sk','sm','sn','sl','sw',
          'tw','dw','kw','gw','θw','spl','spr','str','skr','skw','pj','bj','kj','fj','mj','hj','vj','nj','lj'}
def vowel(p, s):
    if p == 'AH': return 'ʌ' if s in '12' else 'ə'
    if p == 'ER': return 'ɝ' if s in '12' else 'ɚ'
    return V[p]
def cmu_kk(phones):
    segs = []   # (text, is_vowel, stress)
    for ph in phones:
        m = re.match(r'([A-Z]+)([012]?)$', ph)
        p, s = m.group(1), m.group(2)
        if p in V or p in ('AH', 'ER'): segs.append([vowel(p, s), True, s])
        else: segs.append([C[p], False, ''])
    out = [x[0] for x in segs]
    marks = {}
    for i, (t, isv, s) in enumerate(segs):
        if not isv or s not in '12': continue
        # 往前找前一個母音，中間的子音取「合法的最長字首」放到重音後面
        j = i - 1
        while j >= 0 and not segs[j][1]: j -= 1
        cons = [segs[k][0] for k in range(j + 1, i)]
        take = 0
        for n in range(len(cons), 0, -1):
            cl = ''.join(cons[-n:])
            if n == 1 or cl in ONSETS: take = n; break
        if j < 0: take = len(cons)   # 第一個音節：重音標在最前面
        pos = i - take
        if pos == 0 and s == '1' and sum(1 for x in segs if x[1]) == 1: continue   # 單音節字不標重音
        marks[pos] = 'ˋ' if s == '1' else 'ˏ'
    return ''.join((marks.get(i, '') + t) for i, t in enumerate(out))

cmu = {}
for line in open(cmuf, encoding='utf-8'):
    line = line.split('#')[0].strip()
    if not line: continue
    w, *ph = line.split()
    if '(' in w: continue          # 只取第一個唸法
    cmu[w] = cmu_kk(ph)

# ---------- 英式 IPA（ECDICT）粗略轉 KK，CMU 沒有的時候用 ----------
def ipa_kk(p):
    p = p.replace('ә', 'ə').replace("'", 'ˋ').replace('ˈ', 'ˋ').replace(',', 'ˏ').replace('ˌ', 'ˏ').replace('ɡ', 'g')
    for a, b in [('ɜ:', 'ɝ'), ('ə:', 'ɝ'), ('i:', 'i'), ('u:', 'u'), ('ɑ:', 'ɑ'), ('ɔ:', 'ɔ'), ('əu', 'o'), ('əʊ', 'o'),
                 ('eɪ', 'e'), ('ei', 'E'), ('ai', 'aɪ'), ('au', 'aʊ'), ('ɔi', 'ɔɪ'), ('ɒ', 'ɑ'), ('e', 'ɛ')]:
        p = p.replace(a, b)
    return p.replace('E', 'e')

# ---------- 中文意思 ----------
POS = {'n':'名詞','v':'動詞','vt':'動詞','vi':'動詞','a':'形容詞','adj':'形容詞','adv':'副詞','ad':'副詞','prep':'介系詞',
       'conj':'連接詞','pron':'代名詞','int':'感嘆詞','interj':'感嘆詞','num':'數詞','art':'冠詞','aux':'助動詞',
       'pl':'名詞（複數）','abbr':'縮寫','phr':'片語'}
def senses_of(tr):
    out = collections.OrderedDict(); fallback = []
    for line in tr.replace('\\n', '\n').split('\n'):
        line = line.strip()
        if not line: continue
        if line.startswith('['):           # [网络] [计] [医]… 專業或網路用法先放備用
            fallback.append(re.sub(r'^\[[^\]]*\]\s*', '', line)); continue
        m = re.match(r'^([a-z]+)\.\s*(.*)$', line)
        pos, txt = (POS.get(m.group(1), ''), m.group(2)) if m else ('', line)
        if not txt: continue
        out.setdefault(pos, []).append(txt)
    if not out and fallback: out[''] = fallback[:1]
    res = []
    for pos, txts in out.items():
        z = '；'.join(txts)
        z = re.sub(r'\s*,\s*', '、', z); z = re.sub(r'\s*;\s*', '；', z)
        z = cc.convert(z).strip('；、 ')
        if z: res.append([pos, z[:40]])
    return res[:4]
def brief(z):
    parts = re.split(r'[；、]', re.sub(r'（[^）]*）|\([^)]*\)', '', z))
    parts = [x.strip() for x in parts if x.strip() and len(x.strip()) <= 10]
    return '；'.join(parts[:2]) if parts else z[:12]

FORMS = {'p':'過去式','d':'過去分詞','i':'現在分詞','3':'第三人稱單數','s':'複數','r':'比較級','t':'最高級'}

rows = list(csv.DictReader(open(ecsv, encoding='utf-8')))
num = lambda x: int(x or 0)
core = set()
for r in rows:
    f, b = num(r['frq']), num(r['bnc'])
    if 0 < f <= 20000 or 0 < b <= 20000 or r['tag'] or r['collins']: core.add(r['word'].lower())

entries, redirects = {}, {}
for r in rows:
    w = r['word'].strip(); lw = w.lower()
    if not re.fullmatch(r"[A-Za-z][A-Za-z' -]*", w): continue
    f, b = num(r['frq']), num(r['bnc'])
    single = ' ' not in w
    if single:
        keep = r['tag'] or r['collins'] or r['oxford'] or 0 < f <= 40000 or 0 < b <= 40000
    else:
        ws = lw.split()
        PART = {'up','down','out','off','on','in','with','to','for','away','over','about','into','of','at','by','back','through','around'}
        real = [l for l in r['translation'].replace('\\n', '\n').split('\n') if l.strip() and not l.strip().startswith('[')]
        keep = (len(ws) <= 4 and all(x in core for x in ws) and real
                and (r['phonetic'] or (len(ws) <= 3 and any(x in PART for x in ws[1:]))))
    if not keep or lw in entries: continue
    ss = senses_of(r['translation'])
    if not ss: continue
    if not single: ss = [[p or '片語', z] for p, z in ss]
    if single: kk = cmu.get(lw) or (ipa_kk(r['phonetic']) if r['phonetic'] else '')
    else:
        parts = [cmu.get(x) for x in lw.split()]
        kk = ' '.join(parts) if all(parts) else (ipa_kk(r['phonetic']) if r['phonetic'] else '')
    forms = []
    for ex in (r['exchange'] or '').split('/'):
        if ':' not in ex: continue
        k, v = ex.split(':', 1)
        if k == '0' and v: redirects.setdefault(lw, v.lower())
        if k in FORMS and v and v != lw:
            forms.append([FORMS[k], v]); redirects.setdefault(v.lower(), lw)
    e = [('[' + kk + ']') if kk else '', brief(ss[0][1]), ss]
    if forms: e.append(forms[:6])
    entries[lw] = e

# 變化形：自己沒有條目才轉到原形
redir = {k: v for k, v in redirects.items() if k not in entries and v in entries}
# 自己有條目、但只是「xxx 的複數」這種，也記下原形
for k, v in redirects.items():
    if k in entries and v in entries and v != k and len(entries[k]) < 5: entries[k].append(v) if len(entries[k]) == 4 else entries[k].extend([[], v])

outdir.mkdir(parents=True, exist_ok=True)
for f in outdir.glob('*.json'): f.unlink()
buckets = collections.defaultdict(dict)
for k, v in entries.items(): buckets[k[0] if 'a' <= k[0] <= 'z' else '_'][k] = v
for k, v in redir.items(): buckets[k[0] if 'a' <= k[0] <= 'z' else '_'][k] = '=' + v
total = 0
for letter, d in sorted(buckets.items()):
    s = json.dumps(d, ensure_ascii=False, separators=(',', ':'))
    (outdir / f'{letter}.json').write_text(s, encoding='utf-8'); total += len(s.encode())
meta = {'version': 1, 'words': len(entries), 'forms': len(redir), 'bytes': total, 'files': sorted(buckets)}
(outdir / 'meta.json').write_text(json.dumps(meta), encoding='utf-8')
print(meta)
