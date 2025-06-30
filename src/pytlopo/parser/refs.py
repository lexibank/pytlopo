"""
Dyen and Aberle's (1974)
Foley and van Valin (1984)

Haudricourt
and Ozanne-Rivierre (1982)

Lynch and Pat, eds, (1996

Renfrew 1987, 1992)

Green 1967, 1979, 1994a
"""
import re


# match cross-refs
# §4.1.1      -> add chapter!, remove 4th-level hierarchy
# Ch 4, §4.1

# (vol. 1, p.247)
# (vol. 1, pp.293–294)
# vol.1, ch.6, §5.6
# vol.1 (ch.6, §5.6)
# (vol.1, p.80)
# (vol.1:155)
# volume 1 (p.93)
CROSS_REF_PATTERN = re.compile(  # #s-<section>-<subsection>-<subsubsection>
    r'(vol(\.|ume)\s*(?P<volume>[1-5])\s*(?P<sep>,|\()\s*)?'
    r'((C|c)h(apter|\.)?\s*(?P<chapter>[0-9]+),\s*)?'
    r'(§\s*(?P<section>[0-9]+))'
    r'(\s*\.\s*(?P<subsection>[0-9]+))?'
    r'(\s*\.\s*(?P<subsubsection>[0-9]+))?')

CROSS_REF_PATTERN_PAGES = re.compile(  # -> 1 #p-<page>
    r'(vol(\.|ume)\s*(?P<volume>[1-5])\s*(?P<sep>,|\())\s*pp?\.\s*(?P<page>[0-9]+)')

#
# match reconstruction refs: "POc *paus, *paus-i- 'weave, plait'"
#


def key_to_regex(key, in_text=True):
    #
    # FIXME: match "(after Blust ...)", "(from French-Wright ...)"!
    # (Milke 1968: *paRaRa)
    #
    comps = key.split()
    if len(comps) > 1:
        authors = r'\s+'.join([re.escape(c) if c not in {'&', 'and'} else r'(and|&)' for c in comps[:-1]])
        year = comps[-1]
        if in_text:
            return re.compile(r"{}('s)?(,\s*eds?,\s*)?\s*\(?{}".format(authors, year))
        return re.compile(r"\(((?P<qualifier>after|from)\s+)?{}('s)?(,\s*eds?,\s*)?\s*{}(\s*\:\s*(?P<pages>[^,;\)]+))?\)".format(authors, year))
    if in_text:
        return re.compile(r"\s+{}(\s|\.|,)".format(comps[0]))
    return re.compile(r"\({}\)".format(comps[0]))


def search(s, *keys):
    for key in keys:
        for m in key_to_regex(key).finditer(s):
            print(key, s[m.start():m.end()])


def repl_ref(srcid, m):
    matched_string = m.string[m.start():m.end()]

    # Figure out if we are already within a link label!
    for i in range(30):
        c = m.string[m.start() - i - 1]
        if c == ']':
            break
        if c == '[':
            # We are in a link label! Don't replace anything!
            return matched_string

    if '(' in matched_string:
        a, _, y = matched_string.partition('(')
        return "[{1}](Source#cldf:{0}) ([{2}](Source#cldf:{0})".format(srcid, a.strip(), y)
    if ' ' in matched_string or all(c.isupper() for c in matched_string):
        return "[{1}](Source#cldf:{0})".format(srcid, matched_string)
    return matched_string


def refs2bib(lines):  # pragma: no cover
    from clldutils.misc import slug
    refs, author = [], None
    keys = set()
    for i, line in enumerate(lines, start=1):
        if re.match(r'——\s*,', line):
            assert author
            author, dis, src = line2bibtex(i, re.sub(r'^——\s*,\s*', author + ' ', line))
        else:
            author, dis, src = line2bibtex(i, line)
        key = src.refkey(year_brackets=None) + (dis or '')
        if key == 'Clark 1973' and 'Herbert' in line:
            key = 'H. Clark 1973'
        assert slug(key) not in keys, (key, line, author)
        keys.add(slug(key))
        src['key'] = key
        src.id = slug(key, lowercase=False)
        print(src.bibtex())


def line2bibtex(i, line):  # pragma: no cover
    from pycldf.sources import Source
    bib = []
    m = re.search(r'(?P<year>([0-9]{4}(\-[0-9]+)?(a|b)?)|forthcoming|n\.d\.|in press|in preparation|In progress|ongoing)', line)
    assert m, line
    raw_author = line[:m.start()].strip()
    author = raw_author
    disambiguation = None

    edp = re.compile(r'\s+ed(s)?\.?,?\s*$')
    ctype = 'author'
    if edp.search(author):
        ctype = 'editor'
        author = author[:m.start()].strip()
    if author.endswith(','):
        author = author[:-1].strip()
    genre = 'misc'
    kw = {ctype: author, 'year': m.group('year')}

    rem = line[m.end():].strip()
    if rem[0] in "abcdefgh":
        disambiguation, rem = rem[0], rem[1:].strip()

    if rem.startswith(','):
        rem = rem.lstrip(',').strip()
    inm = re.search(r'\.\s+In\s+', rem)
    if inm:
        edm = re.search(r',\s+eds?\.?(\s*,)?\s+', rem[inm.end():])
        if edm:
            assert ctype == 'author', (rem, line)
            kw['editor'] = rem[inm.end():inm.end() + edm.start()].replace('1', 'I')
            genre = 'incollection'
            kw['booktitle'] = rem[inm.end() + edm.end():].strip().rstrip('.').strip()
            rem = rem[:inm.start()].strip()

    rem.rstrip('.')
    kw['title'] = rem.lstrip('.').strip()
    src = Source(genre, str(i), **kw)
    return raw_author, disambiguation, src
