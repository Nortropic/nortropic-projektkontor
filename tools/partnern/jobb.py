"""Registrerade bakgrundsutredningar som återkommer till samma tråd.

Ett jobb är en journalförd utfästelse: registrerat → pågår → klart/begränsat/misslyckat/avbrutet. Det körs
som en egen modellkörning (samma avgränsade verktyg, inga skrivningar utanför partnerns lager). Avbryts det
av en serveromstart återupptas det vid nästa start från sin modellsession; avbryter Johnny det står det
avbrutet tills han återupptar det.
"""
from __future__ import annotations

import json
import queue
import re
import threading

from .agent import Korning
from .lager import nytt_id
from .verktyg import Verktygsfel, _norm


class Jobb:
    def __init__(self, server):
        self.s = server
        self._ko = queue.Queue()
        self._aktiva = {}
        self._las = threading.Lock()

    def starta_arbetare(self) -> None:
        threading.Thread(target=self._arbeta, name='partner-jobb', daemon=True).start()

    def registrera(self, korning, a: dict) -> dict:
        rubrik = re.sub(r'\s+', ' ', str(a.get('rubrik') or '')).strip()[:140]
        uppdrag = str(a.get('uppdrag') or '').strip()[:6000]
        if not rubrik or not uppdrag:
            raise Verktygsfel('Ange rubrik och uppdrag.')
        for j in self.s.lager.fraga("select * from jobb where trad=? and status in ('registrerat','pagar','avbrutet')",
                                    (korning.trad,)):
            if _norm(json.loads(j['data']).get('rubrik')) == _norm(rubrik):
                return {'text': 'Utredningen "%s" finns redan (%s, status %s); ingen ny registrerades.' % (
                    rubrik, j['id'], j['status'])}
        jid = nytt_id('jobb')
        self.s.lager.lagg_till('jobb', jobb=jid, trad=korning.trad, rubrik=rubrik, uppdrag=uppdrag,
                               fragor=[str(f)[:500] for f in (a.get('fragor') or [])][:12],
                               avgransning=str(a.get('avgransning') or '')[:1500], fran_tur=korning.id)
        korning.handelse('jobb', 'Utredning registrerad: %s (%s)' % (rubrik, jid))
        self._ko.put(jid)
        return {'text': 'Utredningen "%s" är registrerad som %s och körs i bakgrunden (egen modellkörning, ingen '
                        'användningsgräns). Resultatet läggs i den här tråden; status syns där.' % (rubrik, jid)}

    def aterstall_vid_start(self) -> list:
        """Registrerade utredningar köas; de som pågick eller avbröts av en omstart (ordnad eller krasch) återupptas.
        En utredning som Johnny själv avbröt står kvar tills han återupptar den."""
        ater = []
        for j in self.s.lager.fraga("select * from jobb where status in ('registrerat','pagar','avbrutet')"):
            historik = json.loads(j['data'] or '{}').get('historik') or []
            orsak = (historik[-1].get('orsak') if historik else '') or ''
            if j['status'] == 'avbrutet' and not orsak.startswith('serveromstart'):
                continue
            if j['status'] == 'pagar':
                self.s.lager.lagg_till('jobb_status', jobb=j['id'], trad=j['trad'], status='avbrutet',
                                       orsak='serveromstart under arbetet; återupptas automatiskt')
            ater.append(j['id'])
            self._ko.put(j['id'])
        return ater

    def avbryt(self, jid: str) -> bool:
        with self._las:
            k = self._aktiva.get(jid)
        if k:
            return k.avbryt('Johnny avbröt utredningen')
        j = self.s.lager.en('select * from jobb where id=?', (jid,))
        if j and j['status'] == 'registrerat':
            self.s.lager.lagg_till('jobb_status', jobb=jid, trad=j['trad'], status='avbrutet', orsak='Johnny avbröt')
            return True
        return False

    def ateruppta(self, jid: str) -> bool:
        j = self.s.lager.en('select * from jobb where id=?', (jid,))
        if not j or j['status'] not in ('avbrutet', 'begransat', 'misslyckat'):
            return False
        self.s.lager.lagg_till('jobb_status', jobb=jid, trad=j['trad'], status='registrerat', orsak='återupptas')
        self._ko.put(jid)
        return True

    def _arbeta(self) -> None:
        while True:
            jid = self._ko.get()
            try:
                self._kor(jid)
            except Exception as fel:  # ett jobb som kraschar får inte stoppa kön
                j = self.s.lager.en('select trad from jobb where id=?', (jid,))
                self.s.lager.lagg_till('jobb_status', jobb=jid, trad=(j or {}).get('trad'), status='misslyckat',
                                       orsak='internt fel: %s' % type(fel).__name__)

    def _kor(self, jid: str) -> None:
        j = self.s.lager.en('select * from jobb where id=?', (jid,))
        if not j or j['status'] not in ('registrerat', 'avbrutet'):
            return
        data = json.loads(j['data'])
        historik = data.get('historik') or []
        if historik and historik[-1].get('status') == 'avbrutet' and 'Johnny' in (historik[-1].get('orsak') or ''):
            return
        ater = bool(data.get('session'))
        if not data.get('session'):
            import uuid
            data['session'] = str(uuid.uuid4())  # journalförs före starten så att en krasch inte tappar sessionen
        self.s.lager.lagg_till('jobb_status', jobb=jid, trad=j['trad'], status='pagar', session=data['session'])
        korning = Korning(self.s, 'jobb', j['trad'], [], jobb=dict(data, jobb=jid),
                          ateruppta=jid if ater else None)
        korning.fortsatt_avbruten = ater
        with self._las:
            self._aktiva[jid] = korning
        self.s.registrera_korning(korning)
        try:
            try:
                res = self.s.agent.kor(korning, data.get('session'))
            except Exception as fel:
                res = {'status': 'fel', 'orsak': 'internt fel: %s' % type(fel).__name__, 'session': korning.session,
                       'forbrukning': {'modellanrop': True}}
            status = {'svarad': 'klart', 'begransad': 'begransat', 'avbruten': 'avbrutet', 'fel': 'misslyckat'}[res['status']]
            self.s.lager.lagg_till('jobb_status', jobb=jid, trad=j['trad'], status=status,
                                   resultat=res.get('svar') or None, orsak=res.get('orsak') or None,
                                   session=res.get('session'), forbrukning=res.get('forbrukning'),
                                   delsvar=(res.get('delsvar') or '')[-4000:] or None, steg=res.get('steg'),
                                   kallor=res.get('kallor'))
        finally:  # avregistreras först när utfallet står i journalen
            self.s.avregistrera_korning(korning)
            with self._las:
                self._aktiva.pop(jid, None)

    def korning(self, jid: str):
        with self._las:
            return self._aktiva.get(jid)
