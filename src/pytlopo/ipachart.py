"""
*pʷ         *p          *t            *c           *k         *q
*bʷ         *b          *d            *j           *g
                        *s
*mʷ         *m          *n            *ñ           *ŋ
                        *r                                    *R
                        *dr
                        *l
*w                                    *y

__pre__
            *i                        *u
            *e                        *o
                        *a
"""
from xml.etree import ElementTree as et

from pyclts.ipachart import PulmonicConsonants, VowelTrapezoid, Segment

from .config import POC_GRAPHEMES, POC_BIPA_GRAPHEMES

BIPA_TO_POC_ORTHOGRAPHY = {v: k for k, v in POC_BIPA_GRAPHEMES.items()}


class Consonants(PulmonicConsonants):
    def format_segment(self, e, segment, is_last, is_first):
        if  segment.label in BIPA_TO_POC_ORTHOGRAPHY:
            label = BIPA_TO_POC_ORTHOGRAPHY[segment.label]
        else:
            assert segment.label in POC_GRAPHEMES
            label = segment.label

        ee = et.SubElement(e, 'span')
        ee.text = label
        if not is_last:
            ee.tail = '\xa0'  # pragma: no cover


def consonant_table(clts):
    d = Consonants()
    d.fill_slots([
        Segment.from_sound(clts.bipa[POC_BIPA_GRAPHEMES.get(s, s)])
        for s in POC_GRAPHEMES if s not in "ā kʷ".split()])
    return d.render()[0]
