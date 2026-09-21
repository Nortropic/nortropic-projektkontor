"""Frozen AP08 handoff behavior; task B still needs actual integrated A to exist."""
import json
import subprocess
from pathlib import Path

SCRIPT = r'''
import sys,pathlib,copy,json
sys.path.insert(0,str(pathlib.Path('tools').resolve()))
import development_result as result
import development_handoff as m
import agarbild
G={'id':'office-ap11','requirements':[{'id':'A','text':'Named reconciliation','task':None},{'id':'B','text':'Named handoff','task':None}],'next_action':{'text':'Inspect unavailable actual observations','authority':'none'}}
P={'schema':1,'generated_at':'2026-09-21T12:00:00Z','title':'AP11','summary':'Dated observation','scope':'Only the finite Office goal','capabilities':[],'work':[],'next_action':{'text':'Inspect unavailable actual observations','owner':'Chain driver','authority':'none','evidence':['goal']},'owner_decision':{'needed':'no','question':'No new owner decision requested','reason':'Technical continuation within already accepted goal','evidence':['goal']},'issues':[],'evidence':[{'id':'goal','title':'Accepted goal','kind':'authority','observed_at':'2026-09-21T11:00:00Z','revision':'fixture','locator':'synthetic fixture','sha256':None,'text':'Named AP11 only'}]}
original=copy.deepcopy((G,P));expected=result.reconcile(G,[])
seen=[];actual_result=result.reconcile;actual_render=agarbild.render
def reconcile(g,r):seen.append('result');return actual_result(g,r)
def render(p):seen.append('ap08');return actual_render(p)
result.reconcile=reconcile;agarbild.render=render
active=False
def audit(e,a):
 if active and (e=='open' or e.startswith(('socket.','subprocess.','os.','ctypes.'))):raise AssertionError('Handoff has effects')
sys.addaudithook(audit)
active=True;value=m.present(G,[],P);active=False
assert (G,P)==original and 'result' in seen and 'ap08' in seen
assert value['reconciliation']==expected
assert value['html']==actual_render(value['picture'])
agarbild.validate(value['picture'])
assert value['picture']['next_action']['authority']=='none'
assert value['picture']['next_action']['text']==G['next_action']['text']
assert value['picture']['owner_decision']==P['owner_decision']
assert value['picture']['evidence'][:len(P['evidence'])]==P['evidence']
assert len(value['picture']['work'])>=2
for item in G['requirements']:assert item['text'] in value['html']
assert value['reconciliation']['whole_goal_complete'] is False
assert all(w['state']!='finished' for w in value['picture']['work'])
# Mixed actual A interface result: delivery support MUST reach AP08 while the
# other requirement remains missing. An always-missing handoff cannot pass.
R={'task_id':'first','task_sha256':'a'*64,'observation':'snapshot','phase':'completed','verified_delivery':True,'target':'Nortropic/nortropic-projektkontor','observed_at_epoch':1790000000,'age_seconds':120,'runtime_revision':'b'*40,'input_revision':'c'*40,'base':'d'*40,'candidate':'e'*40,'acceptance_sha256':'f'*64,'review_run':'independent','evidence':'synthetic saved observation','integration':{'merged':True,'candidate':'e'*40,'merge_commit':'1'*40,'tree':'2'*40,'url':'https://github.com/Nortropic/nortropic-projektkontor/pull/1'}}
g=copy.deepcopy(G);g['requirements'][0]['task']={'id':'first','sha256':'a'*64,'acceptance_sha256':'f'*64,'merge_commit':'1'*40}
before=copy.deepcopy((g,[R],P));active=True;v=m.present(g,[R],P);active=False
assert (g,[R],P)==before
assert v['reconciliation']==actual_result(g,[R])
assert v['reconciliation']['requirements'][0]['status']=='delivery_supported'
assert v['reconciliation']['requirements'][1]['status']=='missing'
assert v['reconciliation']['whole_goal_complete'] is False
agarbild.validate(v['picture']);assert v['html']==actual_render(v['picture'])
assert v['picture']['next_action']['authority']=='none' and v['picture']['owner_decision']==P['owner_decision']
assert any(w['state']=='finished' and g['requirements'][0]['text'] in w['title']+' '+w['text'] for w in v['picture']['work'])
assert any(w['state']!='finished' and g['requirements'][1]['text'] in w['title']+' '+w['text'] for w in v['picture']['work'])
assert R['integration']['merge_commit'] in v['html'] and R['runtime_revision'] in v['html']
# The saved observation's time must be retained, not silently replaced by render time.
import datetime
stamp=datetime.datetime.fromtimestamp(R['observed_at_epoch'],datetime.timezone.utc)
assert any(e['observed_at'] is not None and datetime.datetime.fromisoformat(e['observed_at'].replace('Z','+00:00'))==stamp for e in v['picture']['evidence'])
# Do not smuggle extra authority through a conflicting preexisting picture.
p=copy.deepcopy(P);p['next_action']['authority']='accepted'
try:
 v=m.present(G,[],p);assert v['picture']['next_action']['authority']=='none'
except ValueError:pass
g=copy.deepcopy(G);g['requirements'][0]['text']='<script>fixture()</script>'
v=m.present(g,[],P);assert '<script>' not in v['html'] and '&lt;script&gt;' in v['html']
print(json.dumps({'passed':True,'checks':['Actual A interface and existing AP08 reused','Missing work, source/authority separation and next action survive handoff','Pure dated rendering, no effects, mutation or whole-goal PASS'],'scope':'Synthetic handoff behavior; fresh receiver/actual integration remains separate'}))
'''


def verify(candidate):
    from runtime.profile import sandbox_command, environment
    result = subprocess.run(sandbox_command(Path(candidate), ['/opt/homebrew/bin/python3.12', '-I', '-B', '-c', SCRIPT]),
                            env=environment(), capture_output=True, text=True, timeout=120)
    if result.returncode:
        return {'passed': False, 'reason': 'AP11 handoff recipe failed', 'stderr': result.stderr[-6000:]}
    try:
        return json.loads(result.stdout)
    except ValueError:
        return {'passed': False, 'reason': 'Missing recipe result'}
