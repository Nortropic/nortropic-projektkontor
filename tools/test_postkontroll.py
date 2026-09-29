"""Postkontrollen (POSTKONTROLL-20260929), prövad regel för regel mot små texter i `.scratch`.

Varje regel har ett prov som fäller den och ett som visar att den tiger när texten är hel; fixturerna bär den
hårdbrutna form posterna och planen faktiskt har, eftersom det var radbrytningen som gjorde den första versionen
av SUMMA och TURRADER blind.
"""
import contextlib
import io
from pathlib import Path
import tempfile
import unittest

import postkontroll


ROOT = Path(__file__).resolve().parents[1]
SCRATCH = ROOT / '.scratch'

PLANMALL = """Ägarens tur: väntar ett beslut eller en operatörshandling på ägaren skrivs det i denna plan under en
egen rad med blockets rubrik. Efter NAGOT-20260929 (2026-09-29) är %s
öppna; nästa kvartalsgenomgång är i januari 2027.

ÄGARENS TUR
%s

LOKALA GRENAR MED NAMNGIVET SKÄL (rutinen överst).
"""
TURRAD = '- [beslut] Digitala: %s (NAGOT-20260929) — sedan 2026-09-29'


class Hjalp(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=SCRATCH)
        self.addCleanup(self.temp.cleanup)

    def skriv(self, namn, text):
        vag = Path(self.temp.name) / namn
        vag.write_text(text, encoding='utf-8')
        return str(vag)

    def regler(self, fynd):
        return sorted(f['regel'] for f in fynd)

    def plan(self, antal_ord, rader, namn='plan.md'):
        return self.skriv(namn, PLANMALL % (antal_ord, '\n'.join(rader)))


class Stycken(Hjalp):
    def test_stycket_haller_ihop_over_radbrytning(self):
        """Posterna är hårdbrutna, så en mening som bryts mitt itu måste ändå läsas som en mening."""
        stycken = postkontroll.stycken(['26 rundor i uppdraget,', 'varav 17 på ett och 8 på ett annat.', '', 'Nytt.'])
        self.assertEqual(len(stycken), 2)
        self.assertIn('rundor i uppdraget, varav 17', stycken[0][1])

    def test_radnumret_pekar_pa_raden_traffen_star_pa(self):
        start, stycke, karta = postkontroll.stycken(['första raden', 'andra raden'])[0]
        self.assertEqual(postkontroll.radnr(karta, start, stycke.index('andra')), 2)


class Summa(Hjalp):
    def test_delarna_efter_varav_maste_bli_helheten(self):
        fil = self.skriv('post.md', 'Granskning: 26 rundor i uppdraget före denna posts egen,\n'
                                    'varav 17 på Digitala-kandidater (10 underkända) och 8 på kontorsposter.\n')
        fynd = postkontroll.kontrollera([fil])
        self.assertEqual(self.regler(fynd), ['SUMMA'])
        self.assertIn('17 + 8', fynd[0]['text'])
        self.assertEqual(fynd[0]['rad'], 2)

    def test_tal_inne_i_parentes_raknas_inte_som_led(self):
        """`(10 underkända)` är en underuppgift om de 17, inte en tredje del av de 26."""
        fil = self.skriv('post.md', '25 rundor, varav 17 på kandidater (10 underkända) och 8 på poster.\n')
        self.assertEqual(postkontroll.kontrollera([fil]), [])

    def test_talord_raknas_som_tal(self):
        fil = self.skriv('post.md', 'Tjugo rundor, varav sexton på kandidater och tre på poster.\n')
        self.assertEqual(self.regler(postkontroll.kontrollera([fil])), ['SUMMA'])

    def test_helheten_ar_talet_narmast_fore_varav_aven_med_komma(self):
        """"Runda 9 fällde fem, varav …" — helheten är fem, inte rundans nummer. Kravet att helheten skulle stå
        som tal + ord gjorde att kommat efter "fem" bröt paret, så regeln tog rundans nummer och räknade 3 + 2
        mot 9. Delarna måste vara minst två för att uppdelningen ska prövas, annars skiljer fixturen inte lägena."""
        fil = self.skriv('post.md', 'Runda 9 fällde fem, varav tre var kända och två var nya.\n')
        self.assertEqual(postkontroll.kontrollera([fil]), [])

    def test_tal_i_kodcitat_raknas_inte(self):
        """En text som citerar en annan texts felräkning räknar inte själv; annars fälls posten för det den
        redovisar att den rättat."""
        fil = self.skriv('post.md', 'Raden sade `26 rundor, varav 17 på ett slag och 8 på ett annat` och '
                                    'det var fel.\n')
        self.assertEqual(postkontroll.kontrollera([fil]), [])

    def test_helheten_tas_narmast_fore_varav(self):
        """"Steg 2 gav sex fynd, varav …" — helheten är sex, inte stegets nummer. Tas ett tidigare tal räknas
        uppdelningen mot fel helhet och en hel uppräkning blir ett falskt fynd."""
        fil = self.skriv('post.md', 'Steg 2 gav sex fynd, varav fyra var kända och två var nya.\n')
        self.assertEqual(postkontroll.kontrollera([fil]), [])

    def test_upprakningen_slutar_vid_satsens_slut(self):
        """Efter kolon följer ett nytt led, inte fler delar av samma helhet."""
        fil = self.skriv('post.md', 'Steg 2 gav sex fynd, varav fyra var kända: två av dem rörde tre filer.\n')
        self.assertEqual(postkontroll.kontrollera([fil]), [])

    def test_en_ensam_del_efter_varav_ar_ingen_uppdelning(self):
        fil = self.skriv('post.md', 'Nio anmärkningar, varav två fördes in i nästa version.\n')
        self.assertEqual(postkontroll.kontrollera([fil]), [])


class Talspridning(Hjalp):
    def test_samma_storhet_med_olika_tal_pa_olika_stallen(self):
        fil = self.skriv('post.md', 'En post blir faktarättelse bara när fem krav håller.\n\n'
                                    'Samma sex krav räknas likadant i koden och här.\n')
        fynd = postkontroll.kontrollera([fil])
        self.assertEqual(self.regler(fynd), ['TALSPRIDNING'])
        self.assertIn('krav', fynd[0]['text'])

    def test_storheten_ar_samma_over_filgransen(self):
        post = self.skriv('post.md', 'Klassningens fem krav står i drift.md.\n')
        block = self.skriv('block.md', 'Klassningens sex krav är prövade.\n')
        self.assertEqual(self.regler(postkontroll.kontrollera([post, block])), ['TALSPRIDNING'])

    def test_tal_i_kodcitat_ar_inte_styckets_egen_rakning(self):
        """En post som redovisar att den rättat "fem krav" till sex citerar den gamla räkningen; den räknar inte."""
        fil = self.skriv('post.md', 'Sex krav håller.\n\nRunda 3 fällde att posten sade `fem krav` i punktlistan.\n')
        self.assertEqual(postkontroll.kontrollera([fil]), [])

    def test_samma_tal_overallt_ger_inget_fynd(self):
        fil = self.skriv('post.md', 'Sex krav håller.\n\nSamma sex krav räknas likadant.\n')
        self.assertEqual(postkontroll.kontrollera([fil]), [])

    def test_obestamd_artikel_ar_ingen_rakning(self):
        """"Faller ett krav" är artikel, inte talet 1, och ska inte lägga ett tredje tal i jämförelsen."""
        fil = self.skriv('post.md', 'Sex krav håller. Faller ett krav blir posten ett förslag.\n')
        self.assertEqual(postkontroll.kontrollera([fil]), [])

    def test_rakning_i_singular_ses_inte(self):
        """Priset för raden ovan: "i en runda" är en verklig räkning som regeln inte når. Fyndet F017 i
        genomgången är av det slaget, och är därför klassat som ett bedömningsfynd och inte som fångat.

        Provet vilar på två saker samtidigt — "en" är utesluten och singularformen saknas i STORHETER — så det
        andra ledet prövas för sig: även med ett tal som inte är artikel ser regeln inte singularformen.
        """
        fil = self.skriv('post.md', 'Beskedet granskades i en runda.\n\nBeskedet granskades i två rundor.\n')
        self.assertEqual(postkontroll.kontrollera([fil]), [])
        singular = self.skriv('annan.md', 'Det var tre runda beslut.\n\nDet var fem runda beslut.\n')
        self.assertEqual(postkontroll.kontrollera([singular]), [])


class Parentes(Hjalp):
    def test_slutparentes_utan_borjan_ar_en_halv_omskrivning(self):
        fil = self.skriv('post.md', 'Baslinjen är 297 av miljöskäl och inte av kodskäl).\n')
        self.assertEqual(self.regler(postkontroll.kontrollera([fil])), ['PARENTES'])

    def test_parentestecken_i_kodcitat_raknas_inte(self):
        """En text som beskriver regeln själv citerar tecknen; de är inte styckets egna parenteser."""
        fil = self.skriv('post.md', 'Regeln beskrevs som "fler `)` än `(`" men koden letar annorlunda.\n')
        self.assertEqual(postkontroll.kontrollera([fil]), [])

    def test_parentes_over_radbrytning_ar_hel(self):
        fil = self.skriv('post.md', 'Baslinjen är 297 (mätt på oförändrad main\nföre ändringen).\n')
        self.assertEqual(postkontroll.kontrollera([fil]), [])


class Turrader(Hjalp):
    def test_prosans_antal_mot_blockets(self):
        plan = self.plan('tre rader', [TURRAD % 'a', TURRAD % 'b'])
        fynd = postkontroll.kontrollera([], plan=plan)
        self.assertEqual(self.regler(fynd), ['TURRADER'])
        self.assertIn('säger 3 öppna rader', fynd[0]['text'])

    def test_ratt_antal_ger_inget_fynd(self):
        self.assertEqual(postkontroll.kontrollera([], plan=self.plan('två rader', [TURRAD % 'a', TURRAD % 'b'])), [])

    def test_blocket_slutar_ocksa_vid_en_tomrad(self):
        """Aquarium-läsaren slutar vid första rad som inte är en turrad, och en tom rad är en sådan."""
        plan = self.skriv('plan.md', 'Efter NAGOT-20260929 är två rader\nöppna.\n\nÄGARENS TUR\n%s\n\n%s\n\nSlut.\n'
                          % (TURRAD % 'a', TURRAD % 'b'))
        fynd = [f for f in postkontroll.kontrollera([], plan=plan) if f['regel'] == 'TURRADER']
        self.assertIn('har 1 rader', fynd[0]['text'])

    def test_blocket_slutar_vid_forsta_rad_som_inte_ar_turrad(self):
        """Aquarium-läsaren slutar där, så kontrollen måste räkna likadant."""
        plan = self.plan('två rader', [TURRAD % 'a', 'En prosarad mitt i blocket.', TURRAD % 'b'])
        fynd = [f for f in postkontroll.kontrollera([], plan=plan) if f['regel'] == 'TURRADER']
        self.assertIn('har 1 rader', fynd[0]['text'])


class Turform(Hjalp):
    def test_rad_utan_sedan_datum(self):
        plan = self.plan('två rader', [TURRAD % 'a', '- [operatörshandling] Kör kommandot (NAGOT-20260929)'])
        fynd = [f for f in postkontroll.kontrollera([], plan=plan) if f['regel'] == 'TURFORM']
        self.assertEqual(len(fynd), 1)
        self.assertIn('sedan ÅÅÅÅ-MM-DD', fynd[0]['text'])

    def test_turrad_efter_blockslutet_nas_inte_av_lasaren(self):
        plan = self.plan('två rader', [TURRAD % 'a', 'En prosarad.', TURRAD % 'b'])
        fynd = [f for f in postkontroll.kontrollera([], plan=plan) if f['regel'] == 'TURFORM']
        self.assertIn('utanför blocket', fynd[0]['text'])

    def test_hela_rader_ger_inget_formfynd(self):
        plan = self.plan('två rader', [TURRAD % 'a', TURRAD % 'b'])
        self.assertEqual([f for f in postkontroll.kontrollera([], plan=plan) if f['regel'] == 'TURFORM'], [])


class Planblock(Hjalp):
    def test_dubblerad_rubrik(self):
        plan = self.skriv('plan.md', '# Ett block\n\ntext\n\n# Ett block\n\ntext\n')
        fynd = [f for f in postkontroll.kontrollera([], plan=plan) if f['regel'] == 'PLANBLOCK']
        self.assertEqual(len(fynd), 1)
        self.assertIn('står 2 gånger', fynd[0]['text'])

    def test_varje_rubrik_en_gang_ger_inget_fynd(self):
        plan = self.skriv('plan.md', '# Ett block\n\ntext\n\n# Ett annat\n\ntext\n')
        self.assertEqual([f for f in postkontroll.kontrollera([], plan=plan) if f['regel'] == 'PLANBLOCK'], [])


class Planfall(Hjalp):
    def test_stycke_som_faller_bort_ur_planen(self):
        """Planens block bär inte alltid markdown-rubrik, så bortfallet följs på stycken."""
        bas = self.skriv('bas.md', 'HELHET — det ena spåret.\n\nKUNDSTART — det andra spåret.\n\nSlutet.\n')
        plan = self.skriv('plan.md', 'HELHET — det ena spåret.\n\nSlutet.\n')
        fynd = [f for f in postkontroll.kontrollera([], plan=plan, bas=bas) if f['regel'] == 'PLANFALL']
        self.assertEqual(len(fynd), 1)
        self.assertIn('KUNDSTART', fynd[0]['text'])

    def test_omskrivet_stycke_ar_inget_bortfall(self):
        bas = self.skriv('bas.md', 'HELHET — det ena spåret med sina fyra etapper.\n\nSlutet.\n')
        plan = self.skriv('plan.md', 'HELHET — det ena spåret med sina fem etapper.\n\nSlutet.\n')
        self.assertEqual([f for f in postkontroll.kontrollera([], plan=plan, bas=bas) if f['regel'] == 'PLANFALL'], [])

    def test_likhetstroskeln_skiljer_omskrivet_fran_borttaget_i_samma_hunk(self):
        """När två basstycken blir ett är det tröskeln som avgör vilket som försvann: det stycke som har en
        efterföljare som liknar det är omskrivet, det andra är borta. Utan jämförelsen rapporteras båda."""
        bas = self.skriv('bas.md', 'HELHET — det ena spåret med fyra etapper.\n\n'
                                   'KUNDSTART — det andra spåret för kundupplevelsen.\n\nSlutet.\n')
        plan = self.skriv('plan.md', 'HELHET — det ena spåret med fem etapper.\n\nSlutet.\n')
        fynd = [f for f in postkontroll.kontrollera([], plan=plan, bas=bas) if f['regel'] == 'PLANFALL']
        self.assertEqual(len(fynd), 1, 'bara det stycke som saknar efterföljare ska rapporteras')
        self.assertIn('KUNDSTART', fynd[0]['text'])
        self.assertNotIn('HELHET', fynd[0]['text'])

    def test_ersattning_som_inte_krymper_ar_inget_bortfall(self):
        bas = self.skriv('bas.md', 'HELHET — det ena spåret.\n\nKUNDSTART — det andra spåret.\n\nSlutet.\n')
        plan = self.skriv('plan.md', 'HELHET — det ena spåret.\n\nNågot helt annat om en tredje sak.\n\nSlutet.\n')
        self.assertEqual([f for f in postkontroll.kontrollera([], plan=plan, bas=bas) if f['regel'] == 'PLANFALL'], [])


class Turbort(Hjalp):
    def test_borttagen_rad_rapporteras_att_kvittera(self):
        bas = self.plan('två rader', [TURRAD % 'a', TURRAD % 'b'], 'bas.md')
        plan = self.plan('två rader', [TURRAD % 'b'])
        fynd = [f for f in postkontroll.kontrollera([], plan=plan, bas=bas) if f['regel'] == 'TURBORT']
        self.assertEqual(len(fynd), 1)
        self.assertIn('Digitala: a', fynd[0]['text'])

    def test_prosan_som_namnger_den_borttagna_postens_namn_pekas_ut(self):
        bas = self.plan('två rader', ['- [beslut] Digitala: a (BORTTAGEN-POST-20260929) — sedan 2026-09-29',
                                      TURRAD % 'b'], 'bas.md')
        plan = self.skriv('plan.md', 'Efter BORTTAGEN-POST-20260929 är en rad\nöppen.\n\nÄGARENS TUR\n%s\n\nSlut.\n'
                          % (TURRAD % 'b'))
        fynd = [f for f in postkontroll.kontrollera([], plan=plan, bas=bas) if f['regel'] == 'TURBORT']
        self.assertIn('prosan namnger BORTTAGEN-POST-20260929', ' '.join(f['text'] for f in fynd))

    def test_oforandrat_block_ger_inget_fynd(self):
        bas = self.plan('två rader', [TURRAD % 'a', TURRAD % 'b'], 'bas.md')
        plan = self.plan('två rader', [TURRAD % 'a', TURRAD % 'b'])
        self.assertEqual([f for f in postkontroll.kontrollera([], plan=plan, bas=bas) if f['regel'] == 'TURBORT'], [])


class Planensstycken(Hjalp):
    def test_textreglerna_laser_planens_andrade_stycken(self):
        """Planblocket och posten är samma leverans och ska räkna likadant, så SUMMA gäller också den nya texten."""
        bas = self.skriv('bas.md', 'Ett gammalt block utan tal.\n\nÄGARENS TUR\n%s\n\nSlut.\n' % (TURRAD % 'a'))
        plan = self.skriv('plan.md', 'Nytt block: 26 rundor i uppdraget,\nvarav 17 på ett slag och 8 på ett annat '
                          'slag.\n\nEtt gammalt block utan tal.\n\nÄGARENS TUR\n%s\n\nSlut.\n' % (TURRAD % 'a'))
        fynd = [f for f in postkontroll.kontrollera([], plan=plan, bas=bas) if f['regel'] == 'SUMMA']
        self.assertEqual(len(fynd), 1)
        self.assertIn('17 + 8', fynd[0]['text'])

    def test_planens_oforandrade_block_lases_inte(self):
        """Hela planen bär historiska block vars tal inte hör ihop; bara ändringens stycken är leveransen."""
        bas = self.skriv('bas.md', 'Gammalt: 26 rundor i uppdraget,\nvarav 17 på ett slag och 8 på ett annat '
                         'slag.\n\nÄGARENS TUR\n%s\n\nSlut.\n' % (TURRAD % 'a'))
        plan = self.skriv('plan.md', 'Nytt block utan tal.\n\nGammalt: 26 rundor i uppdraget,\nvarav 17 på ett '
                          'slag och 8 på ett annat slag.\n\nÄGARENS TUR\n%s\n\nSlut.\n' % (TURRAD % 'a'))
        self.assertEqual([f for f in postkontroll.kontrollera([], plan=plan, bas=bas) if f['regel'] == 'SUMMA'], [])

    def test_utan_bas_lases_planen_inte_av_textreglerna(self):
        plan = self.skriv('plan.md', '26 rundor i uppdraget,\nvarav 17 på ett slag och 8 på ett annat slag.\n')
        self.assertEqual([f for f in postkontroll.kontrollera([], plan=plan) if f['regel'] == 'SUMMA'], [])


class Kommandot(Hjalp):
    def kor(self, argv):
        with contextlib.redirect_stdout(io.StringIO()) as ut:
            return postkontroll.main(argv), ut.getvalue()

    def test_exitkod_1_nar_nagot_finns_att_bemota(self):
        fil = self.skriv('post.md', '26 rundor, varav 17 på kandidater och 8 på poster.\n')
        kod, utdata = self.kor([fil])
        self.assertEqual(kod, 1)
        self.assertIn('1 fynd att bemöta', utdata)

    def test_exitkod_0_for_en_hel_text(self):
        kod, utdata = self.kor([self.skriv('post.md', 'En hel mening utan tal.\n')])
        self.assertEqual(kod, 0)
        self.assertIn('POSTKONTROLL OK', utdata)

    def test_bas_utan_plan_avvisas(self):
        with self.assertRaises(SystemExit), contextlib.redirect_stderr(io.StringIO()):
            postkontroll.main([self.skriv('post.md', 'text\n'), '--bas', 'bas.md'])


if __name__ == '__main__':
    unittest.main()
