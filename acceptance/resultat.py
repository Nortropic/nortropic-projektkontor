"""Host-owned AP04 result contract; candidate executed only inside native sandbox."""
import json
import subprocess
from pathlib import Path


def verify(candidate):
    from runtime.profile import sandbox_command, environment
    script = r'''
import contextlib, copy, io, json, math, os, pathlib, re, subprocess, sys, types
p = pathlib.Path('tools/kontor_result.py')
source = p.read_text()
compiled = compile(source, str(p), 'exec')
mod = types.ModuleType('office_result')
def audit(event,args):
    if event == 'open' or event.startswith(('os.','socket.','subprocess.','ctypes.')) or event == 'builtins.input':
        raise AssertionError('I/O during pure module import/render: '+event)
sys.addaudithook(audit)
with contextlib.redirect_stdout(io.StringIO()) as captured:
    exec(compiled, mod.__dict__)
assert not captured.getvalue(), 'Import must not print'
base={'task_id':'office-result-1','target':'Nortropic/nortropic-projektkontor',
'observation':'snapshot','live':False,'remote_current':False,'phase':'completed',
'VeR':None,'verified_delivery':True,'observed_at_epoch':123.0,'age_seconds':4.0,
'runtime_revision':'a'*40,'input_revision':'b'*40,'base':'c'*40,'candidate':'d'*40,
'acceptance_sha256':'e'*64,'review_run':'separate-review','evidence':'evidence/runs/office-result-1/state.json',
'integration':{'merged':True,'candidate':'d'*40,'merge_commit':'f'*40,'tree':'1'*40,
'url':'https://github.com/Nortropic/nortropic-projektkontor/pull/1'}}
checks=[]
def render(value):
    original=copy.deepcopy(value)
    with contextlib.redirect_stdout(io.StringIO()) as printed:
        result=mod.render(value)
    assert value==original, 'Input mutated'
    assert not printed.getvalue(), 'Rendering printed'
    assert isinstance(result,dict)
    json.dumps(result,allow_nan=False)
    assert result.get('live') is False and result.get('remote_current') is False
    assert isinstance(result.get('limitations'),list) and result['limitations']
    return result
r=render(base)
assert all(r[k]==base[k] for k in ('observation','task_id','phase','target'))
assert r['status']=='delivered' and r['merge_commit']=='f'*40 and r['url']==base['integration']['url']
assert all(r[k]==base[k] for k in ('runtime_revision','input_revision','base','candidate','review_run','acceptance_sha256','evidence','observed_at_epoch','age_seconds'))
checks.append('valid delivery retains exact identities')
for key in ('runtime_revision','input_revision','base','candidate','review_run','acceptance_sha256','evidence','observed_at_epoch','age_seconds','integration','task_id','target'):
    value=copy.deepcopy(base);del value[key]
    result=render(value);assert result['status']=='unavailable' and result['observation']=='unavailable',key
checks.append('missing completion evidence refuses delivery')
for key,bad in [('verified_delivery','true'),('verified_delivery',False),('observation','live'),('runtime_revision','main'),('target','other/repo'),('age_seconds',True),('age_seconds',-1),('observed_at_epoch',float('inf')),('phase','mystery')]:
    value=copy.deepcopy(base);value[key]=bad
    result=render(value);assert result['status']=='unavailable' and result['observation']=='unavailable',key
checks.append('invalid or unverified completion refuses delivery')
for key,bad in [('merged','true'),('candidate','a'*40),('merge_commit','main'),('tree',None),('url','https://github.com/other/repo/pull/1'),('url',base['integration']['url']+'/extra')]:
    value=copy.deepcopy(base);value['integration'][key]=bad
    result=render(value);assert result['status']=='unavailable' and result['observation']=='unavailable',key
checks.append('mismatched integration refuses delivery')
for phase in ['accepted','running_codex','running_claude','reviewing','publishing','waiting_access','waiting_diagnosis','waiting_review','waiting_publication_reconciliation']:
    value={**base,'phase':phase,'verified_delivery':False,'state':{'waiting_reason':'Preserved diagnosis'}}
    r=render(value);assert all(r[k]==value[k] for k in ('observation','task_id','phase','target'))
    assert r['status']=='not_delivered' and r['waiting_reason']=='Preserved diagnosis'
    assert 'merge_commit' not in r
checks.append('noncompleted states never claim delivery')
for value in [None,[],{}, {'observation':'unavailable','error':'Evidence missing'}]:
    r=render(value);assert r['status']=='unavailable' and r['observation']=='unavailable'
    if isinstance(value,dict) and value.get('error'):assert 'Evidence missing' in json.dumps(r)
checks.append('malformed and missing evidence exposed')
print(json.dumps({'passed':True,'checks':checks}))
'''
    result = subprocess.run(sandbox_command(Path(candidate), ['/opt/homebrew/bin/python3.12','-I','-B','-c',script]),
                            env=environment(), capture_output=True, text=True, timeout=30)
    try:
        outcome = json.loads(result.stdout)
    except ValueError:
        outcome = {'passed':False,'reason':'Contract process did not return JSON'}
    if result.returncode != 0:
        outcome = {'passed':False,'reason':'Contract failed','stderr':result.stderr[-5000:]}
    return outcome
