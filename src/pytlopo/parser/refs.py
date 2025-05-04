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

CROSS_REF_PATTERN = re.compile(
    r'(Ch(apter|\.)?\s+(?P<chapter>[0-9]+),\s*)?'
    r'§\s*(?P<section>[0-9]+)'
    r'(\s*\.\s*(?P<subsection>[0-9]+))?'
    r'(\s*\.\s*(?P<subsubsection>[0-9]+))?')


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
    if '(' in matched_string:
        a, _, y = matched_string.partition('(')
        return "[{1}](Source#cldf:{0}) ([{2}](Source#cldf:{0})".format(srcid, a.strip(), y)
    return "[{1}](Source#cldf:{0})".format(srcid, matched_string)


def refs2bib():
    import re
    from clldutils.source import Source
    from clldutils.misc import slug
    refs, key = [], None
    for i, line in enumerate(
            self.raw_dir.joinpath('vol1', 'references.bib').read_text(encoding='utf-8').split('\n'),
            start=1):
        if i % 2 == 1:
            key = line
        else:
            assert key
            refs.append((key, line))
    bib = []
    for key, line in refs:
        line = re.sub(
            r'1\s*(?P<a>[0-9])\s*(?P<b>[0-9])\s*(?P<c>[0-9])(?P<d>[abcde])?\s*,',
            lambda m: '1{}{}{}{},'.format(m.group('a'), m.group('b'), m.group('c'),
                                          m.group('d') or ''),
            line)
        m = re.search(r'(?P<year>([0-9]{4}|forthcoming|n\.d\.|in press))', line)
        assert m
        assert m.group('year') in key
        author = line[:m.start()].strip()
        edp = re.compile(r'\s+ed(s)?\.?,?\s*$')
        ctype = 'author'
        if edp.search(author):
            ctype = 'editor'
            author = author[:m.start()].strip()
        if author.endswith(','):
            author = author[:-1].strip()
        genre = 'misc'
        kw = {ctype: author, 'year': m.group('year'), 'key': key}

        rem = line[m.end():].strip()
        if rem.startswith(','):
            rem = rem.lstrip(',').strip()
        inm = re.search(r'\.\s+In\s+', rem)
        if inm:
            edm = re.search(r',\s+eds?\.?\s*,\s*', rem[inm.end():])
            if edm:
                assert ctype == 'author'
                kw['editor'] = rem[inm.end():inm.end() + edm.start()].replace('1', 'I')
                genre = 'incollection'
                kw['booktitle'] = rem[inm.end() + edm.end():].strip().rstrip('.').strip()
                rem = rem[:inm.start()].strip()

        rem.rstrip('.')
        kw['title'] = rem
        src = Source(genre, slug(key, lowercase=False), **kw)
        print(src.bibtex())
    return
