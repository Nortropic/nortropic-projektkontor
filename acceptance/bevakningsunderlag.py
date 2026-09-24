"""Host intake acceptance: synthetic only, isolated native permissions."""
import json
import subprocess
from pathlib import Path
SCRIPT = r'''
import sys,pathlib,tempfile,json,copy,hashlib,urllib.request,urllib.error,io,unittest.mock as mock
sys.path.insert(0,str(pathlib.Path('tools').resolve()))
import bevakningsunderlag as m
assert tuple(m.LOCAL_FILES)==('runtime/worker.py','runtime/workflow.py','runtime/activities.py','runtime/run.py','runtime/service.py','runtime/profile.py','config/temporal-probe-requirements.lock','docs/runtime-v0.1.md','runtime/daemon.py','runtime/shared.py','runtime/release.py')
P='https://www.python.org/downloads/source/'
T='https://api.github.com/repos/temporalio/sdk-python/releases?per_page=20'
v={'python':'3.12.13','temporalio':'1.33.0','active_config_sha256':'a'*64,'runtime_revision':'b'*40,'office_revision':'c'*40}
responses={P:b'<a href="/downloads/release/python-31213/">Python 3.12.13</a><a href="/downloads/release/python-3140/">Python 3.14.0</a>',T:json.dumps([{'tag_name':'1.33.0','draft':False,'prerelease':False,'published_at':'2026-09-01T00:00:00Z'}]).encode(),'https://www.python.org/downloads/release/python-31213/':b'<h1>Python 3.12.13</h1><p><strong>Release Date:</strong> September 1, 2026</p>','https://api.github.com/repos/temporalio/sdk-python/releases/tags/1.33.0':json.dumps({'tag_name':'1.33.0','body':'Contrib integration only; no global guarantee','published_at':'2026-09-01T00:00:00Z','draft':False,'prerelease':False}).encode()}
with tempfile.TemporaryDirectory(dir='.scratch') as td:
 r=pathlib.Path(td);roots={k:r/k for k in ('active','working')}
 for root in roots.values():
  for f in m.LOCAL_FILES:
   p=root/f;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('synthetic '+f)
 calls=[]
 def fetch(u):calls.append(u);return responses[u]
 def collect(n,prev=None,f=fetch):return m.collect(r/n,roots,v,previous=prev,fetcher=f)
 first=collect('one');assert first['complete'] and not first['same_controlled_basis'] and len(calls)==4
 assert len(first['local'])==2*len(m.LOCAL_FILES) and first['versions']==v
 saved=copy.deepcopy(first);second=collect('two',first);assert second['same_controlled_basis'] and first==saved
 assert (r/'two/packet.json').stat().st_mode&0o777==0o600
 assert len({s['id'] for s in first['sources']})==4
 for s in first['sources']+first['local']:
  assert s['status']=='available' and s['observed_at'] and s['sha256']==hashlib.sha256((r/'one'/s['path']).read_bytes()).hexdigest()
 roots['working'].joinpath(m.LOCAL_FILES[0]).write_text('changed local use')
 changed=collect('three',first);assert changed['complete'] and not changed['same_controlled_basis']
 roots['active'].joinpath(m.LOCAL_FILES[0]).unlink()
 missing=collect('four',first);assert not missing['complete'] and not missing['same_controlled_basis'] and missing['fingerprint'] is None
 def lost(u):raise OSError('PRIVATE-SECRET /private/path')
 lostpacket=collect('five',first,lost);assert not lostpacket['complete'] and not lostpacket['same_controlled_basis'];assert 'PRIVATE-SECRET' not in json.dumps(lostpacket)

 # Real new stable selection; prerelease/draft cannot win.
 originals={str(p):p.read_bytes() for root in roots.values() for p in root.rglob('*') if p.is_file()}
 responses[P]+=b'<a href="/downloads/release/python-31214/">Python 3.12.14</a>'
 responses['https://www.python.org/downloads/release/python-31214/']=b'<h1>Python 3.12.14</h1>'
 responses[T]=json.dumps([{'tag_name':'1.34.0','draft':False,'prerelease':False},{'tag_name':'9.0.0','draft':True,'prerelease':False},{'tag_name':'9.1.0','draft':False,'prerelease':True},{'tag_name':'1.33.0','draft':False,'prerelease':False}]).encode()
 responses['https://api.github.com/repos/temporalio/sdk-python/releases/tags/1.34.0']=json.dumps({'tag_name':'1.34.0','body':'Selected new version','draft':False,'prerelease':False}).encode()
 roots['active'].joinpath(m.LOCAL_FILES[0]).write_text('synthetic '+m.LOCAL_FILES[0])
 calls.clear();new=collect('new',first);assert new['complete'] and not new['same_controlled_basis'] and len(calls)==6
 assert {x['id'] for x in new['sources']}=={'python-index','temporal-index','python-3.12.13','python-3.12.14','temporal-1.33.0','temporal-1.34.0'}
 external_key='https://api.github.com/repos/temporalio/sdk-python/releases/tags/1.34.0'
 external_old=responses[external_key];changed_body=json.loads(external_old);changed_body['body']='Changed vendor assertion only';responses[external_key]=json.dumps(changed_body).encode()
 external_only=collect('external-only',new);assert external_only['complete'] and not external_only['same_controlled_basis'] and external_only['fingerprint']!=new['fingerprint'];responses[external_key]=external_old
 for key,content in [(T,b'not json'),('https://api.github.com/repos/temporalio/sdk-python/releases/tags/1.34.0',b'{"tag_name":"9.0.0"}'),('https://www.python.org/downloads/release/python-31214/',b'<h1>Python 9.0.0</h1>'),(P,b'x'*(1048576+1))]:
  old=responses[key];responses[key]=content
  bad=collect('bad-'+str(len(list(r.iterdir()))),first);assert not bad['complete'] and not bad['same_controlled_basis'];responses[key]=old
 target=roots['working']/m.LOCAL_FILES[0];old=target.read_bytes();target.write_bytes(b'x'*(1048576+1));assert not collect('large-local')['complete'];target.write_bytes(old)
 target.unlink();target.symlink_to((roots['active']/m.LOCAL_FILES[0]).resolve());assert not collect('link-source')['complete'];target.unlink();target.write_bytes(old)
 alias=r/'alias';alias.symlink_to(roots['working'].resolve(),target_is_directory=True)
 try:
  linked=m.collect(r/'root-alias',{'working':alias,'active':roots['active']},v,fetcher=fetch)
  assert not linked['complete']
 except ValueError:pass
 try:m.collect(alias/'output',roots,v,fetcher=fetch)
 except ValueError:pass
 else:raise AssertionError('Symlink output ancestor accepted')
 for p in (r/'new').rglob('*'):assert p.stat().st_mode&0o777==(0o700 if p.is_dir() else 0o600)
 assert (r/'new').stat().st_mode&0o777==0o700
 for name,data in originals.items():assert pathlib.Path(name).read_bytes()==data
 before=(r/'one/packet.json').read_bytes()
 try:collect('one')
 except (ValueError,FileExistsError):pass
 else:raise AssertionError('Overwrote previous intake')
 assert before==(r/'one/packet.json').read_bytes()
 for u in ['http://www.python.org/downloads/source/','https://example.com/','https://api.github.com/repos/other/releases','https://www.python.org@evil.invalid/downloads/source/']:
  try:m.fetch(u)
  except ValueError:pass
  else:raise AssertionError('Unsafe URL accepted')
# Transport seam is urllib.request; no live network in host acceptance.
real_build=urllib.request.build_opener
captured=[]
def build(*handlers):
 opener=real_build(*handlers);captured.append(opener);return opener
class Response(io.BytesIO):
 def geturl(self):return P
 def getcode(self):return 200
 @property
 def status(self):return 200
 headers={}
def opened(self,request,**kw):
 assert 0<kw.get('timeout',0)<=10
 url=request.full_url if hasattr(request,'full_url') else request
 assert url==P
 if hasattr(request,'header_items'):
  assert not any(k.lower() in ('authorization','cookie') for k,v in request.header_items())
 return Response(b'x'*1048577)
with mock.patch.object(urllib.request,'build_opener',build),mock.patch.object(urllib.request.OpenerDirector,'open',opened):
 try:m.fetch(P)
 except ValueError:pass
 else:raise AssertionError('Oversize transport accepted')
assert captured,'Use bounded urllib opener, not ambient proxy/auth'
for opener in captured:
 assert not any(isinstance(h,urllib.request.ProxyHandler) and h.proxies for h in opener.handlers)
 assert not any(isinstance(h,(urllib.request.HTTPBasicAuthHandler,urllib.request.HTTPDigestAuthHandler,urllib.request.HTTPCookieProcessor)) for h in opener.handlers)
 redirect=[h for h in opener.handlers if isinstance(h,urllib.request.HTTPRedirectHandler)]
 assert len(redirect)==1
 try:result=redirect[0].redirect_request(urllib.request.Request(P),None,302,'redirect',{},'https://example.com/')
 except (ValueError,urllib.error.HTTPError):pass
 else:assert result is None,'Redirect followed'
print(json.dumps({'passed':True,'checks':['new actual observations and immutable prior','external AND active/working local bindings','changed/missing/unavailable remain distinct','bounded official selection and private exclusive evidence','no inferred authority']}))
'''
def verify(candidate):
    from runtime.profile import sandbox_command, environment
    p=subprocess.run(sandbox_command(Path(candidate),['/opt/homebrew/bin/python3.12','-I','-B','-c',SCRIPT]),env=environment(),capture_output=True,text=True,timeout=120)
    if p.returncode:return {'passed':False,'reason':'AP10 intake contract failed','stderr':p.stderr[-6000:]}
    try:return json.loads(p.stdout)
    except ValueError:return {'passed':False,'reason':'No host result'}
