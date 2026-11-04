"""Migrate six preserved itineraries to one app. No itinerary facts are refreshed here."""
from pathlib import Path
import json,re,shutil,sys,hashlib
ROOT=Path(__file__).resolve().parents[1]
SRC=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT.parent/'source'
text=(SRC/'cycling.html').read_text()
def literal(text,prefix):return json.JSONDecoder().raw_decode(text.split(prefix,1)[1])[0]
bike=literal(text,'const DATA=');guides=literal(text,'const TRAVEL=');rest=literal(text,'const REST=')
rail=literal((SRC/'assets/rail-data.js').read_text(),'window.RAIL_DATA=')
context=literal((SRC/'assets/rail-context.js').read_text(),'window.RAIL_CONTEXT=')
trips={}
meta=[('small','内陸を巡る試走','筑豊・朝倉・日田','日田','#247759'),('kaikyo','海響館と角島の試走','下関・川棚温泉・角島','下関','#347b91'),('main','自転車で九州一周','海沿いを中心に、九州7県へ','熊本','#bb683e'),('kyoto','自転車で京都往復','往路は瀬戸内、帰路は山陰','京都','#78589a')]
for key,title,subtitle,cover,color in meta:
 days=[]
 for d in bike[key]:
  days.append({**d,'kind':'stay' if d['rest'] else 'move','notes':d['note'],'stay':None if d['stay']=='帰宅' else '甘木' if d['stay']=='朝倉・甘木' else d['stay'],'originalStay':d['stay'],'originalTitle':d['title'],'sources':[]})
 tips=['走行距離は道路・宿が未確定の概算です。地図は街を結んだ概略図で、通行可否を確認したナビではありません。','荒天や体調不良のときは休養日を削らず、日程の延長や一部区間の交通機関利用を検討してください。']
 if key=='kaikyo':tips+=['折尾〜下関の往路、門司港〜折尾の帰路は輪行を想定した試走です。自転車だけで完走する周回ではありません。角島大橋は強風・悪天候時に無理をせず、島への寄り道を省いてください。']
 if key=='main':tips+=['佐多岬・指宿・天草・国東半島の外周などを省いた短縮案です。島原〜熊本と鹿児島〜桜島でフェリーを使います。']
 if key=='kyoto':tips+=['28日間は走行22日＋休養6日。京都は12〜14日目の夜に3連泊し、13・14日目は休養日です。','往路は瀬戸内側、帰路は山陰側。関門海峡は往復とも人道トンネルを押し歩きます。基本案に列車・船の区間はありません。','7・15・17日目など負荷の大きい区間は分割を検討。山陰・丹波の冬の積雪や凍結を前提にした計画ではありません。']
 trips['bike-'+key]={'id':'bike-'+key,'mode':'bike','legacy':key,'label':title,'subtitle':subtitle,'intro':tips[0], 'color':color,'cover':cover,'days':days,'restCount':sum(d['rest'] for d in bike[key]),'tips':tips,'checked':'2026-10-04' if key=='kyoto' else '2026-09-26','transportReserve':15000 if key=='kaikyo' else 5000,'localReserve':20000 if key=='kyoto' else 10000,'buffer':30000 if key=='kyoto' else 15000}
for key,t in rail['trips'].items():
 id='rail-'+key;trips[id]={**t,'id':id,'mode':'rail','legacy':key,'cover':'長崎' if key=='kyushu' else '京都','label':'列車で九州周遊' if key=='kyushu' else '列車で京都・山陰','checked':rail['checked'],'transportReserve':t['railReserve']}
app={'version':'2026-11-05-unified','migrated':'2026-11-05','sourceCommit':'eb6c04987062e68af31a23b6b2e6a7b597eb721a','trips':trips,'bike':{'places':bike['places'],'guides':guides,'rest':rest},'rail':rail,'geo':bike['geo'],'sources':{**rail['sources'],**{k:[v['name'],v['url']] for k,v in rest['sources'].items()}},'hotels':guides['hotels']}
(ROOT/'assets').mkdir(exist_ok=True)
(ROOT/'assets/app.css').write_text((SRC/'assets/rail.css').read_text()+(ROOT/'assets/style-extension.css').read_text())
(ROOT/'assets/data.js').write_text('window.TRAVEL_APP_DATA='+json.dumps(app,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')+';\n')
# Retain photographic content and original attribution, with no new remote image requests.
shutil.copytree(SRC/'assets/photos',ROOT/'assets/photos',dirs_exist_ok=True)
manifest=json.loads((ROOT/'assets/photos/manifest.json').read_text());manifest['places'].update(context.get('photos',{}))
(ROOT/'assets/photos/data.js').write_text('window.JOURNEY_PHOTOS='+json.dumps(manifest,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')+';\n')
for n in ['PHOTO-CREDITS.md','RAIL-PHOTO-CREDITS.md']:shutil.copy2(SRC/n,ROOT/n)
# Keep the original geodata license and editable geometry together.
i=text.find('GEOGRAPHIC DATA NOTICE')
if i>=0:(ROOT/'MAP-LICENSES.txt').write_text(text[i:text.find('-->',i)])
(ROOT/'.nojekyll').touch()
for alias,tid in [('cycling.html','bike-small'),('rail.html','rail-kyushu')]:
 (ROOT/alias).write_text(f'<!doctype html><html lang="ja"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>旅のプランへ</title><meta http-equiv="refresh" content="0;url=./?trip={tid}"><p><a href="./?trip={tid}">統合した旅行プランを開く</a></p></html>')
report={'sourceCommit':app['sourceCommit'],'trips':{},'sourceFileHashes':{f:hashlib.sha256((SRC/f).read_bytes()).hexdigest() for f in ['cycling.html','assets/rail-data.js']}}
for k,t in trips.items():
 source=bike[t['legacy']] if t['mode']=='bike' else rail['trips'][t['legacy']]['days']
 assert len(source)==len(t['days'])
 for a,b in zip(source,t['days']):
  assert a['stops']==b['stops']
  if t['mode']=='bike':assert a['km']==b['km'] and a['rest']==b['rest'] and a['stay']==b['originalStay']
  else:assert a==b
 report['trips'][k]={'days':len(t['days']),'restDays':t['restCount'],'nights':sum(bool(d['stay']) for d in t['days']),'preserved':True}
(ROOT/'migration-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps(report,ensure_ascii=False))
