"""

"""
import re
import typing
import functools
import dataclasses

from pycldf.sources import Sources, Source
from clldutils.misc import slug

from .config import TRANSCRIPTION, proto_pattern, witness_pattern
from pytlopo.parser.forms import (
    parse_protoform, POC_GRAPHEMES, iter_graphemes, iter_glosses, get_quotes,
    strip_footnote_reference, strip_comment, strip_pos, pos_pattern
)
from pytlopo.parser.lines import extract_etyma, iter_chapters
from pytlopo.parser import refs


@dataclasses.dataclass
class Reference:
    id: str
    label: str
    pages: str = None

    def __str__(self):
        return '[{}]({})'.format(self.label, self.id)

    @property
    def cldf_id(self):
        res = self.id
        if self.pages:
            assert '[' not in self.pages
            res += '[{}]'.format(self.pages)
        return res


def comment_or_sources(vol, cmt):
    """
    If `cmt` can be parsed as comma-separated list of references, these are returned.
    """
    srcs, with_pages = [], False
    for chunk in cmt.split(','):
        chunk = chunk.strip()
        res = vol.match_ref(chunk)
        if res:
            if res[1]:
                with_pages = True
            srcs.append(Reference(res[0], chunk, res[1]))
        else:  # We connot match the chunk.
            return cmt, None
    return None, srcs


@dataclasses.dataclass
class Gloss:
    gloss: str
    comment: str = None
    sources: typing.List[Reference] = None
    number: str = None
    pos: str = None
    fn: str = None

    @classmethod
    def from_dict(cls, vol, d):
        d['sources'] = []
        if d['comments']:
            cmts = []
            for cmt in d['comments']:
                cmt, srcs = comment_or_sources(vol, cmt)
                if cmt:
                    cmts.append(cmt)
                elif srcs:
                    d['sources'] = srcs
            d['comments'] = "; ".join(cmts)

        return cls(
            fn=d['fn'],
            #
            # FIXME: number!?
            #
            pos=d['pos'],
            gloss=d['gloss'],
            comment=d['comments'] or None,
            sources=d['sources'])

    def __str__(self):
        return "{}{}{}{}{}".format(
            '({}) '.format(self.pos or self.number) if self.pos or self.number else '',
            "'{}'".format(self.gloss) if self.gloss else '',
            ' ({})'.format(self.comment) if self.comment else '',
            ' ({})'.format(', '.join(str(s) for s in self.sources)) if self.sources else '',
            ' [{}]'.format(self.fn) if self.fn else '',
        )


@dataclasses.dataclass
class Protoform:
    """
    PEOc (POC?)[6] *kori(s), *koris-i- 'scrape (esp. coconuts), grate (esp. coconuts)
    """
    forms: typing.List[str]
    glosses: typing.List[Gloss]
    protolanguage: str
    comment: str = None
    pfdoubt: bool = False
    pldoubt: bool = False
    pos: str = None
    sources: typing.List[Reference] = None

    def __str__(self):
        return "{}\t{}\t{}{}\t{}".format(
            self.protolanguage,
            ', '.join('*' + f for f in self.forms),
            '({})'.format(self.comment) if self.comment else '',
            '({})'.format(', '.join(str(s) for s in self.sources)) if self.sources else '',
            "; ".join(str(g) for g in self.glosses),
        )

    @classmethod
    def from_line(cls, vol, line):
        # FIXME: could store the quoting type with vol!?
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

        rem, fn, fnpos = strip_footnote_reference(rem, start_only=True)
        if rem:
            assert rem[0] in "('‘", rem

        cmt, rem = strip_comment(rem, 'start')
        if cmt == '1' or pos_pattern.fullmatch("({})".format(cmt)):
            # It's part of the glosses.
            if rem.startswith('(?)'):
                # POc *qatu(R) (N) (?) ‘number of things in a line, row’
                kw['pfdoubt'] = True  # ?
                rem = rem[3:].strip()
            assert rem[0] in "'‘", line
            pass
            rem = '({}) {}'.format(cmt, rem)
        elif cmt == '?':
            assert rem[0] in "'‘", line
            kw['pfdoubt'] = True
        elif cmt:
            # Check whether it's a source or comma-separated list of sources!
            # PMP *bubuŋ (Dempwolff 1938, Zorc 1994) 'ridgepole, ridge of the roof'
            cmt, srcs = comment_or_sources(vol, cmt)
            if cmt:
                kw['comment'] = cmt
            elif srcs:
                kw['sources'] = srcs
        elif rem:
            assert rem[0] in "'‘", line

        if rem:
            # Now consume the gloss.
            kw['glosses'] = [Gloss.from_dict(vol, g) for g in iter_glosses(rem)]

        kw['forms'] = forms
        return cls(**kw)


@dataclasses.dataclass
class Reflex:
    group: str
    lang: str
    form: str
    lfn: str = None  # Footnote with comment about the language.
    ffn: str = None  # Footnote with comment about the form.
    glosses: typing.List[Gloss] = None
    cf: bool = False

    def __str__(self):
        return "\t{}: {}{}\t{}{}\t{}".format(
            self.group,
            self.lang,
            ' [{}]'.format(self.lfn) if self.lfn else '',
            self.form,
            ' [{}]'.format(self.ffn) if self.ffn else '',
            "; ".join(str(g) for g in self.glosses),
            #"\t({})".format(self.comment) if self.comment else '',
        )

    @classmethod
    def from_line(cls, vol, line, cf):
        lang, word, gloss, pos = None, None, None, None
        group, _, rem = line.partition(':')
        rem_words = rem.strip().split()
        for lg in sorted(vol.langs, key=lambda l: -len(l)):
            lg = lg.split()
            if rem_words[:len(lg)] == lg:
                lang = ' '.join(lg)
                for word in lg:
                    rem = rem.lstrip(' ')
                    assert rem.startswith(word), rem
                    rem = rem[len(word):].strip()
                break
        # get the next word:
        rem, lfn, _ = strip_footnote_reference(rem, start_only=True)
        if rem.startswith('|'):  # multi word marker
            assert rem.count('|') == 2, rem
            word, _, rem = rem[1:].strip().partition('|')
            rem = rem.strip()
            words = word.split()
        else:
            rem_comps = rem.split()
            try:
                word, comma = rem_comps.pop(0), None
            except:
                raise ValueError(line)
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

        rem, ffn, pos = strip_footnote_reference(rem, start_only=True)
        assert lang, line
        return cls(
            group=group.strip(),
            lang=' '.join(lg),
            form=word,
            glosses=[Gloss.from_dict(vol, g) for g in iter_glosses(rem)],
            cf=cf,
            lfn=lfn,
            ffn=ffn,
            #pos=pos,
            #comment=gloss['comment']
        )


def markdown_escape(s):
    for k, v in {
        "*": "&ast;",
        "[": "&#91;",
        "]": "&#93;",
    }.items():
        s = s.replace(k, v)
    return s


@dataclasses.dataclass
class Reconstruction:
    protoforms: list
    reflexes: list = None
    chapter: tuple = None
    section: tuple = None
    subsection: tuple = None
    page: int = 0
    pre: list = None
    post: list = None
    cfs: list = None
    footnotes: dict = None
    disambiguation: str = 'a'

    def key(self):
        if not self.section:
            print(self)
            raise ValueError
        return (
            self.chapter[0],
            self.section[0] if self.section else None,
            self.subsection[0] if self.subsection else None,
            self.page,
            slug(self.protoforms[0].protolanguage, lowercase=False),
            slug(self.protoforms[0].forms[0]),
            self.disambiguation,
        )

    @property
    def id(self):
        return '-'.join(str(s) for s in self.key())

    def __hash__(self):
        return hash(self.key())

    def cldf_markdown_link(self):
        return '[{} &ast;_{}_](CognatesetTable#cldf:{})\n'.format(
            self.protoforms[0].protolanguage,
            markdown_escape(self.protoforms[0].forms[0]),
            self.id)

    @classmethod
    def from_data(cls, vol, h1, h2, h3, pageno, paras):
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
            vol.replace_refs(p)

        kw = dict(
            terminology=(h1, h2, h3),
            protoforms=protoforms,
            reflexes=reflexes,
            page=pageno,
            cfs=cfs,
            pre=pre,
            post=post,
        )
        kw['protoforms'] = [Protoform.from_line(vol, pf) for pf in kw['protoforms']]
        reflexes = [Reflex.from_line(vol, line, cf) for line, cf, proto in kw['reflexes'] if
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
        kw['cfs'] = [(cfspec, [Reflex.from_line(vol, line, True) for line in cf
                               if not proto_pattern.match(line)  # FIXME!!!!
                               ]) for cfspec, cf in kw['cfs'] or []]
        kw['reflexes'] = reflexes
        kw['footnotes'], post = {}, []
        for par in kw['post']:
            rem, fn, _ = strip_footnote_reference(par, start_only=True)
            if fn:
                kw['footnotes'][fn] = vol.replace_refs(rem)
            else:
                post.append(vol.replace_refs(par))
        kw['post'] = post
        kw['chapter'], kw['section'], kw['subsection'] = kw.pop('terminology')
        return cls(**kw)

    def __str__(self):
        res = """\
{} / {} / {} / Page {}
{}
{}
{}
""".format(
            '{0[0]}. {0[1]}'.format(self.chapter) if self.chapter else '',
            '{0[0]}. {0[1]}'.format(self.section) if self.section else '',
            '{0[0]}. {0[1]}'.format(self.subsection) if self.subsection else '',
           self.page,
           '\n\n'.join(par.strip() for par in self.pre),
           '\n'.join(str(pf) for pf in self.protoforms),
           '\n'.join(str(w) for w in self.reflexes),
        )
        if self.cfs:
            for cfspec, cf in self.cfs:
                res += '  cf. also:{}\n'.format(' ' + cfspec if cfspec else '')
            for w in cf:
                res += '{}\n'.format(str(w))
        for i, par in enumerate(self.post):
            res += ('\n' if i == 0 else '\n\n') + par
        for k, v in (self.footnotes or {}).items():
            res += '\n\n[{}] {}'.format(k, v)
        return res

    def pre_note(self):
        return '\n\n'.join(par.strip() for par in self.pre)

    def post_note(self):
        res = ''
        for i, par in enumerate(self.post):
            res += ('\n' if i == 0 else '\n\n') + par
        for k, v in (self.footnotes or {}).items():
            res += '\n\n[{}] {}'.format(k, v)
        return res

    def desc(self):
        return self.pre_note() + self.post_note()


def polish_text(text):
    text = re.sub(r'\s*\.\s*\.\s*\.\s*', ' … ', text)
    return text.replace('*', '&ast;')


@dataclasses.dataclass
class Chapter:
    text: str
    bib: Source

    @classmethod
    def from_text(cls, vol, num, text):
        for md in vol.metadata['chapters']:
            if md['number'] == num:
                break
        else:
            raise ValueError('Chapter number {} not found'.format(num))

        bib = Source('incollection', vol.bib.id + '-' + md['number'], **{k: v for k, v in vol.bib.items()})
        bib['booktitle'] = bib.pop('title')
        bib['title'] = md['title']
        bib['author'] = md['author']
        bib['pages'] = md['pages']
        header = "# {}\n\nby {}\n\n".format(md['title'], md['author'])
        return cls(polish_text(header + vol.replace_refs(text, num)), bib)


class Volume:
    def __init__(self, d, langs, bib):
        self.dir = d
        self.langs = langs
        self.metadata = self.dir.read_json('md.json')
        self._lines = None
        bib.id = 'tlopo{}'.format(d.name[-1])
        bib['title'] += ' {}: {}'.format(d.name[-1], self.metadata['title'])
        self.bib = bib

    def __str__(self):
        return self.bib['title']

    @functools.cached_property
    def chapters(self):
        if not self._lines:
            assert self.reconstructions
        return {num: Chapter.from_text(self, num, text) for num, text in iter_chapters(self._lines)}

    #
    # FIXME:
    # - access references.bib
    # - search/replace refs in text
    #
    @functools.cached_property
    def sources(self):
        return Sources.from_file(self.dir / 'references.bib')

    @functools.cached_property
    def source_in_brackets_pattern_dict(self):
        return {src.id: refs.key_to_regex(src['key'], in_text=False) for src in self.sources}

    @functools.cached_property
    def source_pattern_dict(self):
        return {src.id: refs.key_to_regex(src['key']) for src in self.sources}

    def match_ref(self, s):
        if not s.startswith('('):
            s = '({})'.format(s)
        for srcid, pattern in self.source_in_brackets_pattern_dict.items():
            m = pattern.fullmatch(s)
            if m:
                return srcid, m.groupdict().get('pages')

    def replace_refs(self, s, chapter=None):
        for srcid, pattern in self.source_pattern_dict.items():
            s = pattern.sub(functools.partial(refs.repl_ref, srcid), s)
        def repl(m):
            fragment = 's-{}'.format(m.group('section'))
            if m.group('subsection'):
                fragment += '-{}'.format(m.group('subsection'))
            if m.group('chapter') and m.group('chapter') != chapter:
                # cross-chapter reference!
                path = 'chapter{}.md'.format(m.group('chapter'))
            else:
                path = ''
            return '[{}]({}#{})'.format(re.sub(r'\s*\.\s*', '.', m.string[m.start():m.end()]), path, fragment)

        return refs.CROSS_REF_PATTERN.sub(repl, s)

    @functools.cached_property
    def reconstructions(self):
        return list(self._iter_reconstructions(
            self.dir.joinpath('text.txt').read_text(encoding='utf8').split('\n')))

    def _iter_reconstructions(self, lines):
        rids = set()
        etyma = extract_etyma(lines)
        h1, h2, h3, pageno, paras = next(etyma)
        rec = Reconstruction.from_data(self, h1, h2, h3, pageno, paras)
        rids.add(rec.id)
        yield rec
        try:
            while True:
                h1, h2, h3, pageno, paras = etyma.send(rec.cldf_markdown_link())
                rec = Reconstruction.from_data(self, h1, h2, h3, pageno, paras)
                if rec.id in rids:
                    rec.disambiguation = 'b'
                rids.add(rec.id)
                yield rec
        except StopIteration as e:
            self._lines = e.value
