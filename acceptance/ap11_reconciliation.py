"""Reviewed host recipe. Candidate code runs only inside the existing sandbox."""
import json
import subprocess
from pathlib import Path

SCRIPT = r'''
import sys,pathlib,copy,json
sys.path.insert(0,str(pathlib.Path('tools').resolve()))
import kontor_result
import development_result as m
R={'task_id':'first','task_sha256':'a'*64,'observation':'snapshot','phase':'completed','verified_delivery':True,'target':'Nortropic/nortropic-projektkontor','observed_at_epoch':1,'age_seconds':2,'runtime_revision':'b'*40,'input_revision':'c'*40,'base':'d'*40,'candidate':'e'*40,'acceptance_sha256':'f'*64,'review_run':'independent','evidence':'synthetic saved observation','integration':{'merged':True,'candidate':'e'*40,'merge_commit':'1'*40,'tree':'2'*40,'url':'https://github.com/Nortropic/nortropic-projektkontor/pull/1'}}
G={'id':'office-ap11','requirements':[{'id':'A','text':'Named reconciliation','task':{'id':'first','sha256':'a'*64,'acceptance_sha256':'f'*64,'merge_commit':'1'*40}},{'id':'B','text':'Named handoff','task':None}],'next_action':{'text':'Prepare actual dependent handoff','authority':'accepted'}}
assert kontor_result.render(R)['status']=='delivered'
active=False
def audit(e,a):
 if active and (e=='open' or e.startswith(('socket.','subprocess.','os.','ctypes.'))):raise AssertionError('Reconciliation has effects')
sys.addaudithook(audit)
def invoke(g,reports):
 global active
 before=copy.deepcopy((g,reports));active=True
 try:x=m.reconcile(g,reports)
 finally:active=False
 assert (g,reports)==before
 assert x['goal_id']=='office-ap11' and x['live'] is False and x['remote_current'] is False
 assert x['whole_goal_complete'] is False and x['limitations']
 assert x['next_action']==g['next_action']
 assert [r['id'] for r in x['requirements']]==[r['id'] for r in g['requirements']]
 json.dumps(x,allow_nan=False)
 return x
x=invoke(G,[R]);assert x['requirements'][0]['status']=='delivery_supported'
assert x['requirements'][1]['status']=='missing';assert x['requirements'][0]['result']==kontor_result.render(R)
for field,value in [('task_sha256','9'*64),('acceptance_sha256','8'*64),('task_id','another')]:
 r=copy.deepcopy(R);r[field]=value
 assert invoke(G,[r])['requirements'][0]['status']!='delivery_supported'
r=copy.deepcopy(R);r['integration']['merge_commit']='3'*40
assert invoke(G,[r])['requirements'][0]['status']!='delivery_supported'
for field in ('review_run','integration','observed_at_epoch'):
 r=copy.deepcopy(R);del r[field]
 assert invoke(G,[r])['requirements'][0]['status']!='delivery_supported'
r=copy.deepcopy(R);r['verified_delivery']=False
assert invoke(G,[r])['requirements'][0]['status']!='delivery_supported'
assert invoke(G,[])['requirements'][0]['status']=='missing'
g=copy.deepcopy(G);g['requirements']=g['requirements'][:1]
assert invoke(g,[R])['whole_goal_complete'] is False
# Even identical duplicate observations are ambiguous; never select the positive one.
try:
 x=invoke(g,[R,R]);assert x['requirements'][0]['status']!='delivery_supported'
except ValueError:pass
g=copy.deepcopy(G);g['next_action']['authority']='none'
assert invoke(g,[R])['next_action']['authority']=='none'
for g in ({}, {**G,'id':'other-goal'}, {**G,'requirements':[G['requirements'][0],G['requirements'][0]]}):
 try:m.reconcile(g,[R])
 except ValueError:pass
 else:raise AssertionError('Invalid named-goal structure accepted')
# Observe actual reuse, rather than only duplicated matching text.
seen=[];original=kontor_result.render
def traced(report):seen.append(report);return original(report)
kontor_result.render=traced;m.reconcile(G,[R]);assert seen
print(json.dumps({'passed':True,'checks':['Named requirements tied to exact task, frozen acceptance and integration','Existing result reader reused, pure reads, missing/mismatch/duplicate fail closed','No whole-goal completion or new authority inferred from task PASS'],'scope':'Synthetic behavior, not actual delivery or current remote proof'}))
'''


def verify(candidate):
    from runtime.profile import sandbox_command, environment
    result = subprocess.run(sandbox_command(Path(candidate), ['/opt/homebrew/bin/python3.12', '-I', '-B', '-c', SCRIPT]),
                            env=environment(), capture_output=True, text=True, timeout=120)
    if result.returncode:
        return {'passed': False, 'reason': 'AP11 reconciliation recipe failed', 'stderr': result.stderr[-6000:]}
    try:
        return json.loads(result.stdout)
    except ValueError:
        return {'passed': False, 'reason': 'Missing recipe result'}
