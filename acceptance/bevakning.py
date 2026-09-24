"""Frozen Office policy acceptance; synthetic inputs, native read-only candidate."""
import json
from pathlib import Path
import subprocess


SCRIPT = r'''
import ast, copy, hashlib, importlib, json, os, pathlib, tempfile
from datetime import datetime, timezone
from unittest.mock import patch
import sys
sys.path.insert(0, str(pathlib.Path('tools').resolve()))
import bevakningsunderlag as intake
import change_assessment as ap05
import assignment_preparation as ap06

EXPECTED_FILES = ('runtime/worker.py','runtime/workflow.py','runtime/activities.py',
 'runtime/run.py','runtime/service.py','runtime/profile.py',
 'config/temporal-probe-requirements.lock','docs/runtime-v0.1.md',
 'runtime/daemon.py','runtime/shared.py','runtime/release.py',
 'runtime/private_workflow.py','runtime/private_activity.py',
 'runtime/private_stage.py','runtime/obligation.py')
assert tuple(intake.LOCAL_FILES) == EXPECTED_FILES
# Only the named source list and dated-label parser may alter existing intake.
intake_tree=ast.parse(pathlib.Path('tools/bevakningsunderlag.py').read_text())
for node in intake_tree.body:
 if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='LOCAL_FILES' for t in node.targets):
  node.value=ast.Constant(value=None)
 if isinstance(node,ast.FunctionDef) and node.name=='_python_index':node.body=[ast.Pass()]
assert hashlib.sha256(ast.dump(intake_tree,include_attributes=False).encode()).hexdigest()=='71e3c8762b891b23ff789ae53865f3d06beb18a0d2afee8542e29171ab2a2b06'
def canonical(x): return json.dumps(x,sort_keys=True,separators=(',', ':'),ensure_ascii=True,allow_nan=False).encode()
def digest(x): return hashlib.sha256(x).hexdigest()
def write(p, value):
 p.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
 with p.open('x') as f: json.dump(value,f,sort_keys=True);f.write('\n')
 p.chmod(0o600)
def read(p): return json.loads(p.read_text())
def expect_error(fn):
 try: fn()
 except (ValueError,OSError): return
 raise AssertionError('Unsafe or invalid input accepted')
V={'python':'3.12.13','temporalio':'1.33.0','runtime_revision':'b'*40,
 'office_revision':'c'*40,'active_config_sha256':'a'*64}
variant={'vendor':b'Vendor states: only selected optional integration changes.',
         'local':b'Explicit local core path. No optional integration.',
         'missing':False}
calls=[]
def fake_collect(output, local_roots, versions, previous=None, fetcher=None):
 # Separate synthetic source generator, preserving the real packet contract.
 assert set(local_roots)=={'active','working'} and versions==V
 calls.append(str(output));output=pathlib.Path(output);output.mkdir(mode=0o700)
 timestamp=datetime.now(timezone.utc).isoformat()
 packet={'schema':1,'observed_at':timestamp,'sources':[],'local':[],
  'versions':copy.deepcopy(versions),'complete':not variant['missing'],
  'fingerprint':None,'same_controlled_basis':False,'coverage':'Synthetic selected lines; not exhaustive'}
 ext=[('python-index',b'INDEX-ONLY-CANARY-PYTHON'),('temporal-index',b'INDEX-ONLY-CANARY-SDK'),
      ('python-3.12.13',b'Python synthetic baseline'),('temporal-1.33.0',variant['vendor'])]
 entries=[('sources',identity,data) for identity,data in ext]
 entries += [('local',root+':'+name,variant['local'] if root=='working' and name==EXPECTED_FILES[0]
             else ('synthetic '+root+' '+name).encode()) for root in ('active','working') for name in EXPECTED_FILES]
 for i,(group,identity,data) in enumerate(entries):
  missing=variant['missing'] and identity=='temporal-1.33.0'
  rel='record-%02d.raw'%i
  if not missing:
   (output/rel).write_bytes(data);(output/rel).chmod(0o600)
  record={'id':identity,'status':'unavailable' if missing else 'available','observed_at':timestamp,
   'sha256':None if missing else digest(data),'path':None if missing else rel,'error':'source_unavailable' if missing else None}
  if group=='sources':record.update(url='https://example.invalid/synthetic/'+identity,published_at='2020-01-01T00:00:00Z')
  packet[group].append(record)
 if packet['complete']:
  basis={'versions':versions,**{g:sorted([{k:r[k] for k in ('id','status','sha256')} for r in packet[g]],key=lambda x:x['id']) for g in ('sources','local')}}
  packet['fingerprint']=digest(canonical(basis))
  packet['same_controlled_basis']=isinstance(previous,dict) and previous.get('complete') is True and previous.get('fingerprint')==packet['fingerprint']
 write(output/'packet.json',packet)
 return packet

with tempfile.TemporaryDirectory(dir='.scratch') as td:
 root=pathlib.Path(td).resolve();context=root/'context';context.mkdir(mode=0o700)
 case={'schema':1,'id':'SYNTHETIC-AP09-CASE','created_at':'2021-01-01T00:00:00Z',
  'sources':[{'id':'vendor','title':'Synthetic vendor','version':'original',
   'path':'vendor.txt','sha256':digest(variant['vendor']),'size':len(variant['vendor'])},
   {'id':'local','title':'Synthetic local','version':'original','path':'local.txt',
    'sha256':digest(variant['local']),'size':len(variant['local'])},
   {'id':'old-transform','title':'Earlier transformed evidence','version':'original',
    'path':'old.txt','sha256':'d'*64,'size':17}],
  'claims':[{'id':'supplier','kind':'fact','text':'Selected vendor claim','reason':'Selected source',
             'standing':'historical scoped claim','sources':['vendor']},
            {'id':'applicability','kind':'judgment','text':'Retain scoped use','reason':'Selected local use',
             'standing':'old gaps stay open','sources':['vendor','local','old-transform']}],
  'actions':[{'id':'observe','text':'Observe again','reason':'Named scope','claims':['applicability'],
   'authority':{'status':'not_established','scope':'Fixture observation is not authority','sources':[]}}],
  'next_action':'observe'}
 watch={'schema':1,'case_id':case['id'],'first_treated_at':'2021-02-03T04:05:06Z',
  'old_gaps':['Synthetic graceful-drain guarantee remains unproven.'],
  'source_map':{'vendor':'temporal-1.33.0','local':'working:runtime/worker.py','old-transform':None}}
 write(context/'case.json',case);write(context/'watch.json',watch)
 (context/'authority.md').write_text('Synthetic current AP10 mandate: selected observation and assessment only; no upgrade.')
 (context/'prior-decision.md').write_text('Synthetic independently reviewed AP09 retain within scope; stronger shutdown evidence absent.')
 (context/'UNSELECTED-SECRET.json').write_text('NEVER-COPY-THIS-CONTEXT')
 source_before={p.name:p.read_bytes() for p in context.iterdir()}
 context_hash=digest(canonical({p.name:digest(p.read_bytes()) for p in (context/'case.json',context/'watch.json',context/'authority.md',context/'prior-decision.md')}))
 roots={'active':root/'active','working':root/'working'}
 for p in roots.values():
  p.mkdir()
  for name in EXPECTED_FILES:
   target=p/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_text('Synthetic local fixture')
 # Public intake API: real source-index label form, using synthetic responses.
 py=intake.PYTHON_INDEX;sdk=intake.TEMPORAL_INDEX
 dated={py:b'<a href="/downloads/release/python-31213/">Python 3.12.13 - March 3, 2026</a><a href="/downloads/release/python-31214/">Python 3.12.14 - Aug. 12, 2026</a>',
  sdk:json.dumps([{'tag_name':'1.33.0','draft':False,'prerelease':False}]).encode(),
  'https://www.python.org/downloads/release/python-31213/':b'<h1>Python 3.12.13</h1>',
  'https://www.python.org/downloads/release/python-31214/':b'<h1>Python 3.12.14</h1>',
  'https://api.github.com/repos/temporalio/sdk-python/releases/tags/1.33.0':json.dumps({'tag_name':'1.33.0','draft':False,'prerelease':False}).encode()}
 actual=intake.collect(root/'dated-labels',roots,V,fetcher=lambda u:dated[u])
 assert actual['complete'] and {s['id'] for s in actual['sources']}=={'python-index','temporal-index','python-3.12.13','python-3.12.14','temporal-1.33.0'}
 dated[py]=dated[py].replace(b'Python 3.12.14 -',b'Python 3.12.15 -')
 mismatch=intake.collect(root/'mismatched-label',roots,V,fetcher=lambda u:dated[u])
 assert not mismatch['complete'] and next(s for s in mismatch['sources'] if s['id']=='python-index')['status']=='unavailable'
 count=[0]
 with patch.object(intake,'collect',side_effect=fake_collect),patch.object(ap05,'assess',wraps=ap05.assess) as assess_spy,patch.object(ap06,'prepare',wraps=ap06.prepare) as prep_spy:
  m=importlib.import_module('bevakning')
  def new_round(prior=None,ctx=context):
   count[0]+=1;home=root/('round-%02d'%count[0]);(home/'intake').mkdir(parents=True,mode=0o700)
   if prior is not None:write(home/'intake/previous.json',prior)
   before=len(calls);result=m.prepare(home/'intake/data',roots,V,prior,ctx)
   assert len(calls)==before+1,'Every round must observe external AND local basis again'
   assert result['completed'] is True and type(result['needs_model']) is bool
   write(home/'intake/result.json',result)
   return home,result
  def packet(home):return read(home/'intake/data/packet.json')
  def phash(home):return digest((home/'intake/data/packet.json').read_bytes())
  def analysis(home,decision='retain'):
   return {'case_id':case['id'],'packet_sha256':phash(home),'decision':decision,
    'vendor':'Scoped supplier assertion, no global guarantee.',
    'local':'Selected active and working paths observed; installation is not use.',
    'judgment':'Retain within scope; old evidence gap remains.',
    'authority':'Observation only; no upgrade or source write permitted.',
    'evidence':['temporal-1.33.0','working:runtime/worker.py'],
    'contradictions':[],'proposal':None}
  def results(home,a=None,verdict='approved',same_thread=False,review=True):
   a=analysis(home) if a is None else a
   for role,answer,thread in [('analysis',a,'analysis-'+home.name),('review',
    {'case_id':case['id'],'packet_sha256':phash(home),'assessment_sha256':digest(canonical(a)),
     'verdict':verdict,'reason':'Synthetic independent substantive review',
     'blockers':[] if verdict=='approved' else ['Unsupported conclusion']},
    ('analysis-' if same_thread else 'review-')+home.name)]:
    if role=='review' and not review:continue
    write(home/role/'result.json',{'completed':True,'answer':answer,
     'provider':{'valid_terminal':True,'thread_id':thread,'usage':None},
     'elapsed_seconds':1.0,'process_group_removed':True})
   return a
  def finish(home,config_change=None):
   (home/'report').mkdir(exist_ok=True,mode=0o700)
   config={'runtime_revision':V['runtime_revision'],'office_revision':V['office_revision'],
     'config_sha256':V['active_config_sha256'],'directory':str(root/'release'),'files':{}}
   config.update(config_change or {})
   request={'run_id':home.name,'workflow_id':'synthetic','started_at':packet(home)['observed_at'],
    'obligation':'office-python-temporal','config_sha256':V['active_config_sha256'],
    'role':'report','seconds':60,'outcomes':{'analysis':{'completed':True},'review':{'completed':True}}}
   result=m.finish(home,request,config)
   assert not (home/'report/result.json').exists(),'Only Runtime writes final result'
   assert result['case_id']==case['id'] and result['first_treated_at']==watch['first_treated_at']
   assert result['packet_sha256']==phash(home) and result['context_sha256']==context_hash
   assert result['old_gaps']==watch['old_gaps'] and result['action_executed'] is False and result['publication'] is False
   assert result['observed_at']==packet(home)['observed_at'] and result['reported_at'] and result['limitations']
   return result
  def prior(home,report):
   write(home/'report/result.json',report)
   return {'home':str(home),'report':report,'packet':packet(home)}

  first,state=new_round();assert state['needs_model'] is True
  prepared=read(first/'intake/data/prepared.json');assert prepared['packet_sha256']==phash(first) and prepared['context_sha256']==context_hash
  ap=read(first/'intake/data/ap05.json');statuses={s['id']:s['status'] for s in ap['source_checks']}
  assert statuses=={'vendor':'ok','local':'ok','old-transform':'not_checked'}
  assert assess_spy.call_count and ap['judgments'][0]['source_check']=='needs_reassessment'
  a=results(first);good=finish(first)
  assert good['reviewed'] is True and good['decision']=='retain' and good['reasoning']['vendor']==a['vendor']
  assert good['review']['analysis_thread_id']!=good['review']['review_thread_id']
  assert good['review']['assessment_sha256']==digest(canonical(a))
  assert good['review']['analysis_result_sha256']==digest((first/'analysis/result.json').read_bytes())
  assert good['review']['review_result_sha256']==digest((first/'review/result.json').read_bytes())
  assert good['review_origin']==str(first) and good['reused_from'] is None and good['reviewed_at']
  last=prior(first,good);frozen=copy.deepcopy(last)
  repeated,rs=new_round(last);assert rs['needs_model'] is False
  reused=finish(repeated);assert reused['reviewed'] is True and reused['reused_from']==str(first)
  assert reused['review_origin']==str(first) and reused['reviewed_at']==good['reviewed_at']
  assert reused['reasoning']==good['reasoning'] and last==frozen
  # A second reuse proves the preserved lineage is practical, not a one-use flag.
  chain=prior(repeated,reused);third,ts=new_round(chain);assert ts['needs_model'] is False
  assert finish(third)['review_origin']==str(first)

  old=variant['vendor'];variant['vendor']=b'Changed vendor-only assertion'
  ext,es=new_round(last);assert es['needs_model'] is True
  assert read(ext/'intake/data/ap05.json')['facts'][0]['source_check']=='needs_reassessment'
  variant['vendor']=old
  old=variant['local'];variant['local']=b'Changed local-only usage'
  loc,ls=new_round(last);assert ls['needs_model'] is True;variant['local']=old
  variant['missing']=True;missing,ms=new_round(last);assert ms['needs_model'] is True
  results(missing);assert finish(missing)['reviewed'] is False
  honest,hs=new_round(last);results(honest,analysis(honest,'insufficient'))
  honest_result=finish(honest);assert honest_result['reviewed'] is True and honest_result['decision']=='insufficient'
  honest_prior=prior(honest,honest_result);variant['missing']=False
  _,hps=new_round(honest_prior);assert hps['needs_model'] is True
  # A bare reviewed flag, changed context, and damaged bound review never allow reuse.
  damaged=copy.deepcopy(last);damaged['report']['decision']='propose_action'
  _,ds=new_round(damaged);assert ds['needs_model'] is True
  other=root/'changed-context';other.mkdir();write(other/'case.json',case)
  newer=copy.deepcopy(watch);newer['old_gaps'].append('Additional unresolved question');write(other/'watch.json',newer)
  for name in ('authority.md','prior-decision.md'):(other/name).write_bytes((context/name).read_bytes())
  _,cs=new_round(last,other);assert cs['needs_model'] is True
  original_review=(first/'review/result.json').read_bytes();(first/'review/result.json').write_text('{}')
  _,broken=new_round(chain);assert broken['needs_model'] is True
  (first/'review/result.json').write_bytes(original_review)

  for mode in ('missing','rejected','same_thread','hash','analysis_failed','thread_missing','truthy_review','contradiction','wrong_config'):
   home,_=new_round();ans=analysis(home)
   if mode=='contradiction':ans['contradictions']=['Unresolved conflict'];ans['decision']='retain'
   results(home,ans,verdict='rejected' if mode=='rejected' else 'approved',
           same_thread=mode=='same_thread',review=mode!='missing')
   if mode in ('hash','analysis_failed','thread_missing','truthy_review'):
    p=home/('review' if mode in ('hash','truthy_review') else 'analysis')/'result.json';obj=read(p)
    if mode=='hash':obj['answer']['assessment_sha256']='0'*64
    elif mode=='analysis_failed':obj['completed']=False
    elif mode=='thread_missing':obj['provider']['thread_id']=''
    else:obj['completed']=1
    p.write_text(json.dumps(obj))
   failure=finish(home,{'office_revision':'e'*40} if mode=='wrong_config' else None)
   assert failure['reviewed'] is False and failure['decision']=='insufficient' and failure['reviewed_at'] is None

  proposed,_=new_round();ans=analysis(proposed,'propose_action')
  ans['proposal']={'text':'Ask for an isolated dependency compatibility investigation',
   'reason':'A scoped incompatibility needs an owner decision, not an automatic upgrade',
   'requirement':'Compare the named API before any dependency change',
   'observable':'A separate authorized synthetic fixture demonstrates the API outcome',
   'claims':['applicability']}
  results(proposed,ans);before=prep_spy.call_count;proposal_report=finish(proposed)
  assert proposal_report['reviewed'] is True and proposal_report['decision']=='propose_action'
  assert prep_spy.call_count==before+1 and proposal_report['ap06']['status']=='draft'
  draft=proposal_report['ap06'];assert not draft['mechanical_complete'] and draft['package']['task_draft']=={}
  gaps={g['code'] for g in draft['gaps']};assert 'action_authority_missing' in gaps and 'task_field_missing' in gaps
  assert 'Compare the named API' in draft['package']['brief']
  assert draft['private']['case']['sources']==case['sources'] and draft['private']['case']['claims']==case['claims']
  assert (proposed/'report/ap06.json').is_file()
  proposal_prior=prior(proposed,proposal_report);before=prep_spy.call_count
  proposal_repeat,prs=new_round(proposal_prior);assert prs['needs_model'] is False
  replay=finish(proposal_repeat);assert replay['reviewed'] is True and replay['ap06']==draft
  assert prep_spy.call_count==before,'Reused reviewed proposal must not create another action draft'

  # Selected-copy and exact-review-input boundary; no execution/network/other context.
  for role in ('analysis','review'):
   ws=root/('workspace-'+role);ws.mkdir(mode=0o700)
   m.workspace(ws,first,context,role)
   inp=read(ws/'INPUT.json');assert inp['packet_sha256']==phash(first) and inp['case_id']==case['id']
   assert any(b'Synthetic current AP10 mandate' in p.read_bytes() for p in ws.rglob('*') if p.is_file())
   assert any(b'Synthetic independently reviewed AP09 retain' in p.read_bytes() for p in ws.rglob('*') if p.is_file())
   for p in ws.rglob('*'):
    assert not p.is_symlink()
    assert p.stat().st_mode&0o777==(0o700 if p.is_dir() else 0o600)
    if p.is_file():
     content=p.read_bytes()
     assert b'NEVER-COPY-THIS-CONTEXT' not in content and b'INDEX-ONLY-CANARY' not in content
   if role=='review':
    assert read(ws/'assessment.json')==a and inp['assessment_sha256']==digest(canonical(a))
   else:assert not (ws/'assessment.json').exists()
   expect_error(lambda:m.workspace(ws,first,context,role))
   schema=m.schema(role);assert schema['type']=='object' and schema['additionalProperties'] is False
   assert set(schema['required'])==set(schema['properties'])
   expected=set(a) if role=='analysis' else {'case_id','packet_sha256','assessment_sha256','verdict','reason','blockers'}
   assert set(schema['properties'])==expected
   assert isinstance(m.prompt(role),str) and len(m.prompt(role))>100
  ws=root/'workspace-invalid';ws.mkdir();expect_error(lambda:m.workspace(ws,first,context,'execute'))
  alias=root/'context-alias';alias.symlink_to(context,target_is_directory=True)
  expect_error(lambda:new_round(None,alias))
  unsafe,_=new_round();record=packet(unsafe)['local'][0];p=unsafe/'intake/data'/record['path'];data=p.read_bytes()
  outside=root/'DO-NOT-COPY';outside.write_bytes(data);p.unlink();p.symlink_to(outside)
  ws=root/'workspace-symlink';ws.mkdir();expect_error(lambda:m.workspace(ws,unsafe,context,'analysis'))
  for name,data in source_before.items():assert (context/name).read_bytes()==data
  assert case==read(context/'case.json') and watch==read(context/'watch.json')
print(json.dumps({'passed':True,'checks':['AP05 exact baseline and honest not_checked',
 'fresh external and local observations before bounded reviewed reuse',
 'distinct successful review bound to exact assessment and packet',
 'missing contradictory tampered evidence fails closed',
 'actual AP06 out-of-mandate draft with missing executable fields',
 'selected private immutable model copies and no index fulltext']}))
'''


def verify(candidate):
    from runtime.profile import sandbox_command, environment
    result = subprocess.run(
        sandbox_command(Path(candidate), ['/opt/homebrew/bin/python3.12', '-I', '-B', '-c', SCRIPT]),
        env=environment(), capture_output=True, text=True, timeout=120,
    )
    if result.returncode:
        return {'passed': False, 'reason': 'AP10 private policy contract failed',
                'stderr': result.stderr[-6000:]}
    try:
        return json.loads(result.stdout)
    except ValueError:
        return {'passed': False, 'reason': 'Missing host acceptance result'}
