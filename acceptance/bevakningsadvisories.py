"""Frozen advisory intake qualification; synthetic sources, no live network.

The previous acceptance remains byte-identical. Its policy/schema checks are
retained, with explicit fixture adaptations for the newly required lock intake.
The fixed module digest is set by the host before review, never learned at run.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess

INTAKE_SHA256 = '9ab189c9408e3556e0d287c32f4ed9e05a6e6e59c96957a2a19b78745c61fbb9'
PRIOR_SHA256 = '76a0fa694061be3e843ada843ad4b6a0de190559f5f83c523903d8d5054a8ac8'


def retained_script():
    path = Path(__file__).with_name('bevakningsschema.py')
    if hashlib.sha256(path.read_bytes()).hexdigest() != PRIOR_SHA256:
        raise ValueError('Previous frozen acceptance changed')
    spec = importlib.util.spec_from_file_location('prior_watch_schema', path)
    prior = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prior)
    text = prior.SCRIPT
    # Exact old module pin changes only in this new acceptance, never in its source.
    old = 'bd1d043999b985b370645c2230b54ba1db265b1a669e2087dc1b073d425c7f2f'
    assert text.count(old) == 1
    text = text.replace(old, INTAKE_SHA256, 1)
    old = "target.write_text('Synthetic local fixture')"
    new = ("target.write_text(('temporalio==1.33.0 --hash=sha256:'+'a'*64+'\\n') "
           "if name=='config/temporal-probe-requirements.lock' else 'Synthetic local fixture')")
    assert text.count(old) == 1
    text = text.replace(old, new, 1)
    anchor = " actual=intake.collect(root/'dated-labels'"
    assert text.count(anchor) == 1
    text = text.replace(anchor, " dated['https://api.github.com/advisories?ecosystem=pip&affects=temporalio%401.33.0&type=reviewed&is_withdrawn=false&per_page=100']=b'[]'\n" + anchor, 1)
    old = "{'python-index','temporal-index','python-3.12.13','python-3.12.14','temporal-1.33.0'}"
    assert text.count(old) == 1
    text = text.replace(old, old[:-1] + ",'advisories-temporalio-1.33.0','advisories-temporalio-1.33.0-none'}", 1)
    return text


ADVISORY_SCRIPT = r'''
import copy, hashlib, io, json, pathlib, tempfile, urllib.error, urllib.request
from datetime import datetime
from email.message import Message
from unittest.mock import patch
import bevakningsunderlag as m
LOCK='config/temporal-probe-requirements.lock'
PREFIX='https://api.github.com/advisories?ecosystem=pip&affects='
SUFFIX='&type=reviewed&is_withdrawn=false&per_page=100'
QUERIES=[PREFIX+'protobuf%407.36.2'+SUFFIX,PREFIX+'temporalio%401.8.0'+SUFFIX]
versions={'python':'3.12.13','temporalio':'1.8.0','runtime_revision':'b'*40,
 'office_revision':'c'*40,'active_config_sha256':'a'*64}
responses={
 'https://www.python.org/downloads/source/':b'<a href="/downloads/release/python-31213/">Python 3.12.13</a>',
 'https://www.python.org/downloads/release/python-31213/':b'<h1>Python 3.12.13</h1>',
 'https://api.github.com/repos/temporalio/sdk-python/releases?per_page=20':b'[{"tag_name":"1.8.0","draft":false,"prerelease":false}]',
 'https://api.github.com/repos/temporalio/sdk-python/releases/tags/1.8.0':b'{"tag_name":"1.8.0","draft":false,"prerelease":false}',
 **{url:b'[]' for url in QUERIES}}
ghsa={'ghsa_id':'GHSA-2345-6789-cfgh','type':'reviewed','withdrawn_at':None,'severity':'high',
 'vulnerabilities':[{'package':{'ecosystem':'pip','name':'temporalio'},
 'vulnerable_version_range':'< 1.8.1','first_patched_version':'1.8.1'}]}
with tempfile.TemporaryDirectory(dir='.scratch') as temp:
 root=pathlib.Path(temp);roots={k:root/k for k in ('active','working')}
 for kind,folder in roots.items():
  for relative in m.LOCAL_FILES:
   path=folder/relative;path.parent.mkdir(parents=True,exist_ok=True)
   path.write_text('synthetic '+relative)
  (folder/LOCK).write_text(('protobuf==7.36.2 --hash=sha256:'+'b'*64+'\n'+'temporalio==1.8.0 --hash=sha256:'+'a'*64+'\n') if kind=='active' else 'working-only==9.9.9 --hash=sha256:'+'c'*64+'\n')
 calls=[]
 def fetch(url):
  calls.append(url);value=responses[url]
  if isinstance(value,Exception):raise value
  return value
 def collect(name,previous=None):
  calls.clear();return m.collect(root/name,roots,versions,previous=previous,fetcher=fetch)
 first=collect('empty');assert first['complete']
 assert [u for u in calls if u.startswith(PREFIX)]==QUERIES
 saved={p.name:p.read_bytes() for p in (root/'empty').iterdir()}
 rows=[r for r in first['sources'] if 'derived_from' in r];assert len(rows)==2
 for row in rows:
  assert datetime.fromisoformat(row['observed_at']).tzinfo
  raw=(root/'empty'/row['path']).read_bytes();value=json.loads(raw)
  assert value['state']=='inga_kanda_granskade' and hashlib.sha256(raw).hexdigest()==row['sha256']
 responses[QUERIES[1]]=json.dumps([ghsa]).encode()
 found=collect('found',first);assert found['complete'] and not found['same_controlled_basis']
 row=next(r for r in found['sources'] if r['id'].endswith(ghsa['ghsa_id']))
 raw=(root/'found'/row['path']).read_bytes();value=json.loads(raw)
 assert value['ghsa_id']==ghsa['ghsa_id'] and value['severity']=='high' and value['locked_version']=='1.8.0'
 assert value['patches']==[{'affected_range':'< 1.8.1','first_patched_version':'1.8.1'}]
 assert hashlib.sha256(raw).hexdigest()==row['sha256']
 assert collect('same',found)['same_controlled_basis']
 for i,error in enumerate([TimeoutError(),urllib.error.HTTPError('synthetic',429,'rate',{},None),b'{}',json.dumps([ghsa]*100).encode()]):
  responses[QUERIES[1]]=error;unknown=collect('unknown-'+str(i),found)
  assert not unknown['complete'] and unknown['fingerprint'] is None and not unknown['same_controlled_basis']
  affected=[r for r in unknown['sources'] if r['id'].startswith('advisories-temporalio-')]
  assert len(affected)==1 and affected[0]['status']=='unavailable'
  assert any(r['id']=='advisories-protobuf-7.36.2-none' and r['status']=='available' for r in unknown['sources'])
 (roots['active']/LOCK).write_text('--index-url https://outside.invalid\n')
 invalid=collect('invalid-lock');assert not invalid['complete']
 assert not any(u.startswith(PREFIX) for u in calls)
 assert all((root/'empty'/name).read_bytes()==raw for name,raw in saved.items())
for url in [QUERIES[0]+'&extra=x',QUERIES[0].replace('api.github.com','outside.invalid'),QUERIES[0].replace('ecosystem=pip','ecosystem=npm')]:
 with patch.object(urllib.request,'build_opener') as opener:
  try:m.fetch(url)
  except ValueError:pass
  else:raise AssertionError('Outside address accepted')
  opener.assert_not_called()
class Response(io.BytesIO):
 status=200
 def __init__(self,next_page=False):
  super().__init__(b'[]');self.headers=Message();self.reads=[]
  if next_page:self.headers['Link']='<https://api.github.com/advisories?after=x>; rel="next"'
 def geturl(self):return QUERIES[0]
 def read(self,n=-1):self.reads.append(n);return super().read(n)
with patch.object(urllib.request,'build_opener') as opener:
 response=Response(True);opener.return_value.open.return_value=response
 try:m.fetch(QUERIES[0])
 except ValueError:pass
 else:raise AssertionError('Unconsumed page accepted as complete')
 assert response.reads==[]
with patch.object(urllib.request,'build_opener') as opener:
 opener.return_value.open.return_value=Response();assert m.fetch(QUERIES[0])==b'[]'
 args=opener.return_value.open.call_args
 assert not any(k.lower() in ('authorization','cookie') for k,v in args.args[0].header_items())
 assert 0<args.kwargs['timeout']<=10
print(json.dumps({'passed':True,'checks':['retained strict schema and policy checks',
 'active exact pins only and two literal bounded unauthenticated queries',
 'separate hashed GHSA severity and patch observations; dated known-empty',
 'timeout rate limit malformed lock and pagination remain unknown',
 'unchanged historical packets and stable controlled-basis reuse']}))
'''


def script():
    return ('import contextlib, io, json\n'
            '_prior_output=io.StringIO()\n'
            'with contextlib.redirect_stdout(_prior_output):\n'
            '    exec(' + repr(retained_script()) + ')\n'
            'assert json.loads(_prior_output.getvalue())["passed"] is True\n'
            'exec(' + repr(ADVISORY_SCRIPT) + ')\n')


def verify(candidate):
    from runtime.profile import sandbox_command, environment
    result = subprocess.run(
        sandbox_command(Path(candidate), ['/opt/homebrew/bin/python3.12', '-I', '-B', '-c', script()]),
        env=environment(), capture_output=True, text=True, timeout=120,
    )
    if result.returncode:
        return {'passed': False, 'reason': 'Advisory intake contract failed', 'stderr': result.stderr[-6000:]}
    try:
        return json.loads(result.stdout)
    except ValueError:
        return {'passed': False, 'reason': 'Missing host acceptance result'}
