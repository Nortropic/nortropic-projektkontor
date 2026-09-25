# Aquarium: the Arkivet date of an undated delivery

Change `_arkivet` in `tools/aquarium.py` as section 1 states, add the two tests of section 2 to `tools/test_aquarium.py`
and add the one sentence of section 3 to `tools/AQUARIUM.md`. Existing Runtime builds and tests this product; its review
and integration follow the office's working form. Do not modify any other file, any active execution, host acceptance or
publication authority. Standard library only. No real sources, network, model calls or written files beyond the task.

Aquarium's Arkivet shows one item per delivered or closed commitment. An item from the decision log takes its date from
the delivery entry itself: the first real date in the entry's id, else in its text (`_first_date(entry['id'],
entry['text'])`). The entry `AP10-LEVERANS` carries no date, so AP10 is shown undated and last, although its delivery
note `evidence/ap10/leverans.md` carries one. Nothing may be invented: an item stays undated unless a source carries its
date, and the item says where its date came from.

The texts in `code format` below are exact, character for character.

## 1. `_arkivet(available, office)` in `tools/aquarium.py`

- For a delivery entry of the decision log whose own date is `None`, take the date of the delivery note of the same
  commitment: the first note in `office['notes']` whose `ap` equals the entry's key (`_delivery_key(entry['id'])`),
  dated as notes are dated today (`_first_date(note['ap'], note['text'])`). If that date is not `None`, the item's
  `date` is it and its `basis` is exactly `'beslutsloggen ' + entry['id'] + ', datum ur leveransbesked ' + key`.
- Everything else is exactly as before: an entry with its own date keeps it and the basis `'beslutsloggen ' + entry['id']`;
  an entry without its own date and without a dated note of its key stays undated with that same basis; a note whose key
  has a delivery entry still adds no item of its own; a note without such an entry still adds its own item as before;
  the order (dated items newest first, then the undated ones in their source order) and the unavailable case are
  unchanged. `_arkivet` stays pure. No other function changes.

## 2. Two tests in class `Arkivet` of `tools/test_aquarium.py`

Add exactly these two methods to the existing class `Arkivet`, using its `project` helper and the module's `entry`
helper, and leave every existing test unchanged:

- `test_an_undated_delivery_takes_the_date_of_its_note`: an office whose only entry is `AP10-LEVERANS` without a date and
  whose only note is AP10 with a date in its text; the one item has that date and the basis
  `beslutsloggen AP10-LEVERANS, datum ur leveransbesked AP10`.
- `test_the_entry_date_wins_and_an_undated_note_invents_nothing`: an entry with its own date and a note of the same key
  with another date keeps its own date and the basis without the suffix; an entry without a date and a note of the same
  key without a date stays undated.

You cannot run the tests. Read them before you write: the existing `test_deliveries_notes_dates_and_order` gives AP10 its
date in the entry's text, so it is unchanged by this rule; `test_undated_items_last_and_nothing_invented` has no notes,
so it is unchanged too. Keep the helpers' signatures and the existing imports as they are.

## 3. One sentence in `tools/AQUARIUM.md`

In the section `## Datum`, directly after the sentence that begins "Samma regel gäller Arkivets" and ends "vid Ägarens
bord.", add exactly this one sentence and change nothing else in the file:

`Saknar en leveranspost i beslutsloggen datum används datumet i leveransbeskedet för samma åtagande, och posten säger det.`
