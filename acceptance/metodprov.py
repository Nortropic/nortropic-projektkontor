"""Host-only acceptance of the candidate method's isolated synthetic example.
This does not establish the method's real effect; AP07 host case review does that.
"""
import hashlib
import json
from pathlib import Path
import re
import subprocess


def verify(candidate):
    from runtime.profile import sandbox_command, environment
    candidate = Path(candidate)
    path = candidate / 'tools/METODPROV.md'
    text = path.read_text(encoding='utf8')
    blocks = re.findall(r'^```python\n(.*?)^```\s*$', text, re.M | re.S)
    if len(blocks) != 1 or '/Users/' in text or '/home/' in text:
        return {'passed': False, 'reason': 'One self-contained Python example; no private absolute paths required'}
    # Execute untrusted example only under existing native sandbox, additionally
    # deny writes, processes, network and ctypes. No host eval of candidate code.
    runner = '''import sys,json,io,contextlib
script=sys.stdin.read()
def audit(event,args):
 if event=='subprocess.Popen' or event.startswith(('socket.','ctypes.','shutil.')) or (event.startswith('os.') and event not in ('os.listdir','os.scandir','os.walk')):
  raise RuntimeError('Example attempted external side effect')
 if event=='open':
  mode=args[1];flags=args[2]
  if (isinstance(mode,str) and any(c in mode for c in 'wax+')) or (isinstance(flags,int) and flags & (1|2|64|512|1024)):
   raise RuntimeError('Example attempted write')
sys.addaudithook(audit)
exec(compile(script,'<method-example>','exec'),{'__name__':'__main__'})
'''
    result = subprocess.run(sandbox_command(candidate, ['/opt/homebrew/bin/python3.12','-I','-B','-c',runner]),
                            input=blocks[0], text=True, capture_output=True, env=environment(), timeout=30)
    if result.returncode or result.stderr:
        return {'passed': False, 'reason': 'Synthetic method example failed', 'stdout':result.stdout[-3000:], 'stderr':result.stderr[-3000:]}
    try: data=json.loads(result.stdout)
    except ValueError: return {'passed':False,'reason':'Example must emit one JSON object'}
    keys={'hypothesis','observation','decision','limitation'}
    if not isinstance(data,dict) or set(data)!=keys or not all(isinstance(v,str) and v.strip() for v in data.values()):
        return {'passed':False,'reason':'Missing explicit example outcome fields'}
    return {'passed':True,'checks':['Untrusted standalone example executed in existing native sandbox with writes/process/network denied','Four explicit nonempty outcome fields; content/effect still requires separate judgment'],
            'example_output':data,'method_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'scope':'Method example mechanics only; no real-case effectiveness or authority assertion'}
