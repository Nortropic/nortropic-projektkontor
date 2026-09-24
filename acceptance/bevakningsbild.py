"""Synthetic read-only AP08 watch projection contract; no live native queries."""
import json
from pathlib import Path
import subprocess

SCRIPT = r'''
import copy, hashlib, json, os, pathlib, subprocess, sys, tempfile
from datetime import datetime
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path('tools').resolve()))
import agarbild
import bevakningsbild as m

def canon(x):return json.dumps(x,sort_keys=True,separators=(',', ':'),ensure_ascii=True,allow_nan=False).encode()
def sha(raw):return hashlib.sha256(raw).hexdigest()
def put(p,obj):
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(obj,sort_keys=True)+'\n');return sha(p.read_bytes())
def read(p):return json.loads(p.read_text())
def expect_error(fn):
 try:fn()
 except (ValueError,OSError):return
 raise AssertionError('Unsafe operation accepted')
def native():
 return {'observed_at':'2024-01-03T10:00:00+00:00','obligation':'office-python-temporal',
 'paused':False,'note':'AP10 explicit operator resume','limited_actions':False,'remaining_actions':0,
 'schedule':{'calendars':[{'hour':[{'start':9,'end':9,'step':1}],
  'minute':[{'start':0,'end':0,'step':1}],'second':[{'start':0,'end':0,'step':1}],
  'year':[],'month':[{'start':1,'end':12,'step':1}],
  'day_of_month':[{'start':1,'end':31,'step':1}],
  'day_of_week':[{'start':0,'end':6,'step':1}],'comment':None}],
  'time_zone_name':'Europe/Stockholm','intervals':[],'cron_expressions':'[]',
  'skip':[],'start_at':None,'end_at':None,'jitter':None},
 'policy':{'overlap':2,'catchup_window':'22:00:00','pause_on_failure':False},
 'next_action_times':['2024-01-04T08:00:00+00:00'],'actions':2,
 'missed_catchup':0,'skipped_overlap':0,'running':[],'recent':[],
 'meaning':'Dated native schedule observation, not successful intake'}
N=native();G='2024-01-03T10:01:00+00:00'
def work(v,title):return next(x for x in v['work'] if x['title']==title)
def body(v):return json.dumps(v,ensure_ascii=False).lower()
def project(n,l,r,g=G):
 original=copy.deepcopy((n,l,r));out=m.view(n,l,r,g)
 assert original==(n,l,r),'Pure projection mutated its inputs'
 agarbild.validate(out)
 assert out['generated_at']==g and {'native','latest','reviewed'} <= {e['id'] for e in out['evidence']}
 return out

with tempfile.TemporaryDirectory(dir='.scratch') as td:
 base=pathlib.Path(td).resolve();rt=base/'Nortropic Runtime';rt.mkdir()
 releases=rt/'.runtime/ap10/releases';rel=releases/('b'*40+'-'+'c'*40)
 code=rel/'runtime/runtime/obligation.py';code.parent.mkdir(parents=True);code.write_text('# frozen synthetic code; never execute')
 wh=put(rel/'context/watch.json',{'schema':1,'case_id':'SYNTHETIC-CASE','first_treated_at':'2023-01-01T00:00:00Z','old_gaps':['Preserved synthetic old gap'],'source_map':{}})
 cfg={'schema':1,'host_root':str(rt),'office_root':str(base/'nortropic-projektkontor'),
 'database':str(rt/'.runtime/runtime.sqlite'),'runtime_revision':'b'*40,'office_revision':'c'*40,
 'files':{'runtime/runtime/obligation.py':sha(code.read_bytes()),'context/watch.json':wh},'instruction_guards':{}}
 cp=rel/'config.json';ch=put(cp,cfg);active=rt/'.runtime/ap10/active.json';put(active,{'config':str(cp),'sha256':ch})
 exe=rt/'.runtime/temporal-venv/bin/python';exe.parent.mkdir(parents=True);exe.write_text('synthetic launcher never executed')
 rounds=rt/'.runtime/ap10/rounds';rounds.mkdir()
 def round_data(run,when,reviewed=True,complete=True,origin=None):
  home=rounds/run
  packet={'schema':1,'observed_at':when,'sources':[{'id':'temporal-1.33.0',
   'url':'https://example.invalid/synthetic','status':'available' if complete else 'unavailable',
   'observed_at':when,'published_at':'2023-12-01T00:00:00Z',
   'sha256':sha(b'Synthetic vendor evidence') if complete else None,
   'path':'note.raw' if complete else None,'error':None if complete else 'unavailable'}],'local':[],
   'versions':{'python':'3.12.13','temporalio':'1.33.0','runtime_revision':'b'*40,
    'office_revision':'c'*40,'active_config_sha256':ch},'complete':complete,
   'fingerprint':None,'same_controlled_basis':bool(origin),
   'coverage':'Synthetic selected-source comparison only'}
  if complete:
   packet['fingerprint']=sha(canon({'versions':packet['versions'],'sources':[
    {k:r[k] for k in ('id','status','sha256')} for r in packet['sources']],'local':[]}))
  ph=put(home/'intake/data/packet.json',packet)
  ans={'case_id':'SYNTHETIC-CASE','packet_sha256':ph,'decision':'retain',
   'vendor':'<img src=x onerror=alert(1)> is evidence text',
   'local':'Selected local path only','judgment':'Retain scoped use; old gap remains',
   'authority':'No upgrade or source changes','evidence':['temporal-1.33.0'],'contradictions':[],'proposal':None}
  reviewmeta=None;reviewtime=None
  if reviewed and origin is None:
   ah=put(home/'analysis/result.json',{'completed':True,'process_group_removed':True,
    'provider':{'valid_terminal':True,'thread_id':'analysis-'+run,'usage':None},'elapsed_seconds':1,'answer':ans})
   rh=put(home/'review/result.json',{'completed':True,'process_group_removed':True,
    'provider':{'valid_terminal':True,'thread_id':'review-'+run,'usage':None},'elapsed_seconds':1,
    'answer':{'case_id':ans['case_id'],'packet_sha256':ph,'assessment_sha256':sha(canon(ans)),
             'verdict':'approved','reason':'Synthetic scoped review','blockers':[]}})
   reviewmeta={'analysis_thread_id':'analysis-'+run,'review_thread_id':'review-'+run,
    'assessment_sha256':sha(canon(ans)),'analysis_result_sha256':ah,'review_result_sha256':rh}
   reviewtime=when
   stamp=datetime.fromisoformat(when.replace('Z','+00:00')).timestamp()
   os.utime(home/'review/result.json',(stamp,stamp))
  if origin:
   reviewmeta=copy.deepcopy(origin['report']['review']);reviewtime=origin['report']['reviewed_at']
  report={'schema':1,'completed':True,'obligation':'office-python-temporal','run_id':run,
   'case_id':ans['case_id'],'packet_sha256':ph,'context_sha256':'d'*64,'observed_at':when,
   'first_treated_at':'2023-01-01T00:00:00Z','reported_at':when,'reviewed':reviewed,
   'reviewed_at':reviewtime,'decision':'retain' if reviewed else 'insufficient',
   'reasoning':{k:ans[k] for k in ('vendor','local','judgment','authority')},
   'evidence':['temporal-1.33.0'],'contradictions':[],'old_gaps':['Preserved synthetic old gap'],
   'reused_from':str(pathlib.Path(origin['locator']).parent.parent) if origin else None,
   'review_origin':origin['report']['review_origin'] if origin else (str(home) if reviewed else None),
   'review':reviewmeta,'ap05':{},'ap06':None,'action_executed':False,'publication':False,
   'runtime_revision':'b'*40,'office_revision':'c'*40,'active_config_sha256':ch,
   'limitations':['Selected observations, not live status or comprehensive assurance']}
  rp=home/'report/result.json';put(rp,report)
  return {'report':report,'packet':packet,'integrity':'available','locator':str(rp)}
 good=round_data('11111111-1111-1111-1111-111111111111','2024-01-02T09:00:00+00:00')
 failed=round_data('22222222-2222-2222-2222-222222222222','2024-01-03T09:00:00+00:00',False,False)
 failed['report']['limitations']=['Later intake incomplete; no accepted review'];put(pathlib.Path(failed['locator']),failed['report'])
 with patch('builtins.open',side_effect=AssertionError('view I/O')),patch('os.open',side_effect=AssertionError('view I/O')),patch('subprocess.run',side_effect=AssertionError('view process')):
  picture=project(N,failed,good)
 assert work(picture,'Senaste observation')['state'] in ('waiting','unknown')
 assert work(picture,'Senaste observation')['observed_at']==failed['report']['observed_at']
 assert work(picture,'Senast granskade besked')['observed_at']==good['report']['reviewed_at']
 html=agarbild.render(picture);assert '<img src=x' not in html and '&lt;img' in html
 assert 'Preserved synthetic old gap' in html and picture['owner_decision']['needed']!='yes'
 assert 'inaktuell' in body(project(N,good,good))
 unavailable=copy.deepcopy(good);unavailable['integrity']='unavailable'
 assert work(project(N,unavailable,good),'Senaste observation')['state'] in ('waiting','unknown')
 proposal=copy.deepcopy(good);proposal['report']['decision']='propose_action'
 proposal['report']['ap06']={'status':'draft','mechanical_complete':False,
  'package':{'brief':'Synthetic owner decision: authorize only a scoped compatibility investigation',
             'task_draft':{},'gaps':[{'code':'action_authority_missing','subject':'brief'}]}}
 proposed=project(N,proposal,proposal)
 assert proposed['owner_decision']['needed']=='yes' and proposed['next_action']['authority']=='proposed'
 for note,paused in [('PAUSED: in-flight round may finish',True),('STOPPED: explicit stop',True)]:
  n=copy.deepcopy(N);n.update(note=note,paused=paused)
  assert ('stopp' if note.startswith('STOPPED') else 'paus') in body(project(n,failed,good))
 for empty in ('[]',[]):
  for note,paused in [('AP10 explicit operator resume',False),('PAUSED: in-flight round may finish',True),('STOPPED: explicit stop',True)]:
   n=copy.deepcopy(N);n['schedule']['cron_expressions']=empty;n.update(note=note,paused=paused)
   assert work(project(n,failed,good),'Schema')['state']!='unknown'
 for invalid in ('arbitrary', '["0 * * * *"]', ['0 * * * *'], ' [] ', None, 'missing'):
  n=copy.deepcopy(N)
  if invalid=='missing':del n['schedule']['cron_expressions']
  else:n['schedule']['cron_expressions']=invalid
  assert work(project(n,failed,good),'Schema')['state']=='unknown'
 test=copy.deepcopy(N);test['limited_actions']=True;test['remaining_actions']=1
 test['schedule']['calendars'][0]['year']=[{'start':2024,'end':2024,'step':1}]
 assert 'prov' in body(project(test,good,good))
 unknown={'obligation':'office-python-temporal','unavailable':True,'observed_at':N['observed_at'],'reason':'unavailable'}
 assert work(project(unknown,failed,good),'Schema')['state']=='unknown'
 later=copy.deepcopy(N);later['recent']=[{'scheduled_at':'2024-01-03 09:29:00+00:00',
  'started_at':'2024-01-03 09:30:00+00:00','action':{'workflow_id':'watch','first_execution_run_id':'33333333-3333-3333-3333-333333333333'}}]
 assert work(project(later,good,good),'Senaste observation')['state'] in ('waiting','unknown')

 seen=[]
 def reader(runtime_root,config):
  assert pathlib.Path(runtime_root)==rt and config['config_sha256']==ch and pathlib.Path(config['directory'])==rel
  seen.append(1);return copy.deepcopy(N)
 before={str(p):p.read_bytes() for p in rt.rglob('*') if p.is_file()}
 collected=m.collect(rt,status_reader=reader);assert set(collected)=={'native','latest','reviewed'} and len(seen)==1
 assert collected['latest']['report']['run_id']==failed['report']['run_id']
 assert collected['reviewed']['report']['run_id']==good['report']['run_id']
 assert collected['reviewed']['integrity']=='available'
 reused=round_data('44444444-4444-4444-4444-444444444444','2024-01-03T09:40:00+00:00',origin=good)
 c=m.collect(rt,status_reader=reader);assert c['reviewed']['report']['run_id']==reused['report']['run_id']
 assert work(project(c['native'],c['latest'],c['reviewed']),'Senast granskade besked')['observed_at']==good['report']['reviewed_at']
 # Exact default query only, with a poisoned ambient import path removed.
 def run(argv,**kw):
  assert list(argv)==[str(exe),'-B','-m','runtime.obligation','status']
  assert pathlib.Path(kw['cwd'])==rel/'runtime' and kw['timeout']==20 and not kw.get('shell',False)
  assert kw['capture_output'] is True and kw['text'] is True
  assert kw['env']['NR_HOST_ROOT']==str(rt) and kw['env']['NR_CONFIG_SHA256']==ch
  assert 'PYTHONPATH' not in kw['env'] and 'PYTHONHOME' not in kw['env']
  return subprocess.CompletedProcess(argv,0,json.dumps(N),'')
 with patch.dict(os.environ,{'PYTHONPATH':'UNTRUSTED','PYTHONHOME':'UNTRUSTED'}),patch('subprocess.run',side_effect=run) as query:
  assert m.collect(rt)['native']['obligation']=='office-python-temporal';assert query.call_count==1
 with patch('subprocess.run',side_effect=subprocess.TimeoutExpired('status',20)):
  timed=m.collect(rt);assert timed['native']['unavailable'] is True and timed['reviewed'] is not None
 # Changes to bound bytes/summary, missing review and symlink escape deny review.
 origin=pathlib.Path(good['locator']).parent.parent;rp=origin/'review/result.json';raw=rp.read_bytes()
 rp.write_text('{}');c=m.collect(rt,status_reader=reader);assert c['reviewed'] is None;rp.write_bytes(raw)
 reportpath=pathlib.Path(good['locator']);rawreport=reportpath.read_bytes();changed=read(reportpath);changed['reasoning']['judgment']='UNREVIEWED CHANGE';put(reportpath,changed)
 assert m.collect(rt,status_reader=reader)['reviewed'] is None;reportpath.write_bytes(rawreport)
 pp=origin/'intake/data/packet.json';rawpacket=pp.read_bytes();pp.write_text('{}')
 assert m.collect(rt,status_reader=reader)['reviewed'] is None;pp.write_bytes(rawpacket)
 rp.unlink();rp.symlink_to(base/'outside-review');(base/'outside-review').write_bytes(raw)
 assert m.collect(rt,status_reader=reader)['reviewed'] is None;rp.unlink();rp.write_bytes(raw)
 # Unverified code/config must never reach even the injected query seam.
 code.write_text('changed unreviewed code');n=len(seen)
 try:bad=m.collect(rt,status_reader=reader);assert bad['native']['unavailable'] is True
 except ValueError:pass
 assert len(seen)==n;code.write_bytes(before[str(code)])
 alias=base/'runtime-alias';alias.symlink_to(rt,target_is_directory=True)
 n=len(seen)
 try:bad=m.collect(alias,status_reader=reader);assert bad['native']['unavailable'] is True
 except ValueError:pass
 assert len(seen)==n
 for name,data in before.items():assert pathlib.Path(name).read_bytes()==data
 # Output remains private/exclusive and uses existing AP08, not a parallel renderer.
 out=base/'picture';snapshot={'native':N,'latest':failed,'reviewed':good}
 with patch.object(m,'collect',return_value=snapshot):assert m.main([str(out)])==0
 assert {p.name for p in out.iterdir()}=={'input.json','index.html'}
 assert out.stat().st_mode&0o777==0o700
 for p in out.iterdir():assert p.stat().st_mode&0o777==0o600
 assert (out/'index.html').read_text().rstrip('\n')==agarbild.render(read(out/'input.json')).rstrip('\n')
 old=(out/'index.html').read_bytes()
 with patch.object(m,'collect',side_effect=AssertionError('Existing output must reject before collection')):
  assert m.main([str(out)])==2
 assert (out/'index.html').read_bytes()==old
 parent=base/'output-alias';parent.symlink_to(base,target_is_directory=True)
 with patch.object(m,'collect',side_effect=AssertionError('Symlink output must reject before collection')):
  assert m.main([str(parent/'new-picture')])==2
print(json.dumps({'passed':True,'checks':['AP08 dated latest versus separately reviewed history',
 'native actual status format including test/paused/stopped and missing later report',
 'exact frozen read-only status query and no working fallback',
 'tampered packet/review/report or symlink cannot become reviewed',
 'private exclusive inert output using existing AP08']}))
'''


def verify(candidate):
    from runtime.profile import sandbox_command, environment
    result = subprocess.run(
        sandbox_command(Path(candidate), ['/opt/homebrew/bin/python3.12', '-I', '-B', '-c', SCRIPT]),
        env=environment(), capture_output=True, text=True, timeout=120,
    )
    if result.returncode:
        return {'passed': False, 'reason': 'AP10 dated watch picture contract failed',
                'stderr': result.stderr[-6000:]}
    try:
        return json.loads(result.stdout)
    except ValueError:
        return {'passed': False, 'reason': 'Missing host result'}
