"""Utfärdarsidan av tools/dokumentpost.py (DOKUMENTVAG-20261001): körs med Runtimes tolk, NR_HOST_ROOT = Runtime-värden och
den antagna utfärdarkoden först på sökvägen. Ändrar ingen utfärdarauktoritet, launcher eller App-nyckel.

    observera KATALOG COMMIT UTFIL      dokumentfallen (KATALOG/fall.json, eller acceptance.json om den finns) körda som
                                        utfärdaren kör dem: frozen_snapshot + run_isolated med KATALOG/probe.py
    forsegla KATALOG                    förseglar uppgiften ur KATALOG/uppgift.json efter alla läskontroller; skriver
                                        KATALOG/FORSEGLAT.json

Förseglingen är härledd ur kontorets förseglingar 2026-09-30 och 2026-10-01 (RUNTIME-BINARER-20260930,
RUNTIME-CODEX-20261001). Skillnaden: granskningen är kontorets tools/granska.py, och dess bindning prövas mot Runtimes
kvitto för läsaren (varje kopierad fil med sha256). Alla läskontroller görs före första skrivningen, och inget befintligt
skrivs över (exklusiva filer).
"""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone

HOST = Path(os.environ['NR_HOST_ROOT']).resolve()
from runtime.check_issuer import (HostIssuer, binding, current_main, frozen_snapshot, run_isolated,  # noqa: E402
                                  sealed_construction_suite, sha)
from runtime import integration  # noqa: E402
from runtime.construction_registration import register, resolve_profile  # noqa: E402

DOKUMENT = re.compile(r'\Adocs/(?:[A-Za-z0-9._-]+/)*[A-Za-z0-9._-]+\.md\Z')  # samma som tools/dokumentpost.py
encode = lambda v: (json.dumps(v, ensure_ascii=False, indent=2) + '\n').encode()


def git(repo, *args):
    return subprocess.run(['git', '-C', str(repo), *args], capture_output=True, check=True, timeout=120).stdout


def granskarens_namn(run_namn):
    """reviewer_run publiceras ordagrant och måste vara en ren etikett ([a-z0-9-], publish_construction.py); härlett ur
    läsarens körning, tvättat här i stället för att vägras där, efter förseglingens skrivningar."""
    return re.sub('-+', '-', re.sub('[^a-z0-9-]', '-', ('kontorsgranskning-' + run_namn).lower()))[:110].rstrip('-')


def publicerbar(text):
    """Samma prov som publish_construction.py gör på limitations och actual_reviewer, här före första skrivningen."""
    return not (len(text) > 3000 or re.search(r'(/Users/|/private/|/var/|/tmp/|/opt/|~/|[A-Za-z]:\\|\.runtime/|evidence/)', text)
                or '@' in text or re.search(r'https?://|www\.', text, re.I) or re.search(r'#\d|GH-\d', text, re.I)
                or any(ord(ch) < 32 or ord(ch) > 126 for ch in text))


def skriv_exklusivt(path, data, mode=0o400):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, mode)
    with os.fdopen(fd, 'wb') as f:
        f.write(data)


def observera(katalog, commit, utfil):
    katalog = Path(katalog).resolve()
    uppgift = json.loads((katalog / 'uppgift.json').read_text())
    kontrakt = json.loads((katalog / 'acceptance.json').read_text()) if (katalog / 'acceptance.json').exists() else None
    fall = kontrakt['cases'] if kontrakt else json.loads((katalog / 'fall.json').read_text())
    ut = {'commit': commit, 'probe_sha256': sha((katalog / 'probe.py').read_bytes()), 'fall': []}
    with tempfile.TemporaryDirectory(prefix='obs-', dir=katalog) as t:
        ws = Path(t).resolve()
        (ws / 'source').mkdir(); (ws / '.scratch').mkdir()
        frozen_snapshot(Path(uppgift['kontor']), commit, ws / 'source')
        prog = ws / 'probe.py'; prog.write_bytes((katalog / 'probe.py').read_bytes()); prog.chmod(0o400)
        for c in fall:
            m = run_isolated(ws, prog, json.dumps(c['input']).encode(), timeout=c['timeout_seconds'])
            try:
                faktiskt = json.loads(m['output'])
            except ValueError:
                faktiskt = None
            rad = {'id': c['id'], 'returncode': m['returncode'], 'timed_out': m['timed_out'], 'observed': faktiskt,
                   'stderr_tail': m['stderr'].decode(errors='replace')[-1500:]}
            if kontrakt:
                rad['matchar'] = json.dumps(faktiskt, sort_keys=True) == json.dumps(c['expected'], sort_keys=True)
            ut['fall'].append(rad)
    Path(utfil).write_text(json.dumps(ut, ensure_ascii=False, indent=1) + '\n')
    print(json.dumps([{k: r[k] for k in r if k not in ('observed', 'stderr_tail')} for r in ut['fall']], ensure_ascii=False))


def forsegla(katalog):
    katalog = Path(katalog).resolve()
    u = json.loads((katalog / 'uppgift.json').read_text())
    namn, kandidat, W = u['namn'], u['kandidat'], Path(u['integrationskopia'])
    kalla, granskning = Path(u['kalla']), Path(u['granskning'])
    # ---- läskontroller
    utfall = json.loads((granskning / 'review.json').read_text())
    svar, modell = utfall.get('answer') or {}, utfall.get('model') or ''
    if svar.get('verdict') != 'approved' or svar.get('blocking_findings') != []:
        raise SystemExit('Ingen godkänd separat granskning utan blockerande fynd; inget förseglas.')
    if not modell or any(ord(c) < 33 or ord(c) > 126 for c in modell):
        raise SystemExit('Granskningens modell saknas eller är inte ett rent id.')
    run = Path(utfall['run'])
    kvitto_bytes = (run / 'KVITTO.json').read_bytes()
    if (sha(kvitto_bytes) != (run / 'KVITTO.sha256').read_text().split()[0] or utfall.get('receipt_sha256') != sha(kvitto_bytes)
            or json.loads(kvitto_bytes).get('outcome') != 'svar_giltigt'):
        raise SystemExit('Läsarens kvitto stämmer inte med granskningens utfall.')
    lasta = {f['place']: f['copy_sha256'] for f in json.loads(kvitto_bytes).get('underlag') or []}
    granskade_bytes = (granskning / 'filer/kandidat/files-sha256.json').read_bytes()
    if lasta.get('kandidat/files-sha256.json') != sha(granskade_bytes):
        raise SystemExit('Läsaren läste inte exakt den bindning som förseglas.')
    if git(W, 'rev-parse', 'HEAD').decode().strip() != kandidat or git(W, 'status', '--porcelain').strip():
        raise SystemExit('Integrationskopian är inte exakt kandidaten eller inte ren.')
    if any((W / '.scratch').iterdir()):
        raise SystemExit('.scratch är inte tom.')
    bas = git(W, 'rev-list', '--parents', '-n', '1', kandidat).decode().split()[1]
    if current_main('Nortropic/nortropic-projektkontor') != bas:
        raise SystemExit('Main har flyttat sedan kandidaten byggdes; lägg om och publicera på nytt.')
    tree = git(W, 'rev-parse', kandidat + '^{tree}').decode().strip()
    andrade = sorted(p for p in git(W, 'diff', '--no-renames', '--name-only', bas, kandidat).decode().split('\n') if p)
    filer = {rel: sha(git(W, 'show', kandidat + ':' + rel)) for rel in andrade}
    if not andrade or not all(DOKUMENT.match(rel) and '..' not in Path(rel).parts for rel in andrade):
        raise SystemExit('Kandidaten ändrar annat än .md-filer under docs/; den går den vanliga vägen.')
    bas_filer = {rel: (sha(git(W, 'show', bas + ':' + rel)) if git(W, 'ls-tree', bas, '--', rel).strip() else None)
                 for rel in andrade}
    granskat = json.loads(granskade_bytes)
    if granskat.get('files_sha256') != filer or granskat.get('base_files_sha256') != bas_filer:
        raise SystemExit('Granskningen band andra byte än kandidaten eller basen.')
    suite_raw = (katalog / 'suite.json').read_bytes()
    suite = json.loads(suite_raw)
    if suite['candidate'] != kandidat or suite['tree'] != tree or suite['returncode'] != 0 or suite['last_line'] != 'OK':
        raise SystemExit('Svitmätningen gäller inte exakt kandidaten.')
    if sha((katalog / 'suite.log').read_bytes()) != suite['log_sha256']:
        raise SystemExit('Svitens logg ändrad.')
    obs = json.loads((katalog / 'obs-kandidat.json').read_text())
    if obs['commit'] != kandidat or not all(f.get('matchar') for f in obs['fall']) or \
            obs['probe_sha256'] != sha((katalog / 'probe.py').read_bytes()):
        raise SystemExit('Dokumentfallet är inte mätt och grönt på exakt kandidat med denna probe.')
    accept = (katalog / 'acceptance.txt').read_text().strip()
    reviewer_run = granskarens_namn(run.name)
    actual_reviewer = ('Independent reader through the office review tool (tools/granska.py: Runtime critique profile, %s, '
                       'read-only, no network, no execution) over the complete diff from main, the changed documents, the '
                       'owner\'s order and the receipts the post rests on.' % modell)
    limitations = ('Static reading of exact bytes only; the reviewer ran nothing. Documents under docs/ only (DOKUMENTVAG-20261001): '
                   'no code, rule, Runtime, activation or other repository change.')
    if (not re.fullmatch('[a-z0-9][a-z0-9-]{0,119}', reviewer_run) or reviewer_run == u['implementation_run']
            or not publicerbar(actual_reviewer) or not publicerbar(limitations)):
        raise SystemExit('Granskningens kvittofält går inte att publicera ordagrant; inget förseglas.')
    # ---- skrivningar (exklusiva)
    kallsha = sha(kalla.read_bytes())
    accepted = HOST / '.runtime/ap11/accepted' / (namn + '.json')
    post = {'schema': 'construction-acceptance/1', 'id': namn, 'source': str(kalla), 'source_sha256': kallsha,
            'targets': ['office'], 'accepted': True,
            'basis': ('Office document change under DOKUMENTVAG-20261001 (the owner\'s decision of 2026-10-01: one separate review '
                      'for changes to documents under docs/ only). Source: the owner\'s words the change records. Candidate %s '
                      'on %s; credential-free whole suite %d; %d native document observation(s); independent reader review '
                      '%s approved without blocking findings. No activation granted.'
                      % (kandidat[:12], bas[:12], suite['test_count'], len(obs['fall']), reviewer_run)),
            'holder': 'existing publication holder; separately reviewed adoption 10c with actual App 5110369 installation 165844923'}
    skriv_exklusivt(accepted, encode(post))
    reg = register(namn, 'office', kalla, kallsha, accepted)
    profil = resolve_profile(namn)
    build = HOST / '.runtime/ap11/build'
    manifest = {'path': str(W), 'candidate': kandidat, 'base': bas, 'tree': tree, 'files': filer,
                'implementation_run': u['implementation_run'], 'mandate_sha256': profil['mandate_sha256'],
                'registration_sha256': profil['registration_sha256']}
    reviewer = {'verdict': 'approved', 'blocking_findings': [], 'candidate': kandidat, 'source_sha256': filer,
                'reviewer_run': reviewer_run, 'actual_reviewer': actual_reviewer, 'limitations': limitations}
    skriv_exklusivt(build / (namn + '-candidate.json'), encode(manifest), 0o600)
    skriv_exklusivt(build / (namn + '-acceptance.txt'), (accept + '\n').encode(), 0o600)
    skriv_exklusivt(build / (namn + '-reviewer.json'), encode(reviewer), 0o600)
    task = {'id': namn, 'target': 'Nortropic/nortropic-projektkontor', 'base': bas, 'allowed_paths': andrade,
            'steps': [{'provider': 'claude', 'prompt': accept}], 'acceptance_sha256': sha(accept.encode())}
    subject = {'task_id': namn, 'task_sha256': integration.digest(task), 'base': bas, 'candidate': kandidat,
               'completed_steps': [0], 'acceptance_sha256': task['acceptance_sha256'],
               'implementation_runs': [u['implementation_run']]}
    bound = {k: subject[k] for k in ('task_id', 'task_sha256', 'candidate', 'acceptance_sha256')}
    bound.update(scope='whole_task', terminal_status='completed')
    review = {**bound, 'verdict': 'approved', 'blocking_findings': [], 'reviewer_run': reviewer_run,
              'actual_reviewer': actual_reviewer, 'source_sha256': filer, 'limitations': limitations}
    nu = datetime.now(timezone.utc)
    request = {'schema': 'nortropic-issuer-request/1', 'accepted_at': nu.isoformat(),
               'expires_at': (nu + timedelta(hours=23)).isoformat(), 'task': task, 'subject': subject, 'review': review,
               'review_sha256': sha(encode(review)), 'probe_program_sha256': sha((katalog / 'probe.py').read_bytes()),
               'acceptance_contract_sha256': sha((katalog / 'acceptance.json').read_bytes()), 'suite_sha256': sha(suite_raw),
               'accepted_source_sha256': kallsha, 'holder_acceptance_sha256': sha(accepted.read_bytes()),
               'registration_sha256': profil['registration_sha256'],
               'raw_review_sha256': sha((granskning / 'review.json').read_bytes())}
    mapp = HOST / '.runtime/ap11/check-issuer/requests' / namn
    mapp.mkdir(mode=0o700)
    for fil, data in (('request.json', encode(request)), ('review.json', encode(review)),
                      ('probe.py', (katalog / 'probe.py').read_bytes()), ('acceptance.json', (katalog / 'acceptance.json').read_bytes()),
                      ('suite.json', suite_raw), ('suite.log', (katalog / 'suite.log').read_bytes()),
                      ('raw-review.json', (granskning / 'review.json').read_bytes())):
        skriv_exklusivt(mapp / fil, data)
    # ---- skrivskyddad förkontroll med utfärdarens egna funktioner
    issuer = HostIssuer(HOST)
    issuer.authority()
    issuer.request(namn, task, subject, review)
    sealed_construction_suite(W, kandidat, 'tools', namn, suite['test_count'], issuer)
    tests = {**bound, 'passed': True, 'test_count': suite['test_count'], 'returncode': 0}
    integration.require_gate(task, subject, tests, review)
    ut = {'forseglat': nu.isoformat(), 'namn': namn, 'kandidat': kandidat, 'bas': bas, 'test_count': suite['test_count'],
          'binding': binding(task, subject, review), 'registration': reg['id'], 'request_sha256': sha(encode(request))}
    skriv_exklusivt(katalog / 'FORSEGLAT.json', encode(ut), 0o600)
    print(json.dumps(ut, indent=2))


if __name__ == '__main__':
    if sys.argv[1:2] == ['observera'] and len(sys.argv) == 5:
        observera(*sys.argv[2:])
    elif sys.argv[1:2] == ['forsegla'] and len(sys.argv) == 3:
        forsegla(sys.argv[2])
    else:
        raise SystemExit('usage: dokumentpost_utfardare.py observera KATALOG COMMIT UTFIL | forsegla KATALOG')
