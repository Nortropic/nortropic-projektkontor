"""Frozen host proof for the AP05 documented recipe's noninterference correction."""
import json
import subprocess
from pathlib import Path


def verify(candidate):
    from runtime.profile import sandbox_command, environment
    script = r'''
import contextlib, datetime, io, json, os, pathlib, sys, tempfile, unittest
sys.path.insert(0,str(pathlib.Path('tools').resolve()))
from change_assessment import reference_manifest
recipe=pathlib.Path('tools/CHANGE_ASSESSMENT.md').read_text().split('```python\n')[-1].split('```',1)[0]
checks=[]
with tempfile.TemporaryDirectory(dir='.scratch',prefix='host-recipe-') as folder:
    root=pathlib.Path(folder).resolve();selected=root/'sources'/'pending.txt';selected.parent.mkdir()
    case={'schema':1,'id':'synthetic','created_at':'2026-09-20T10:00:00Z',
          'sources':[{'id':'s','title':'Synthetic pending source','version':'v1','path':'sources/pending.txt','sha256':'a'*64,'size':1}],
          'claims':[{'id':'c','kind':'judgment','text':'Unresolved','reason':'Synthetic selected evidence','standing':'unresolved','sources':['s']}],
          'actions':[{'id':'a','text':'Prepare','reason':'Scoped fixture','claims':['c'],'authority':{'status':'not_established','scope':'No grant','sources':[]}}],'next_action':'a'}
    casefile=root/'case.json';casefile.write_text(json.dumps(case))
    verifier=root/'verifier.py';verifier.write_text('import json,sys\nassert len(sys.argv)==3 and sys.argv[1]=="verify"\nm=json.load(sys.stdin)\nprint(json.dumps({"ok":False,"files":[{"path":x["path"],"status":"missing"} for x in m["files"]]}))\nsys.exit(1)\n')
    os.environ.update(AP05_CASE=str(casefile),AP05_SOURCE_ROOT=str(root),AP05_VERIFIER=str(verifier))
    for output in [selected/'run',selected,selected.parent]:
        os.environ['AP05_OUTPUT']=str(output)
        try:
            with contextlib.redirect_stdout(io.StringIO()):exec(compile(recipe,'method-recipe','exec'),{'__name__':'__main__'})
        except (ValueError,SystemExit,FileExistsError):pass
        else:raise AssertionError('Overlapping output was accepted')
        assert not selected.exists() and not selected.is_symlink(), 'Selected missing source mutated'
    checks.append('output below/equal/above selected missing source refused before mutation')
    output=root/'office-output';os.environ['AP05_OUTPUT']=str(output)
    with contextlib.redirect_stdout(io.StringIO()):exec(compile(recipe,'method-recipe','exec'),{'__name__':'__main__'})
    report=json.loads((output/'report.json').read_text())
    assert report['source_checks']==[{'id':'s','status':'missing'}]
    assert report['next_action']['source_check']=='needs_reassessment'
    assert report['next_action']['authority']['status']=='not_established'
    assert not selected.exists() and json.loads(casefile.read_text())==case
    checks.append('fresh sibling output under common root works with unchanged case/missing source')
suite=unittest.defaultTestLoader.discover('tools',pattern='test_change_assessment.py')
with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
    result=unittest.TextTestRunner(stream=io.StringIO()).run(suite)
assert result.wasSuccessful(), 'Assessment unit regression failed'
print(json.dumps({'passed':True,'checks':checks,'unit_tests':result.testsRun}))
'''
    result = subprocess.run(sandbox_command(Path(candidate), ['/opt/homebrew/bin/python3.12', '-I', '-B', '-c', script]),
                            env=environment(), capture_output=True, text=True, timeout=60)
    if result.returncode:
        return {'passed': False, 'reason': 'Documented recipe acceptance failed', 'stderr': result.stderr[-5000:]}
    try:
        return json.loads(result.stdout)
    except ValueError:
        return {'passed': False, 'reason': 'Missing JSON acceptance output'}
