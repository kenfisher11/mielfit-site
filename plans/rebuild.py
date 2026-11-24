"""11/20 컨테이너 교체 후 쇼츠 재제작 파이프라인 (사이트 데이터 → data.json → hook.html 렌더 → 음악 → 한국어 목소리)
사용: python3 rebuild.py plan.json   plan = [{"key":"2027-01-20_1","a":"p4961","b":"p7976","title":"...","next":["어뮤즈 ...", "2.2만원"] 또는 null}, ...]
출력: out/<key>.mp4, out/<key>.data.json"""
import sys, os, json, re, math, subprocess, wave, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from meta import P, pair, loadjs, D as SD, CAT
import numpy as np
H = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(H, 'out'); os.makedirs(OUT, exist_ok=True)
IMG = loadjs('/home/claude/mielfit-site/mielfit-img.js')
try:
    s = open('/home/claude/mielfit-site/mielfit-img2.js').read(); i = s.index('{"'); IMG.update(json.JSONDecoder().raw_decode(s[i:])[0])
except Exception as e: print('img2', e)
NN = SD['nname']
def img(pid): return IMG.get(pid + '|p') or IMG.get(pid + '|c') or ''
LAT = {'a':'에이','b':'비','c':'씨','d':'디','e':'이','f':'에프','g':'지','h':'에이치','i':'아이','j':'제이','k':'케이','l':'엘','m':'엠','n':'엔','o':'오','p':'피','q':'큐','r':'알','s':'에스','t':'티','u':'유','v':'브이','w':'더블유','x':'엑스','y':'와이','z':'지'}
D1 = ['', '일', '이', '삼', '사', '오', '육', '칠', '팔', '구']
def k4(n):
    s = ''
    for v, u in ((1000, '천'), (100, '백'), (10, '십'), (1, '')):
        d = n // v % 10
        if d: s += ('' if d == 1 and u else D1[d]) + u
    return s
def kn(n):
    n = int(n); m, r = divmod(n, 10000); s = ''
    if m: s += ('' if m == 1 else k4(m)) + '만 '
    if r: s += k4(r)
    return s.strip() or '영'
def say(t):
    t = re.sub(r'\d+\.\d+', '', re.sub(r'\(.*?\)', '', str(t))).replace('&', ' 앤 ').replace(':', '')
    t = re.sub(r'\b([A-Za-z]{1,4})\b', lambda m: ''.join(LAT[c] for c in m.group(1).lower()), t)
    t = re.sub(r'\d+', lambda m: kn(m.group(0)), t)
    return re.sub(r'\s+', ' ', t).strip()
def MAN(n):
    if n >= 10000:
        m = n / 10000; return math.floor(m + .5) * 10000 if (m >= 10 or m == int(m)) else math.floor(m * 10 + .5) * 1000
    return math.floor(n / 1000 + .5) * 1000
BRK = {'VT COSMETICS': 'VT'}
def mkdata(key, a, b, nxt, ep, SIM=None):
    A, B = P[a], P[b]; x = pair(a, b)
    sim = x['sim'] if x else SIM; times = x['times'] if x else round(A['ppm'] / B['ppm'], 1)
    ids = (x or {}).get('same') or [i for i in A.get('key', []) if i in set(B.get('ingr', []))] or [i for i in A.get('ingr', [])[1:] if i in set(B.get('ingr', [])[:15])]
    same = [NN[i] for i in ids][:3]
    D = {'ep': ep, 'cat': A['group'], 'cat_ko': CAT.get(A['group'], '화장품'), 'sim': sim, 'times': times, 'same': same,
         'a': {'brand_ko': BRK.get(A['brand'], A['brand']), 'name_ko': A['name'].replace('\\u0026', '&'), 'price': A['price'], 'ml': A['ml'], 'img': img(a)},
         'b': {'brand_ko': BRK.get(B['brand'], B['brand']), 'name_ko': B['name'].replace('\\u0026', '&'), 'price': B['price'], 'ml': B['ml'], 'img': img(b)}}
    if nxt: D['nextL'], D['nextD'] = nxt
    return D
def render(key, D, music):
    from playwright.sync_api import sync_playwright
    fd = os.path.join(H, 'frames_' + key); shutil.rmtree(fd, ignore_errors=True); os.makedirs(fd)
    with sync_playwright() as pw:
        br = pw.chromium.launch(); pg = br.new_page(viewport={'width': 1080, 'height': 1920})
        pg.add_init_script('window.__D=' + json.dumps(D, ensure_ascii=False))
        pg.goto('file://' + os.path.join(H, 'render', 'hook.html')); pg.wait_for_timeout(600)
        for i in range(450):
            pg.evaluate(f'T({i / 30})'); pg.screenshot(path=f'{fd}/{i:04d}.jpg', type='jpeg', quality=92)
        br.close()
    tmp = os.path.join(OUT, key + '.base.mp4')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', '30', '-i', f'{fd}/%04d.jpg', '-i', music, '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-preset', 'medium', '-crf', '20', '-c:a', 'aac', '-b:a', '160k', '-shortest', '-movflags', '+faststart', tmp], check=True)
    shutil.rmtree(fd, ignore_errors=True); return tmp
_tts = None
def tts():
    global _tts
    if _tts is None:
        import sherpa_onnx; M = '/home/claude/tts_model/vits-mimic3-ko_KO-kss_low/'
        _tts = sherpa_onnx.OfflineTts(sherpa_onnx.OfflineTtsConfig(model=sherpa_onnx.OfflineTtsModelConfig(vits=sherpa_onnx.OfflineTtsVitsModelConfig(model=M + 'ko_KO-kss_low.onnx', tokens=M + 'tokens.txt', data_dir=M + 'espeak-ng-data'), num_threads=4)))
    return _tts
def gen(text, fn):
    a = tts().generate(text, sid=0, speed=1.2); x = (np.clip(np.array(a.samples), -1, 1) * 32767).astype(np.int16)
    f = wave.open(fn, 'wb'); f.setnchannels(1); f.setsampwidth(2); f.setframerate(a.sample_rate); f.writeframes(x.tobytes()); f.close()
def voice(key, D, base):
    A, B = D['a'], D['b']; cat = D['cat_ko']
    samev = A['ml'] and B['ml'] and abs(float(A['ml']) - float(B['ml'])) / float(A['ml']) > .1
    bp = round(float(B['price']) * float(A['ml']) / float(B['ml']) / 100) * 100 if samev else float(B['price'])
    diff = MAN(float(A['price']) - bp)
    ln = [(0.05, f"이 {cat}, 얼마게요?"), (1.3, f"{say(A['brand_ko'])} {cat} 쓰시는 분, {kn(diff)} 원 더 내고 있어요"), (3.3, f"정답은 {say(B['brand_ko'])} {cat}"),
          (5.2, (f"같은 양이면 " if samev else '') + f"{kn(diff)} 원 아껴요"),
          (10.4, f"다음 편은 {say(D['nextL'])}, 구독해 두세요" if D.get('nextL') else "내일도 쌍둥이 공개, 구독해 두세요")]
    ins, flt = ['-i', base], []
    for i, (t0, text) in enumerate(ln):
        fn = os.path.join(OUT, f'_v{i}.wav'); gen(text, fn); ins += ['-i', fn]; ms = int(t0 * 1000); flt.append(f'[{i + 1}]adelay={ms}|{ms}[v{i}]')
    flt.append(''.join(f'[v{i}]' for i in range(len(ln))) + f'amix=inputs={len(ln)}:normalize=0,volume=1.6,aresample=44100,pan=stereo|c0=c0|c1=c0[v]')
    flt.append('[0:a]volume=0.28[m]'); flt.append('[m][v]amix=inputs=2:normalize=0:duration=first[out]')
    out = os.path.join(OUT, key + '.mp4')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', *ins, '-filter_complex', ';'.join(flt), '-map', '0:v', '-map', '[out]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '160k', '-movflags', '+faststart', out], check=True)
    return out, ' / '.join(t for _, t in ln), diff
if __name__ == '__main__':
    plan = json.load(open(sys.argv[1])); musics = sorted(os.listdir(os.path.join(H, 'music')))
    for i, it in enumerate(plan):
        D = mkdata(it['key'], it['a'], it['b'], it.get('next'), it.get('ep'), it.get('sim'))
        json.dump(D, open(os.path.join(OUT, it['key'] + '.data.json'), 'w'), ensure_ascii=False)
        base = render(it['key'], D, os.path.join(H, 'music', musics[i % len(musics)]))
        out, lines, diff = voice(it['key'], D, base); os.remove(base)
        print('made', it['key'], '|', lines, flush=True)
