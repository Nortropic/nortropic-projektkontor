"""Reviewed host acceptance: candidate code runs only in existing native sandbox."""
import json
import subprocess
from pathlib import Path

SCRIPT = r'''
import sys, pathlib, copy, json, io, contextlib, unittest
sys.path.insert(0,str(pathlib.Path('tools').resolve()))
import change_assessment as ca
import assignment_preparation as m
c={'schema':1,'id':'synthetic','created_at':'2026-09-20T10:00:00Z','sources':[{'id':'PRIVATE-SOURCE','title':'PRIVATE-TITLE','version':'version1','path':'private/source.txt','sha256':'a'*64,'size':7}], 'claims':[{'id':'PRIVATE-CLAIM','kind':'decision','text':'PRIVATE-RAW-TEXT','reason':'PRIVATE-REASON','standing':'decided','sources':['PRIVATE-SOURCE']}], 'actions':[{'id':'build','text':'Build fixture','reason':'Scoped work','claims':['PRIVATE-CLAIM'],'authority':{'status':'granted','scope':'Only fixture','sources':['PRIVATE-SOURCE']}}], 'next_action':'build'}
q={'checked_at':'2026-09-20T11:00:00Z','manifest':ca.reference_manifest(c),'result':{'ok':True,'files':[{'path':'private/source.txt','status':'ok'}]}}
s={'schema':1,'action':'build','references':[{'id':'PRIVATE-REF','source':'PRIVATE-SOURCE','version':'version1','quote':'PRIVATE-QUOTE'}], 'reference_checks':[{'id':'PRIVATE-REF','source':'PRIVATE-SOURCE','version':'version1','sha256':'a'*64,'quote':'PRIVATE-QUOTE','status':'matched'}], 'requirements':[{'id':'R1','text':'Produce a draft','reason':'Explicit selected outcome','claims':['PRIVATE-CLAIM'],'references':['PRIVATE-REF'],'tests':['T1']}], 'tests':[{'id':'T1','observable':'Output status is draft even with complete input','method':'Assert output status using synthetic data'}], 'export':{'title':'Synthetic preparation','context':[{'kind':'fact','text':'Existing assessment API available'},{'kind':'judgment','text':'Small adapter suffices'},{'kind':'decision','text':'Build bounded preparation'},{'kind':'authority','text':'Host supplied scoped grant requires review'}],'scope':['Pure preparation'],'limitations':['Selected sources only']}, 'task':{'id':'synthetic-task','target':'Nortropic/nortropic-projektkontor','base':'b'*40,'runtime_revision':'c'*40,'allowed_paths':['tools/bered_uppdrag.py'],'attempt_seconds':900,'automatic_retries':0,'steps':[{'provider':'codex','prompt':'Implement the reviewed brief'}],'acceptance':'acceptance/synthetic.py','acceptance_sha256':'d'*64,'brief':'tasks/synthetic.md'}}
checks=[]
def call(a=c,b=q,d=s):
    before=copy.deepcopy((a,b,d))
    with contextlib.redirect_stdout(io.StringIO()) as out:r=m.prepare(a,b,d)
    assert not out.getvalue() and (a,b,d)==before
    assert r['status']=='draft' and r['mechanical_complete']==(not r['gaps'])
    assert set(r)=={'status','mechanical_complete','gaps','private','package'}
    assert set(r['package'])=={'brief','task_draft','requirements','tests','gaps','limitations'}
    assert r['package']['task_draft']==d['task'] and r['private']['assessment']==ca.assess(a,b)
    assert r['package']['gaps']==r['gaps']
    assert r['package']['limitations'] and 'draft' in r['package']['brief'].lower()
    export=json.dumps(r['package']);assert 'PRIVATE-' not in export and 'private/source.txt' not in export
    assert all(set(g)=={'code','subject'} and all(isinstance(v,str) and v for v in g.values()) for g in r['gaps'])
    json.dumps(r,allow_nan=False)
    return r
assert call()['mechanical_complete']
for status in ('changed','missing','unsafe','not_checked'):
    b=copy.deepcopy(q)
    if status=='not_checked':b['result']['files']=[]
    else:b['result']={'ok':False,'files':[{'path':'private/source.txt','status':status}]}
    r=call(b=b);assert not r['mechanical_complete'];assert r['private']['assessment']['decisions'][0]['standing']=='decided'
checks.append('source applicability does not revoke decision, raw identities never export')
for mutate in [lambda d:d.update(reference_checks=[]),lambda d:d['reference_checks'][0].update(status='mismatch'),lambda d:d['requirements'][0].update(tests=[]),lambda d:d['requirements'][0].update(claims=[]),lambda d:d['tests'][0].update(observable=' '),lambda d:d['tests'][0].update(method=''),lambda d:d['task'].pop('base'),lambda d:d['task'].pop('acceptance_sha256'),lambda d:d.update(requirements=[]),lambda d:d['export'].update(context=[])]:
    d=copy.deepcopy(s);mutate(d);assert not call(d=d)['mechanical_complete']
a=copy.deepcopy(c);a['actions'][0]['authority']={'status':'not_established','scope':'Missing','sources':[]};assert not call(a=a)['mechanical_complete']
checks.append('missing reference, authority, observable verification and exact binding produce draft gaps')
for mutate in [lambda d:d['references'][0].update(source='unknown'),lambda d:d['references'][0].update(version='wrong'),lambda d:d['reference_checks'][0].update(sha256='e'*64),lambda d:d['reference_checks'][0].update(quote='wrong'),lambda d:d['requirements'][0].update(claims=['unknown']),lambda d:d['requirements'][0].update(tests=['unknown']),lambda d:d['task'].update(target='Other/repo'),lambda d:d['task'].update(allowed_paths=['tools/kontor.py']),lambda d:d['task'].update(allowed_paths=['tools/assignment_preparation.py']),lambda d:d['task'].update(allowed_paths=['tools/KONTOR.py']),lambda d:d['task'].update(allowed_paths=['tools/ASSIGNMENT_PREPARATION.py']),lambda d:d['task'].update(allowed_paths=['tools/a.py','tools/A.py']),lambda d:d['task'].update(allowed_paths=['tools/../escape']),lambda d:d['task'].update(base='main'),lambda d:d['task'].update(automatic_retries=True),lambda d:d.update(unknown='private'),lambda d:d['task'].update(acceptance_code='raise Exception()')]:
    d=copy.deepcopy(s);mutate(d)
    try:m.prepare(c,q,d)
    except ValueError:pass
    else:raise AssertionError('invalid input accepted')
checks.append('invalid identities, quotes, bindings, target and authority paths rejected')
# Audit pure API after dependencies already loaded: no open, process, network or OS mutation.
def audit(event,args):
    if event=='open' or event.startswith(('os.','socket.','subprocess.','ctypes.')):raise AssertionError('side effect '+event)
sys.addaudithook(audit)
assert call()['mechanical_complete']
checks.append('pure API has no I/O, no acceptance execution, no input mutation')
print(json.dumps({'passed':True,'checks':checks}))
'''

def verify(candidate):
    from runtime.profile import sandbox_command, environment
    p=subprocess.run(sandbox_command(Path(candidate), ['/opt/homebrew/bin/python3.12','-I','-B','-c',SCRIPT]),env=environment(),capture_output=True,text=True,timeout=60)
    if p.returncode:return {'passed':False,'reason':'AP06 core contract failed','stderr':p.stderr[-6000:]}
    try:return json.loads(p.stdout)
    except ValueError:return {'passed':False,'reason':'Missing acceptance JSON'}
