"""Host-owned AP06 CLI acceptance; all candidate execution is sandboxed."""
import hashlib
import json
import subprocess
from pathlib import Path

BOUND_CORE = {'tools/assignment_preparation.py': 'cdcde5bd10aebf8eeba2a45aa980433f4785dbe7d06a466bc2cce1c0131c74fc', 'tools/change_assessment.py': '8f0f059447fec11c49435124c1dd72dcc2a7677d74d488e3c4328dfbb456dffc', 'tools/kontor.py': 'c8954d92af988651b723f449b111fe58919511006edeaef17b02934883572b65'}
SCRIPT = r'''

import sys, pathlib, copy, json, io, contextlib, unittest
sys.path.insert(0,str(pathlib.Path('tools').resolve()))
import change_assessment as ca
import assignment_preparation as m
c={'schema':1,'id':'synthetic','created_at':'2026-09-20T10:00:00Z','sources':[{'id':'PRIVATE-SOURCE','title':'PRIVATE-TITLE','version':'version1','path':'private/source.txt','sha256':'a'*64,'size':7}], 'claims':[{'id':'PRIVATE-CLAIM','kind':'decision','text':'PRIVATE-RAW-TEXT','reason':'PRIVATE-REASON','standing':'decided','sources':['PRIVATE-SOURCE']}], 'actions':[{'id':'build','text':'Build fixture','reason':'Scoped work','claims':['PRIVATE-CLAIM'],'authority':{'status':'granted','scope':'Only fixture','sources':['PRIVATE-SOURCE']}}], 'next_action':'build'}
q={'checked_at':'2026-09-20T11:00:00Z','manifest':ca.reference_manifest(c),'result':{'ok':True,'files':[{'path':'private/source.txt','status':'ok'}]}}
s={'schema':1,'action':'build','references':[{'id':'PRIVATE-REF','source':'PRIVATE-SOURCE','version':'version1','quote':'PRIVATE-QUOTE'}], 'reference_checks':[{'id':'PRIVATE-REF','source':'PRIVATE-SOURCE','version':'version1','sha256':'a'*64,'quote':'PRIVATE-QUOTE','status':'matched'}], 'requirements':[{'id':'R1','text':'Produce a draft','reason':'Explicit selected outcome','claims':['PRIVATE-CLAIM'],'references':['PRIVATE-REF'],'tests':['T1']}], 'tests':[{'id':'T1','observable':'Output status is draft even with complete input','method':'Assert output status using synthetic data'}], 'export':{'title':'Synthetic preparation','context':[{'kind':'fact','text':'Existing assessment API available'},{'kind':'judgment','text':'Small adapter suffices'},{'kind':'decision','text':'Build bounded preparation'},{'kind':'authority','text':'Host supplied scoped grant requires review'}],'scope':['Pure preparation'],'limitations':['Selected sources only']}, 'task':{'id':'synthetic-task','target':'Nortropic/nortropic-projektkontor','base':'b'*40,'runtime_revision':'c'*40,'allowed_paths':['tools/bered_uppdrag.py'],'attempt_seconds':900,'automatic_retries':0,'steps':[{'provider':'codex','prompt':'Implement the reviewed brief'}],'acceptance':'acceptance/synthetic.py','acceptance_sha256':'d'*64,'brief':'tasks/synthetic.md'}}
import tempfile, subprocess, hashlib, os
cli=pathlib.Path('tools/bered_uppdrag.py').resolve()
checks=[]
with tempfile.TemporaryDirectory(dir='.scratch',prefix='ap06-cli-') as td:
    root=pathlib.Path(td).resolve();sources=root/'sources';sources.mkdir();(sources/'private').mkdir()
    selected=sources/'private/source.txt';selected.write_bytes(b'source!')
    c['sources'][0]['sha256']=hashlib.sha256(selected.read_bytes()).hexdigest()
    q['manifest']=ca.reference_manifest(c);s['reference_checks'][0]['sha256']=c['sources'][0]['sha256']
    paths=[root/'case.json',root/'check.json',root/'spec.json']
    def save():
        for p,v in zip(paths,(c,q,s)):p.write_text(json.dumps(v))
    save();originals={str(p):p.read_bytes() for p in [*paths,selected]}
    launcher="import sys,runpy\ndef audit(e,a):\n if e.startswith(('subprocess.','socket.','ctypes.','os.exec','os.spawn')) or e=='os.system':raise RuntimeError('Forbidden side effect')\nsys.addaudithook(audit)\nsys.argv=sys.argv[1:]\nimport pathlib\nsys.path.insert(0,str(pathlib.Path(sys.argv[0]).resolve().parent))\nrunpy.run_path(sys.argv[0],run_name='__main__')"
    def invoke(out,ins=paths):
        p=subprocess.run([sys.executable,'-I','-B','-c',launcher,str(cli),*[str(x) for x in ins],'--source-root',str(sources),'--output',str(out)],capture_output=True,text=True,timeout=20)
        try:r=json.loads(p.stdout)
        except ValueError:raise AssertionError('CLI must return one JSON result even on invalid input: '+p.stderr[-1000:])
        assert str(root) not in p.stderr and 'PRIVATE-' not in p.stderr
        return p.returncode,r
    out=root/'bundle';code,r=invoke(out);assert code==0 and r['status']=='draft' and r['mechanical_complete'] is True
    expected=m.prepare(c,q,s)
    assert json.loads((out/'private.json').read_text())==expected['private']
    assert json.loads((out/'package.json').read_text())==expected['package']
    assert json.loads((out/'task.draft.json').read_text())==s['task']
    assert (out/'brief.draft.md').read_text()==expected['package']['brief']
    assert (out.stat().st_mode&0o777)==0o700
    assert all((p.stat().st_mode&0o777)==0o600 for p in out.iterdir())
    assert all(pathlib.Path(p).read_bytes()==b for p,b in originals.items())
    saved={p.name:p.read_bytes() for p in out.iterdir()}
    assert invoke(out)[0]==2 and saved=={p.name:p.read_bytes() for p in out.iterdir()}
    checks.append('actual CLI calls delivered core; private bundle modes, exact separated output, no overwrite')
    q['result']={'ok':False,'files':[{'path':'private/source.txt','status':'missing'}]};save()
    code,r=invoke(root/'incomplete');assert code==0 and not r['mechanical_complete'] and r['gaps']
    checks.append('incomplete observations preserved as marked draft, never authority')
    for malformed in ['{}','{"schema":NaN}',paths[0].read_text().replace('{','{"schema":1,',1)]:
        paths[0].write_text(malformed);badout=root/'bad';code,r=invoke(badout);assert code==2 and r.get('error') and not badout.exists()
        assert str(root) not in json.dumps(r) and 'PRIVATE-' not in json.dumps(r)
    save()
    link=root/'linked.json';link.symlink_to(paths[0]);assert invoke(root/'linked-out',[link,*paths[1:]])[0]==2
    linkdir=root/'alias';linkdir.symlink_to(root,target_is_directory=True);assert invoke(linkdir/'via-alias')[0]==2;assert not (root/'via-alias').exists()
    # Source missing: output equal, beneath, or above selected source must not create it.
    selected.unlink()
    for badout in [selected,selected/'bundle',selected.parent,selected.with_name('SOURCE.TXT'),selected.with_name('SOURCE.TXT')/'bundle']:assert invoke(badout)[0]==2 and not selected.exists()
    for badout in [paths[0],paths[0]/'bundle',root]:assert invoke(badout)[0]==2
    absentparent=root/'absent';assert invoke(absentparent/'bundle')[0]==2 and not absentparent.exists()
    assert invoke(root/'missing-input',[root/'absent.json',*paths[1:]])[0]==2
    checks.append('strict JSON, symlink/input/output and both-direction source collisions refused without mutation')
    assert invoke(root/'legitimate-missing')[0]==0 and not selected.exists()
    checks.append('separate output with missing selected source is valid draft; no process/network/acceptance execution')
suite=unittest.defaultTestLoader.discover('tools',pattern='test_bered_uppdrag.py')
stream=io.StringIO()
with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):r=unittest.TextTestRunner(stream=stream).run(suite)
assert r.testsRun>0 and r.wasSuccessful(),stream.getvalue()
print(json.dumps({'passed':True,'checks':checks,'candidate_endpoint_tests':r.testsRun}))

'''


def verify(candidate):
    from runtime.profile import sandbox_command, environment
    for name, expected in BOUND_CORE.items():
        path=Path(candidate)/name
        if path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest()!=expected:
            return {'passed':False,'reason':'Active delivered core changed'}
    p=subprocess.run(sandbox_command(Path(candidate), ['/opt/homebrew/bin/python3.12','-I','-B','-c',SCRIPT]),env=environment(),capture_output=True,text=True,timeout=120)
    if p.returncode:return {'passed':False,'reason':'CLI endpoint contract failed','stderr':p.stderr[-6000:]}
    try:return json.loads(p.stdout)
    except ValueError:return {'passed':False,'reason':'No CLI acceptance JSON'}
