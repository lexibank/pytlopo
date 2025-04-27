"""

"""
import re
import functools
import dataclasses

from pycldf.sources import Sources

from .config import TRANSCRIPTION, proto_pattern, witness_pattern
from pytlopo.parser.forms import (
    parse_protoform, POC_GRAPHEMES, iter_graphemes, iter_glosses, get_quotes,
    strip_footnote_reference, strip_comment, strip_pos,
)
from pytlopo.parser.lines import extract_etyma
from pytlopo.parser import refs


@dataclasses.dataclass
class Protoform:
    """
    PEOc (POC?)[6] *kori(s), *koris-i- 'scrape (esp. coconuts), grate (esp. coconuts)
    """
    forms: list
    glosses: str
    protolanguage: str
    note: str = None
    pfdoubt: bool = False
    pldoubt: bool = False
    pos: str = None

    def __str__(self):
        return "{} *{} '{}'".format(
            self.protolanguage,
            ', '.join('*' + f for f in self.forms),
            self.glosses[0] if self.glosses else "")

    @classmethod
    def from_line(cls, line):
        quotes = get_quotes(line)
        kw = {'glosses': []}
        m = proto_pattern.match(line)
        assert m

        kw['protolanguage'] = m.group('pl')
        kw['pfdoubt'] = bool(m.group('pfdoubt'))
        kw['pldoubt'] = bool(m.group('pldoubt'))
        kw['pos'] = m.group('pos') or None
        # FIXME: root, fn!
        rem = line[m.end(0):].strip()
        forms, rem = parse_protoform(rem, kw['protolanguage'])
        "('‘?["
        if rem.startswith('?'):
            kw['pfdoubt'] = True
            rem = rem[1:].strip()
            if rem:
                assert rem[0] in "('‘["

        rem, fn, fnpos = strip_footnote_reference(rem)
        if rem:
            assert rem[0] in "('‘"

        rem, gpos = strip_pos(rem)

        cmt, rem = strip_comment(rem, 'start')
        if rem:
            assert rem[0] in "('‘", line  # There might be a third bracketed item, source.

            if rem[0] == '(':
                src, rem = strip_comment(rem, 'start')
            if rem:
                assert rem[0] in "'‘", line
                # Now consume the gloss.
                kw['glosses'] = [next(iter_glosses(rem))]

        kw['forms'] = forms
        return cls(**kw)


@dataclasses.dataclass
class Reflex:
    group: str
    lang: str
    form: str
    gloss: str = None
    cf: bool = False
    pos: str = None

    # FIXME: must allow multiple glosses -> (gloss, comment or source, pos)

    def __str__(self):
        return "\t{}: {}\t{}\t'{}'".format(self.group, self.lang, self.form, self.gloss or '')

    @classmethod
    def from_line(cls, langs, line, cf):
        # old meaning|W. dialect

        lang, word, gloss, pos = None, None, None, None
        group, _, rem = line.partition(':')
        rem_words = rem.strip().split()
        for lg in sorted(langs, key=lambda l: -len(l)):
            lg = lg.split()
            if rem_words[:len(lg)] == lg:
                lang = ' '.join(lg)
                for word in lg:
                    rem = rem.lstrip(' ')
                    assert rem.startswith(word), rem
                    rem = rem[len(word):].strip()
                break
        # get the next word:
        if re.match(r'\s*\[[0-9]]\s*', rem):  # footnote_pattern!
            fnref, _, rem = rem.partition(']')
            # FIXME: handle footnote.
        rem = rem.strip()
        if rem.startswith('|'):  # multi word marker
            assert rem.count('|') == 2, rem
            word, _, rem = rem[1:].strip().partition('|')
            rem = rem.strip()
            words = word.split()
        else:
            rem_comps = rem.split()
            word, comma = rem_comps.pop(0), None
            if word.endswith(','):
                word = word[:-1]
                comma = True
            words = [word]
            if comma:
                w2 = rem_comps.pop(0)
                words.append(w2)
                word += ', {}'.format(w2)
            rem = ' '.join(rem_comps)

        for w in words:
            for c in iter_graphemes(w):
                if c != ',':
                    if c not in POC_GRAPHEMES + TRANSCRIPTION:
                        raise ValueError(c, rem, line)

        gloss = next(iter_glosses(rem))

        assert lang, line
        return cls(group=group.strip(), lang=' '.join(lg), form=word, gloss=gloss, cf=cf, pos=pos)


@dataclasses.dataclass
class Reconstruction:
    protoforms: list
    reflexes: list = None
    cat1: str = ''
    cat2: str = ''
    page: int = 0
    desc: list = None

    @classmethod
    def from_data(cls, langs, **kw):
        # if any('*soka, *soka-i-' in line for line in kw['protoforms']):
        #    for l in kw['reflexes']:
        #        print(l)
        kw['protoforms'] = [Protoform.from_line(pf) for pf in kw['protoforms']]
        reflexes = [Reflex.from_line(langs, line, cf) for line, cf, proto in kw['reflexes'] if
                    not proto]
        for line, cf, proto in kw['reflexes']:
            if proto:
                try:
                    assert not cf, kw
                    kw['protoforms'].append(Protoform.from_line(line))
                except AssertionError:
                    #
                    # FIXME: what to do with protoforms in cf tables? Just list as reflexes in protolanguages?
                    #
                    pass
        kw['reflexes'] = reflexes
        return cls(**kw)

    def __str__(self):
        return """\
{} / {} / Page {}
{}
{}
""".format(self.cat1, self.cat2, self.page,
           '\n'.join(str(pf) for pf in self.protoforms),
           '\n'.join(str(w) for w in self.reflexes),
           # '\n\n'.join(self.desc)
           )


class Volume:
    def __init__(self, d, langs):
        self.dir = d
        self.langs = langs

    #
    # FIXME:
    # - access references.bib
    # - search/replace refs in text
    #
    @functools.cached_property
    def sources(self):
        return Sources.from_file(self.dir / 'references.bib')

    @functools.cached_property
    def source_pattern_dict(self):
        return {src.id: refs.key_to_regex(src['key']) for src in self.sources}

    def replace_refs(self, s):
        for srcid, pattern in self.source_pattern_dict.items():
            for m in pattern.finditer(s):
                print(m.string[m.start():m.end()])

    @functools.cached_property
    def reconstructions(self):
        return list(self._iter_reconstructions(
            self.dir.joinpath('text.txt').read_text(encoding='utf8').split('\n')))

    def _iter_reconstructions(self, lines):
        for h1, h2, h3, pageno, paras in extract_etyma(lines):
            forms, pre, post = paras
            forms, cfs = forms

            protoforms = []
            reflexes = []
            desc = pre + post

            for line in forms:
                if proto_pattern.match(line):
                    protoforms.append(line)
                elif witness_pattern.match(line):
                    reflexes.append((line, False, False))
                else:
                    raise ValueError(line)

            assert protoforms, paras

            for p in desc:
                self.replace_refs(p)

            yield Reconstruction.from_data(
                self.langs,
                cat1=h1, cat2=h2, protoforms=protoforms, reflexes=reflexes, page=pageno, desc=desc)
    # FIXME: yield last reconstruction!
