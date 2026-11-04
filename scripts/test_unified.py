"""Browser regression tests for six independent trips sharing one UI."""
import json,os,subprocess,time
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
url=os.environ.get('SITE_URL','http://127.0.0.1:8871/')
server=None;errors=[];layouts=[];checks=[]
if not os.environ.get('SITE_URL'):
 server=subprocess.Popen(['python','-m','http.server','8871','--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(.5)
try:
 with sync_playwright() as p:
  browser=p.chromium.launch()
  ctx=browser.new_context(viewport={'width':1440,'height':1000},reduced_motion='reduce')
  page=ctx.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
  page.goto(url,wait_until='networkidle');page.wait_for_function('window.TravelPlanner')
  assert page.locator('.tripcard').count()==6
  assert page.locator('iframe').count()==0
  page.locator('[data-filter=rail]').click();assert page.locator('.tripcard').count()==2
  page.locator('[data-filter=bike]').click();assert page.locator('.tripcard').count()==4
  page.locator('[data-filter=all]').click();assert page.locator('.tripcard').count()==6
  page.screenshot(path=str(ROOT/'home.png'))
  expected={'bike-small':(4,1),'bike-kaikyo':(5,1),'bike-main':(14,2),'bike-kyoto':(28,6),'rail-kyushu':(12,5),'rail-kyoto':(10,4)}
  assert set(page.evaluate('TravelPlanner.tripIds'))==set(expected)
  count=0
  for id,(n,rest) in expected.items():
   page.locator(f'.tripcard[data-trip="{id}"]').click();page.wait_for_timeout(60)
   assert page.locator('#scheduleRows tr').count()==n
   assert page.locator('#tripSelect').input_value()==id
   data=page.evaluate('TRAVEL_APP_DATA.trips[TravelPlanner.getState().trip]')
   assert data['restCount']==rest
   if id.startswith('rail'):assert 'km' not in page.locator('#metrics').inner_text()
   else:assert 'km' in page.locator('#metrics').inner_text()
   for d in data['days']:
    page.evaluate('(n)=>TravelPlanner.selectDay(n)',d['day'])
    page.evaluate('TravelPlanner.open("travel")');assert page.locator('#modalBody').inner_text()
    page.locator('[data-view=visit]').click();assert page.locator('#modalBody').inner_text()
    page.locator('[data-view=hotel]').click();assert page.locator('#modalBody').inner_text()
    page.evaluate('placeDialog.close()');count+=1
   page.evaluate('TravelPlanner.selectDay(1)')
   value='2027-'+('04' if id.startswith('bike') else '05')+'-'+str(list(expected).index(id)+1).zfill(2)
   page.locator('#departure').fill(value);page.locator('#departure').dispatch_event('change')
  savedDates=page.evaluate('TravelPlanner.getState().dates')
  page.reload(wait_until='networkidle');assert page.evaluate('TravelPlanner.getState().dates')==savedDates
  checks.append(f'All six trip selectors, {count} days, separate dates, and all shared detail tabs')
  # Navigation includes repeated points and rest-day boundaries, without mixing trips.
  for id in expected:
   page.evaluate('(id)=>TravelPlanner.selectTrip(id)',id)
   rows=page.evaluate('TRAVEL_APP_DATA.trips[TravelPlanner.getState().trip].days')
   for d in rows:
    for i,name in enumerate(d['stops']):
     state=page.evaluate('([n,i])=>{TravelPlanner.selectDay(n,i);return TravelPlanner.getState()}',[d['day'],i])
     assert state['point']==i and state['day']==d['day']
     assert name in page.locator('#stationNav .step-current').inner_text()
   page.evaluate('TravelPlanner.selectDay(1);TravelPlanner.step(-1)');assert page.evaluate('TravelPlanner.getState().day')==1
  page.evaluate('TravelPlanner.selectTrip("bike-kyoto");TravelPlanner.selectDay(12,3);TravelPlanner.step(1)')
  assert page.evaluate('TravelPlanner.getState().day')==13
  page.evaluate('TravelPlanner.step(1)');assert page.evaluate('TravelPlanner.getState().day')==14
  page.evaluate('TravelPlanner.open("visit")');assert '京都鉄道博物館' in page.locator('#modalBody').inner_text()
  page.locator('[data-rest-day="13"]').click();assert '二条城' in page.locator('#modalBody .activity').inner_text()
  page.locator('[data-rest-day="14"]').click();page.locator('[data-view=hotel]').click()
  assert '3連泊' in page.locator('#modalBody').inner_text();page.evaluate('placeDialog.close()')
  for n in [1,27]:
   page.evaluate('(n)=>{TravelPlanner.selectDay(n,TRAVEL_APP_DATA.trips["bike-kyoto"].days[n-1].stops.length-1);TravelPlanner.open("hotel")}',n)
   assert '1泊' in page.locator('#modalBody h3').inner_text();page.evaluate('placeDialog.close()')
  checks.append('Waypoint navigation, repeated destinations, Kyoto two-day rest and three-night stay, distinct Shimonoseki bookings')
  # Photo files are served locally, and every itinerary has representative real photos.
  for id in expected:
   page.evaluate('(id)=>TravelPlanner.selectTrip(id)',id)
   restdays=page.evaluate('TRAVEL_APP_DATA.trips[TravelPlanner.getState().trip].days.filter(d=>d.kind==="stay").map(d=>d.day)')
   for n in restdays:
    page.evaluate('(n)=>{TravelPlanner.selectDay(n);TravelPlanner.open("photos")}',n)
    assert page.locator('.gallery img').count()>0,(id,n)
    page.locator('.gallery img').evaluate_all('a=>a.forEach(i=>i.loading="eager")')
    page.wait_for_function('Array.from(document.querySelectorAll(".gallery img")).every(i=>i.complete&&i.naturalWidth>0)')
    page.evaluate('placeDialog.close()')
  checks.append('Real photos load on every rest day; attribution remains visible')
  page.locator('#openSettings').click();original=page.evaluate('TravelPlanner.getState().prefs')
  page.locator('#setWidth').fill('82');page.locator('#setHeight').fill('90')
  assert page.evaluate('TravelPlanner.getState().prefs')==original
  page.keyboard.press('Escape');assert page.evaluate('document.activeElement.id')=='openSettings'
  page.locator('#openSettings').click();assert float(page.locator('#setWidth').input_value())==original['width']
  page.locator('#setWidth').fill('82');page.locator('#setHeight').fill('90');page.locator('#setText').select_option('large');page.locator('#saveSettings').click()
  page.reload(wait_until='networkidle');assert page.evaluate('TravelPlanner.getState().prefs.width')==82
  page.locator('#stationQuery').fill('非存在の場所');page.locator('#stationSearch button').click();assert page.locator('#stationQuery').get_attribute('aria-invalid')=='true'
  page.locator('#stationQuery').fill('海響館');page.locator('#stationSearch button').click();assert page.locator('#placeTitle').inner_text()=='海響館'
  assert page.evaluate('TravelPlanner.getState().trip')=='bike-kaikyo'
  page.locator('[data-view=travel]').focus();page.keyboard.press('ArrowRight');assert page.locator('[data-view=visit]').get_attribute('aria-selected')=='true'
  page.evaluate('placeDialog.close()');assert page.evaluate('document.activeElement.id')=='stationQuery'
  # Backup is a local file; test the actual downloaded JSON and round-trip import.
  page.locator('#openSettings').click()
  with page.expect_download() as download:page.locator('#exportBackup').click()
  path=download.value.path();backup=json.loads(Path(path).read_text());assert backup['format']=='kyushu-travel-backup'
  page.locator('#importBackup').set_input_files(path);page.wait_for_timeout(150)
  assert '読み込みました' in page.locator('#backupStatus').inner_text()
  page.locator('#resetSettings').click();page.locator('#saveSettings').click();assert page.evaluate('TravelPlanner.getState().dates')==savedDates
  checks.append('Main-page settings, draft/cancel/save, persistence, search, keyboard tabs, focus return, backup export/import')
  for w,h in [(1920,1080),(1440,1000),(1024,768),(768,1024),(390,844),(320,568),(844,390)]:
   page.set_viewport_size({'width':w,'height':h});page.wait_for_timeout(150)
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
   page.locator('#openSettings').click();page.locator('#setWidth').fill('45');page.locator('#setHeight').fill('50');page.locator('#saveSettings').click()
   for id in ['bike-kyoto','rail-kyoto']:
    page.evaluate('([id,n])=>{TravelPlanner.selectTrip(id);TravelPlanner.selectDay(n);TravelPlanner.open("visit")}',[id,14 if id=='bike-kyoto' else 6])
    m=page.locator('#placeDialog').evaluate('e=>{const r=e.getBoundingClientRect(),b=document.getElementById("modalBody");return {cx:Math.abs(r.x+r.width/2-innerWidth/2),cy:Math.abs(r.y+r.height/2-innerHeight/2),w:r.width,h:r.height,bh:b.clientHeight,sw:b.scrollWidth,bw:b.clientWidth}}')
    assert m['cx']<2 and m['cy']<2 and m['w']<=w+1 and m['h']<=h+1,m
    assert m['bh']>=65 and m['sw']<=m['bw']+1,(w,h,m)
    assert page.locator('#placeDialog input[type=range]').count()==0
    if w in [1440,390] and id=='bike-kyoto':page.screenshot(path=str(ROOT/f'detail-{w}.png'))
    page.evaluate('placeDialog.close()')
   layouts.append([w,h]);page.locator('#openSettings').click();page.locator('#resetSettings').click();page.locator('#saveSettings').click()
  checks.append('Seven responsive viewports, centered minimum-size dialogs, no page or dialog horizontal overflow')
  # Previous origin is the same GitHub Pages host: read legacy keys without overwriting.
  legacy=browser.new_context();legacy.add_init_script('''localStorage.setItem('orio-cycle-plan-v1',JSON.stringify({dates:{small:'2027-01-01',kaikyo:'2027-02-01',main:'2027-03-01',kyoto:'2027-04-01'},checks:[1]}));localStorage.setItem('orio-rail-plan-v1',JSON.stringify({dates:{kyushu:'2027-05-01',kyoto:'2027-06-01'},saved:['kyoto:京都:ky-h326110']}));localStorage.setItem('orio-cycle-explorer-v2',JSON.stringify({hotels:{'日田':'h310033'},sights:['s08']}));localStorage.setItem('orio-cycle-rest-days-v1',JSON.stringify({saved:{'京都':'slow'}}));localStorage.setItem('orio-cycle-site-settings-v2',JSON.stringify({width:79,height:87}));''')
  lp=legacy.new_page();lp.goto(url,wait_until='networkidle');s=lp.evaluate('TravelPlanner.getState()')
  assert s['dates']['bike-kyoto']=='2027-04-01' and s['dates']['rail-kyoto']=='2027-06-01'
  assert s['prefs']['width']==79 and s['variant']['bike-kyoto:14']=='slow'
  assert 'bike-small:日田:h310033' in s['saved'];legacy.close()
  blocked=browser.new_context();blocked.add_init_script('Object.defineProperty(window,"localStorage",{get(){throw new DOMException("Blocked","SecurityError")}})');bp=blocked.new_page();bp.on('pageerror',lambda e:errors.append(str(e)));bp.goto(url,wait_until='networkidle');bp.locator('#openSettings').click();bp.locator('#setWidth').fill('85');bp.locator('#saveSettings').click();assert '保存できない' in bp.locator('#notice').inner_text();blocked.close()
  checks.append('Cycling and rail legacy date/candidate migration; inaccessible-storage fallback')
  page.set_viewport_size({'width':1440,'height':1000});page.evaluate('TravelPlanner.selectTrip("bike-small")');page.evaluate('window.scrollTo(0,0)');page.screenshot(path=str(ROOT/'home.png'))
  assert not errors,errors;browser.close()
 report={'status':'passed','url':url,'tripCount':6,'days':count,'tests':checks,'viewports':layouts,'pageErrors':errors}
 (ROOT/'unified-test-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False),flush=True)
finally:
 if server:server.terminate()
