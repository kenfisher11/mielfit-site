"""site data(js)로 업로드 메타(제목·설명·태그) 재생성 — 11/20 컨테이너 교체 후 복구"""
import json,re,math
def loadjs(p):
  s=open(p).read().strip()
  if s.startswith('window.'): s=s[s.index('=')+1:].rstrip(';')
  else: s=s[s.index('})(')+3:].rstrip(';').rstrip(')')
  return json.JSONDecoder().raw_decode(s)[0]
D=loadjs('/home/claude/mielfit-site/mielfit-data.js'); D2={'products':loadjs('/home/claude/mielfit-site/mielfit-data2.js')}
P={p['id']:p for p in D['products']+D2.get('products',[])}
pairs=loadjs('/home/claude/mielfit-site/mielfit-pairs.js')['pairs']+(lambda z: z['pairs'] if isinstance(z,dict) else z)(loadjs('/home/claude/mielfit-site/mielfit-pairs2.js'))
DAILY={'toner':1.5,'serum':.5,'lotion':.6,'cream':.6,'eye':.13,'sun':1.0,'cleanser':2.0,'oil':2.0}
CAT={'toner':'토너','serum':'세럼','lotion':'로션','cream':'크림','eye':'아이크림','sun':'선크림','cleanser':'클렌저','oil':'클렌징오일'}
def find(brand,kw):
  c=[p for p in P.values() if brand in p['brand'] and kw in p['name']]
  return c
def pair(a,b): return next((x for x in pairs if x['a']==a and x['b']==b),None)
def nm(p): return p['full'] if p['full'].startswith(p['brand']) else f"{p['brand']} {p['full']}"
def desc(a,b,x,first):
  ys=round((a['ppm']-b['ppm'])*DAILY.get(a['group'],.5)*365/100)*100
  return (f"{first}\n\n{nm(a)} → {nm(b)}\n"
          f"전성분 {x['sim']}% 닮음 · 같은 돈이면 {x['times']}통 · 1년 {ys:,}원 차이\n\n"
          "내 화장품 쌍둥이, 사이트에서 사진 한 장으로 찾기 → 프로필 링크(미엘핏)\n\n"
          "성분이 비슷해도 효과·사용감은 다를 수 있어요. 가격은 조사 시점 기준.\n#듀프 #화장품추천 #가성비화장품 #올리브영")
def tags(a,b):
  return ','.join(['듀프','화장품 듀프','반값 화장품','가성비 화장품','올리브영 추천',f"{CAT.get(a['group'],'화장품')} 추천",a['brand'],b['brand'],nm(a),nm(b)])
