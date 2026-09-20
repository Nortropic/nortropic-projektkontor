"""Frozen host AP08 presentation contract, candidate execution native-sandboxed."""
import json
import subprocess
from pathlib import Path
SCRIPT = r'''
import sys,pathlib,copy,json,subprocess,tempfile,os,re,hashlib
from html.parser import HTMLParser
sys.path.insert(0,str(pathlib.Path('tools').resolve()))
import agarbild as m
D={'schema':1,'generated_at':'2026-09-20T15:00:00Z','title':'Kontorets leveransbild','summary':'En daterad redovisning','scope':'Endast valt kontorsarbete','capabilities':[{'title':'Bereda uppdrag','use':'Samla ett granskningsbart uppdrag','limits':'Ger inget byggmandat','delivery':'Historiskt verifierad leverans','availability':'Ej kontrollerad nu','evidence':['e1']}],'work':[{'title':'Ersatt tekniskt försök','state':'superseded','text':'Historik, inte ett aktivt hinder','observed_at':'2026-09-19T10:00:00Z','evidence':['e1']},{'title':'Aktuellt arbete','state':'unknown','text':'Otillräcklig observation','observed_at':None,'evidence':['e2']}],'next_action':{'text':'Kedjedrivaren bedömer kvarstående underlag','owner':'Kedjedrivaren','authority':'accepted','evidence':['e1']},'owner_decision':{'needed':'no','question':'Inget ägarbeslut behövs','reason':'Tekniskt arbete inom accepterat mandat','evidence':['e1']},'issues':[{'text':'Två källor motsäger varandra; inte avgjort','evidence':['e1','e2']}],'evidence':[{'id':'e1','title':'Bevarat kvitto','kind':'delivery','observed_at':'2026-09-19T10:00:00Z','revision':'revision-1','locator':'evidence/selected.json','sha256':'a'*64,'text':'Historisk leverans, inget aktuellt driftbevis'},{'id':'e2','title':'Saknat underlag','kind':'observation','observed_at':None,'revision':'okänd','locator':'saknas','sha256':None,'text':'Ingen aktuell observation'}]}
class Inspect(HTMLParser):
 def __init__(self):super().__init__();self.tags=[];self.attrs=[];self.text=[]
 def handle_starttag(self,t,a):
  assert len({k for k,v in a})==len(a)
  self.tags.append(t);self.attrs.extend((t,k,v) for k,v in a)
 def handle_data(self,s):self.text.append(s)
def inspect_html(html):
 p=Inspect();p.feed(html)
 assert set(p.tags)<=set('html head meta title style body header main nav section article aside footer h1 h2 h3 h4 h5 h6 p ul ol li span div strong em small time details summary a code pre dl dt dd table thead tbody tr th td br hr b i'.split())
 meta=[]
 class Meta(HTMLParser):
  def handle_starttag(self,t,a):
   if t=='meta':meta.append(dict(a))
 q=Meta();q.feed(html)
 assert all(x.get('http-equiv','').lower()!='refresh' for x in meta)
 policies=[x.get('content','') for x in meta if x.get('http-equiv','').lower()=='content-security-policy']
 assert len(policies)==1
 chunks=[chunk.split() for chunk in policies[0].split(';') if chunk.strip()]
 assert len({c[0] for c in chunks})==len(chunks)
 policy={c[0]:c[1:] for c in chunks}
 assert policy.get('default-src')==["'none'"] and policy.get('style-src')==["'unsafe-inline'"] and policy.get('base-uri')==["'none'"] and policy.get('form-action')==["'none'"]
 assert set(policy)<=set(['default-src','style-src','base-uri','form-action'])
 for t,k,v in p.attrs:
  assert not k.lower().startswith('on') and k not in ['src','srcset','action','formaction','background','poster','xlink:href','data','codebase','archive','manifest']
  if k=='href':assert v.startswith('#') and len(v)>1
 assert not re.search(r'url\s*\(|@import',html,re.I)
 assert all('http-equiv' not in x or x['http-equiv'].lower()=='content-security-policy' for x in meta)
 return ''.join(p.text)
# Pure presentation must not access clocks, files, processes or network.
active=False
def audit(e,a):
 if active and (e=='open' or e.startswith(('socket.','subprocess.','os.','ctypes.'))):raise AssertionError('render side effect')
sys.addaudithook(audit)
original=copy.deepcopy(D);active=True;h=m.render(D);active=False;assert D==original
text=inspect_html(h)
for val in ['Bereda uppdrag','Ej kontrollerad nu','Historiskt verifierad leverans','revision-1','Inget ägarbeslut behövs','Två källor motsäger varandra','2026-09-19','2026-09-20']:assert val in text,val
assert re.search('sakna|okänd|otillräcklig',text,re.I) and re.search('framställd',text,re.I) and re.search('observer',text,re.I)
yes=copy.deepcopy(D);yes['owner_decision'].update(needed='yes',question='Acceptera nytt avgränsat mål?',reason='Utanför nuvarande mandat');yes['next_action']['authority']='proposed';assert 'Acceptera nytt avgränsat mål?' in inspect_html(m.render(yes))
hostile=copy.deepcopy(D);payload='<script>PRIVATE-MARKER</script><img src="https://invalid.example/x" onerror="evil()">';hostile['summary']=payload;assert payload in inspect_html(m.render(hostile));assert '<script>' not in m.render(hostile)
bad=[]
for path,val in [('schema',True),('generated_at','2026-09-20'),('generated_at','2026-02-30T10:00:00Z')]:
 x=copy.deepcopy(D);x[path]=val;bad.append(x)
x=copy.deepcopy(D);x['work'][0]['observed_at']='2026-09-21T00:00:00Z';bad.append(x)
x=copy.deepcopy(D);x['evidence'][0]['observed_at']='2026-09-19T10:00:00';bad.append(x)
x=copy.deepcopy(D);x['next_action']['evidence']=['absent'];bad.append(x)
x=copy.deepcopy(D);x['evidence'].append(copy.deepcopy(x['evidence'][0]));bad.append(x)
x=copy.deepcopy(D);x['owner_decision']['needed']='maybe';bad.append(x)
x=copy.deepcopy(D);x['extra']='forbidden';bad.append(x)
for x in bad:
 try:m.render(x)
 except ValueError:pass
 else:raise AssertionError('Invalid structure accepted')
with tempfile.TemporaryDirectory(dir='.scratch',prefix='owner-view-') as td:
 root=pathlib.Path(td);inp=root/'input.json';inp.write_text(json.dumps(D));before=inp.read_bytes();cli=pathlib.Path('tools/agarbild.py').resolve()
 launcher="import sys,runpy,pathlib\ndef audit(e,a):\n if e.startswith(('subprocess.','socket.','ctypes.','os.exec','os.spawn')) or e=='os.system':raise RuntimeError('Forbidden effect')\nsys.addaudithook(audit)\nsys.argv=sys.argv[1:]\nsys.path.insert(0,str(pathlib.Path(sys.argv[0]).parent))\nrunpy.run_path(sys.argv[0],run_name='__main__')"
 def invoke(i,o):return subprocess.run([sys.executable,'-I','-B','-c',launcher,str(cli),str(i),str(o)],capture_output=True,text=True,timeout=20)
 out=root/'view.html';p=invoke(inp,out);assert p.returncode==0,p.stderr;assert (out.stat().st_mode&0o777)==0o600;assert out.read_text()==h;assert inp.read_bytes()==before
 saved=out.read_bytes();assert invoke(inp,out).returncode==2 and out.read_bytes()==saved
 link=root/'link.json';link.symlink_to(inp.resolve());assert link.read_bytes()==inp.read_bytes();assert invoke(link,root/'bad.html').returncode==2 and not (root/'bad.html').exists()
 alias=root/'alias';alias.symlink_to(root.resolve(),target_is_directory=True);assert invoke(inp,alias/'bad.html').returncode==2 and not (root/'bad.html').exists()
 for content in ['{}','{"schema":NaN}','{"schema":1,"schema":1}','PRIVATE-MARKER']:
  inp.write_text(content);p=invoke(inp,root/'bad.html');assert p.returncode==2 and not (root/'bad.html').exists();assert 'PRIVATE-MARKER' not in p.stdout+p.stderr and str(root) not in p.stdout+p.stderr
print(json.dumps({'passed':True,'checks':['Offline inert HTML and readable Swedish evidence/time separation','Missing old conflicting observations, historical supersession, real owner question and no-question','No inferred authority or live state; strict schema and timestamps','Exclusive private CLI output, input preservation, symlink and malformed input refusals','Pure render and CLI process/network effects denied in native sandbox'],'scope':'Presentation/IO behavior only; actual case meaning and recipient browser review are separate'}))
'''
def verify(candidate):
    from runtime.profile import sandbox_command, environment
    p=subprocess.run(sandbox_command(Path(candidate),['/opt/homebrew/bin/python3.12','-I','-B','-c',SCRIPT]),env=environment(),capture_output=True,text=True,timeout=120)
    if p.returncode:return {'passed':False,'reason':'Owner view host contract failed','stderr':p.stderr[-6000:]}
    try:return json.loads(p.stdout)
    except ValueError:return {'passed':False,'reason':'Missing host acceptance result'}
