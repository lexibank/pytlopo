"""

"""
import re
import functools
import dataclasses


from .parse import (
    proto_pattern, parse_protoform, POC_GRAPHEMES, extract_etyma,
    witness_pattern, iter_glosses, get_quotes, glosses_and_note
)

#
# FIXME: gloss parsing should work with smart quotes as well!
#

TRANSCRIPTION = ('Nɸ'
                 'h'
                 'áàāãæǣɒɒ̄'
                 'fzʔðᵑg'
                 '()[]<>-'
                 'ɣ'
                 'ɔ̀ ɔɔ̄'
                 'vøʷöōòó'
                 'î'  # i circumflex
                 'ĩ'  # i tilde
                 'ì'  # i grave
                 'ī'  # i macron
                 'ɨíIɨ̈ı'
                 'ʈtʰᵐxθbˠŋɳ'
                 'èɛɛ́ ɛ̃ə̄éēêəɛ̃́'
                 'ūüùúʉ'
                 'ñm̀'
                 'ṣẓḍʃ'
                 'čc̣'
                 'ˀɬʌḷȴl̥ʋv̈'
                 'ɯβ'  # LATIN SMALL LETTER TURNED M - used as superscript!
                 'ṛr̃ɾɽ')
B = "ɛ̄"


@dataclasses.dataclass
class Protoform:
    """
    PEOc (POC?)[6] *kori(s), *koris-i- 'scrape (esp. coconuts), grate (esp. coconuts)
    """
    form: str
    glosses: str
    protolanguage: str
    note: str = None
    pfdoubt: bool = False
    pldoubt: bool = False

    def __str__(self):
        return "{} *{} '{}'".format(self.protolanguage, self.form, self.glosses[0] if self.glosses else "")

    @classmethod
    def from_line(cls, line):
        quotes = get_quotes(line)
        kw = {}
        m = proto_pattern.match(line)
        assert m

        kw['protolanguage'] = m.group('pl')
        kw['pfdoubt'] = bool(m.group('pfdoubt'))
        kw['pldoubt'] = bool(m.group('pldoubt'))
        pl, _, rem = line.partition('*')
        if quotes[0] in rem:
            # 1. Find matching end-quote.
            # 2. consume everything in parens after that, iteratively.
            pf, _, rem = rem.partition(quotes[0])
            parse_protoform(pf.strip(), kw['protolanguage'])
        else:
            # FIXME: What to do if there is no gloss?
            pf = ''
        #if kw['protolanguage'] == 'PMP':
        #    print(line, pf)
        #if '1)' in pf:
        #    print(pf.strip())
        """
        usu(q,p), *usu(p)-i 
ubi/*ibu 
tuRi[-J 
tup-a((n,IJ))
tuki- (v)
titey (also *teytey)
tau (ni) waga         - multiple words
taRa(q) (N, V)
sauq ? (N) 
*rabut/*rubat
        """
        kw['form'] = pf.strip()
        kw['glosses'], kw['note'] = glosses_and_note(rem, quotes)
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
        if rem.startswith('|'):
            # multi word marker
            assert rem.count('|') == 2, rem
            word, _, rem = rem[1:].strip().partition('|')
            rem = rem.strip()
        else:
            rem_comps = rem.split()
            word, comma = rem_comps.pop(0), None
            if word.endswith(','):
                word = word[:-1]
                comma = True
            for c in word:
                if c not in ''.join(POC_GRAPHEMES) + TRANSCRIPTION:
                    raise ValueError(c, rem, line)
            if comma:
                word += ', {}'.format(rem_comps.pop(0))
            rem = ' '.join(rem_comps)

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
        #if any('*soka, *soka-i-' in line for line in kw['protoforms']):
        #    for l in kw['reflexes']:
        #        print(l)
        kw['protoforms'] = [Protoform.from_line(pf) for pf in kw['protoforms']]
        reflexes = [Reflex.from_line(langs, line, cf) for line, cf, proto in kw['reflexes'] if not proto]
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
           #'\n\n'.join(self.desc)
           )


class Volume:
    def __init__(self, d, langs):
        self.dir = d
        self.langs = langs

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
            yield Reconstruction.from_data(
                self.langs,
                cat1=h1, cat2=h2, protoforms=protoforms, reflexes=reflexes, page=pageno, desc=desc)
    # FIXME: yield last reconstruction!
