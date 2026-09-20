"""Frozen AP-05 host contract. Candidate runs only in Runtime's native sandbox."""
import json
import subprocess
import tempfile
from pathlib import Path


def verify(candidate):
    from runtime.profile import sandbox_command, environment
    script = r'''
import argparse, contextlib, copy, datetime, io, json, math, os, pathlib, re, sys, types
source=pathlib.Path('tools/change_assessment.py').read_text()
compiled=compile(source,'tools/change_assessment.py','exec')
m=types.ModuleType('change_assessment')
def audit(event,args):
    if event=='open' or event.startswith(('os.','socket.','subprocess.','ctypes.')) or event=='builtins.input':
        raise AssertionError('I/O during pure import/API: '+event)
sys.addaudithook(audit)
with contextlib.redirect_stdout(io.StringIO()) as output: exec(compiled,m.__dict__)
assert not output.getvalue()
c={'schema':1,'id':'synthetic-1','created_at':'2026-09-20T10:00:00+00:00',
'sources':[{'id':'s1','title':'Synthetic decision','version':'v1','path':'decision.txt','sha256':'a'*64,'size':7},
{'id':'s2','title':'Synthetic observation','version':'v1','path':'proof.txt','sha256':'b'*64,'size':8}],
'claims':[{'id':'c1','kind':'decision','text':'Two layers in principle','reason':'Explicit scoped decision','standing':'decided in principle','sources':['s1']},
{'id':'c2','kind':'fact','text':'A prior test passed','reason':'Synthetic test record','standing':'recorded','sources':['s2']},
{'id':'c3','kind':'judgment','text':'Review changed implementation','reason':'Version coverage matters','standing':'supported','sources':['s2']}],
'actions':[{'id':'a1','text':'Prepare assessment','reason':'Next permitted work','claims':['c3'],
'authority':{'status':'granted','scope':'Assessment only','sources':['s1']}},
{'id':'a2','text':'Write real map','reason':'Would need separate permission','claims':['c1'],
'authority':{'status':'not_granted','scope':'No map write permission','sources':['s1']}}], 'next_action':'a1'}
expected={'version':1,'files':[{'path':s['path'],'sha256':s['sha256'],'size':s['size']} for s in c['sources']]}
checks=[]
def manifest(v):
    before=copy.deepcopy(v);r=m.reference_manifest(v);assert v==before;return r
assert manifest(c)==expected
u=copy.deepcopy(c);u['sources'].reverse();assert manifest(u)==expected
q={'checked_at':'2026-09-20T11:00:00Z','manifest':expected,'result':{'ok':True,'files':[{'path':'decision.txt','status':'ok'},{'path':'proof.txt','status':'ok'}]}}
def assess(v,w):
    a,b=copy.deepcopy(v),copy.deepcopy(w)
    with contextlib.redirect_stdout(io.StringIO()) as output:r=m.assess(v,w)
    assert v==a and w==b and not output.getvalue()
    json.dumps(r,allow_nan=False)
    assert r['structure_valid'] is True and r['coverage']['complete_search'] is False
    assert r['case_id']==v['id'] and r['created_at']==v['created_at'] and r['checked_at']==w['checked_at']
    assert len(r['limitations'])>=4
    for key in ('approved','authorized','allowed','go'): assert key not in r
    for kind,plural in [('fact','facts'),('judgment','judgments'),('decision','decisions')]:
        originals=[x for x in v['claims'] if x['kind']==kind]
        assert len(r[plural])==len(originals)
        for actual,original in zip(r[plural],originals):
            assert all(actual[k]==original[k] for k in original)
    for actual,original in zip(r['actions'],v['actions']):assert all(actual[k]==original[k] for k in original)
    assert r['next_action']==next(x for x in r['actions'] if x['id']==v['next_action'])
    return r
r=assess(c,q)
assert all(x['status']=='ok' for x in r['source_checks'])
assert all(x['source_check']=='unchanged' for x in r['actions'])
assert r['actions'][1]['authority']['status']=='not_granted'
checks.append('legitimate separated report, exact binding, no global permission')
for status in ('changed','missing','unsafe','not_checked'):
    w=copy.deepcopy(q)
    if status=='not_checked':w['result']['files'].pop()
    else:w['result']['files'][1]['status']=status;w['result']['ok']=False
    r=assess(c,w)
    assert r['source_checks'][1]['status']==status
    assert r['decisions'][0]['source_check']=='unchanged'
    assert r['facts'][0]['affected_sources']==['s2']
    assert r['judgments'][0]['source_check']=='needs_reassessment'
    assert r['next_action']['affected_sources']==['s2']
    assert r['actions'][1]['source_check']=='unchanged'
    assert ('s2' in r['coverage']['not_checked'])==(status=='not_checked')
checks.append('changed missing unsafe unobserved propagate only to dependent claims/actions')
w=copy.deepcopy(q);w['result']['files'][0]['status']='changed';w['result']['ok']=False
r=assess(c,w);assert r['judgments'][0]['source_check']=='unchanged'
assert r['next_action']['source_check']=='needs_reassessment' and r['next_action']['authority']['status']=='granted'
checks.append('authority-only dependency marks applicability without revoking decision')
v=copy.deepcopy(c);v['actions'][0]['authority']={'status':'not_established','scope':'No source supplied','sources':[]}
assert assess(v,q)['next_action']['authority']['status']=='not_established'
checks.append('missing authority stays missing with unchanged source checks')
def reject_case(v):
    for operation in (lambda:manifest(v),lambda:m.assess(v,q)):
        try:operation()
        except ValueError:pass
        else:raise AssertionError('invalid case accepted')
for mutate in [lambda v:v.update(schema=True),lambda v:v['sources'][0].update(size=True),lambda v:v['sources'][0].update(sha256='main'),
lambda v:v['sources'][1].update(id='s1'),lambda v:v['sources'][1].update(path='decision.txt'),
lambda v:v['claims'][0].update(sources=['unknown']),lambda v:v['claims'][0].update(sources=[]),lambda v:v['claims'][0].update(reason=''),
lambda v:v['claims'][0].update(kind='permission'),lambda v:v['actions'][0]['authority'].update(sources=[]),
lambda v:v['actions'][0]['authority'].update(status='yes'),lambda v:v['actions'][0].update(claims=['unknown']),
lambda v:v.update(next_action='unknown'),lambda v:v.update(created_at='2026-99-20T10:00:00Z'),
lambda v:v.update(created_at='2026-09-20T10:00:00'),lambda v:v.update(extra='ignored')]:
    v=copy.deepcopy(c);mutate(v);reject_case(v)
for path in ['/root','../x','a//b','a/./b','a/../b','C:/file','a\\b','a\0b','']:
    v=copy.deepcopy(c);v['sources'][0]['path']=path;reject_case(v)
checks.append('malformed source refs/reasons/authority/timestamps/paths rejected')
for mutate in [lambda w:w['manifest']['files'][0].update(sha256='c'*64),lambda w:w.update(checked_at='2026-09-19T10:00:00Z'),
lambda w:w['result'].update(ok=False),lambda w:w['result']['files'][0].update(path='unknown'),
lambda w:w['result']['files'][0].update(status='approved'),lambda w:w['result']['files'].append(w['result']['files'][0]),
lambda w:w.update(extra=True),lambda w:w['result'].update(ok=1),lambda w:w['manifest'].update(version=True)]:
    w=copy.deepcopy(q);mutate(w)
    try:m.assess(c,w)
    except ValueError:pass
    else:raise AssertionError('invalid observation accepted')
v=copy.deepcopy(c);v['sources'][0]['size']=1
w=copy.deepcopy(q);w['manifest']=manifest(v);w['manifest']['files'][0]['size']=True
try:m.assess(v,w)
except ValueError:pass
else:raise AssertionError('bool manifest size accepted')
w=copy.deepcopy(q);w['result']['files']=[]
r=assess(c,w);assert r['coverage']['not_checked']==['s1','s2']
assert all(x['source_check']=='needs_reassessment' for x in r['actions'])
checks.append('wrong reference and malformed observation rejected; empty coverage not success')
checks.append('no I/O in import and APIs; inputs/reference identities retained')
print(json.dumps({'passed':True,'checks':checks}))
'''
    p = subprocess.run(sandbox_command(Path(candidate), ['/opt/homebrew/bin/python3.12', '-I', '-B', '-c', script]),
                       env=environment(), capture_output=True, text=True, timeout=30)
    try:
        result = json.loads(p.stdout)
    except ValueError:
        result = {'passed': False, 'reason': 'Contract process did not return JSON'}
    if p.returncode:
        result = {'passed': False, 'reason': 'Contract failed', 'stderr': p.stderr[-5000:]}
    if result.get('passed') is not True:
        return result
    cli_case = {'schema': 1, 'id': 'cli-fixture', 'created_at': '2026-09-20T10:00:00Z',
                'sources': [{'id': 's', 'title': 'Synthetic', 'version': 'v1', 'path': 'x', 'sha256': 'a'*64, 'size': 1}],
                'claims': [{'id': 'c', 'kind': 'judgment', 'text': 'Assess fixture', 'reason': 'Synthetic reason', 'standing': 'unresolved', 'sources': ['s']}],
                'actions': [{'id': 'a', 'text': 'Prepare only', 'reason': 'Scoped fixture', 'claims': ['c'],
                             'authority': {'status': 'not_established', 'scope': 'No grant', 'sources': []}}], 'next_action': 'a'}
    expected = {'version': 1, 'files': [{'path': 'x', 'sha256': 'a'*64, 'size': 1}]}
    check = {'checked_at': '2026-09-20T11:00:00Z', 'manifest': expected,
             'result': {'ok': False, 'files': [{'path': 'x', 'status': 'missing'}]}}
    with tempfile.TemporaryDirectory(prefix='ap05-accept-', dir=Path(candidate)/'.scratch') as folder:
        casefile, checkfile = Path(folder)/'case.json', Path(folder)/'check.json'
        casefile.write_text(json.dumps(cli_case)); checkfile.write_text(json.dumps(check))
        def run(args):
            proc = subprocess.run(sandbox_command(Path(candidate), ['/opt/homebrew/bin/python3.12', '-I', '-B',
                                  str(Path(candidate)/'tools/change_assessment.py'), *args]),
                                  env=environment(), capture_output=True, text=True, timeout=15)
            return proc.returncode, json.loads(proc.stdout)
        try:
            code, output = run(['manifest', str(casefile)])
            assert code == 0 and output == expected
            code, output = run(['report', str(casefile), str(checkfile)])
            assert code == 0 and output['next_action']['source_check'] == 'needs_reassessment'
            assert output['next_action']['authority']['status'] == 'not_established'
            for invalid in [json.dumps(cli_case).replace('{', '{"schema":1,', 1), '{"schema":NaN}', '{"schema":Infinity}', '{}']:
                casefile.write_text(invalid)
                code, output = run(['manifest', str(casefile)])
                assert code == 2 and isinstance(output.get('error'), str) and output['error']
            code, output = run(['manifest', str(Path(folder)/'absent.json')])
            assert code == 2 and output.get('error')
        except (AssertionError, ValueError, subprocess.TimeoutExpired) as exc:
            return {'passed': False, 'reason': 'CLI contract failed', 'detail': str(exc)}
    result['checks'].append('native CLI manifest/report, missing-source data, duplicate keys/constants/error exits')
    return result
