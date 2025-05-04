"""
Parse line-level markup.
"""
import re

from pytlopo.config import proto_pattern, witness_pattern, fn_pattern

CF_LINE_PREFIX = 'cf. also'

h1_pattern = re.compile(r'(?P<a>[0-9]+)\.?\s+(?P<title>[A-Z].+)')
h2_pattern = re.compile(r'(?P<a>[0-9]+)(\.|\s)\s*(?P<b>[0-9]+)\.?\s+(?P<title>[A-Z].+)')
h3_pattern = re.compile(r'(?P<a>[0-9]+)(\.|\s)\s*(?P<b>[0-9]+)(\.|\s)\s*(?P<c>[0-9]+)\.?\s+(?P<title>[A-Z].+)')

figure_pattern = re.compile(r'Figure\s+[0-9]+[a-z]*:')


def is_forms_line(line):
    return (proto_pattern.match(line) or
            witness_pattern.match(line) or
            line.strip().startswith(CF_LINE_PREFIX))


def formblock(lines):
    reg, cfs = [], []
    in_cf, cf, cfspec = False, [], None

    for line in lines:
        if line.strip().startswith(CF_LINE_PREFIX):
            in_cf = True
            if cf:  # There's already a previous cf block.
                cfs.append((cfspec, cf))
            cf = []
            cfspec = line.replace(CF_LINE_PREFIX, '').strip().lstrip(':').strip()
            continue
        if in_cf:
            cf.append(line)
        else:
            reg.append(line)
    if cf:
        cfs.append((cfspec, cf))
    return reg, cfs


def etymon(paras):
    pre, forms, post = [], [], []
    for para in paras:
        m = proto_pattern.match(para[0])
        if m:
            assert not forms
            for line in para:
                assert is_forms_line(line), line
            forms = formblock(para)
            continue
        if forms:
            post.append(para)
        else:
            pre.append(para)
    assert forms
    return forms, [' '.join(line.strip() for line in para) for para in pre], [' '.join(line.strip() for line in para) for para in post]


def make_paragraph(lines):
    """
    Lines starting with "|" are a quote.
    If first line is __ul__ ...
    If firts line is __pre__ ...
    Figure ...
    Map ...
    """
    if lines[0].startswith('|'):
        return '> {}'.format(' '.join(line.lstrip('|').strip() for line in lines))
    if lines[0] == '__ul__':
        return '\n'.join('- {}'.format(line) for line in lines[1:])
    if lines[0] == '__pre__':
        return "```\n{}\n```".format('\n'.join(lines[1:]))
    return ' '.join(lines)


def make_chapter(paras):
    """
    If first line starts with footnote pattern, it's the footnote content.
    """
    regular, endnotes = [], []
    for para in paras:
        if fn_pattern.match(para):
            endnotes.append(fn_pattern.sub(lambda m: '[^{}]:'.format(m.group('fn')), para, count=1))
        else:
            regular.append(fn_pattern.sub(lambda m: '[^{}]'.format(m.group('fn')), para))
    return '\n\n'.join(regular + ['\n## Notes'] + endnotes)


def iter_chapters(lines):
    pageno_right_pattern = re.compile(r'\x0c\s+[^0-9]+(?P<no>[0-9]+)')
    pageno_left_pattern = re.compile(r'\x0c(?P<no>[0-9]+)\s+[^0-9]+')
    # replace page numbers with anchors p-...
    # add anchor to sections! s-...
    # Reformat footnotes [^1] and [^1]: ...
    # Turn footnotes into endnotes.
    # Split into markdown docs per chapter. -> remove chapter number from section headings
    chapter, para = [], []
    in_chapter = None
    pageno = -1
    for line in lines:
        m = h1_pattern.match(line)
        if m:
            if in_chapter:
                yield in_chapter, make_chapter(chapter)
            chapter, in_chapter = [], m.group('a')
            continue

        if not in_chapter:
            continue

        m = pageno_left_pattern.fullmatch(line) or pageno_right_pattern.fullmatch(line)
        if m:  # Page number line.
            chapter.append('\n<a id="p-{}"></a>'.format(m.group('no')))
            continue

        m = h2_pattern.match(line)
        if m:
            chapter.append('\n<a id="s-{0}"></a>\n## {0}. {1}\n'.format(m.group('b'), m.group('title')))
            continue

        m = h3_pattern.match(line)
        if m:
            chapter.append('\n<a id="s-{0}-{1}"></a>\n## {0}.{1}. {2}\n'.format(m.group('b'), m.group('c'), m.group('title')))
            continue

        line = line.strip()
        if not line:
            if para:
                chapter.append(make_paragraph(para))
                para = []
        else:
            para.append(line)

    if para:
        chapter.append(make_paragraph(para))
    yield in_chapter, make_chapter(chapter)


def extract_etyma(lines):
    pageno_right_pattern = re.compile(r'\x0c\s+[^0-9]+(?P<no>[0-9]+)')
    pageno_left_pattern = re.compile(r'\x0c(?P<no>[0-9]+)\s+[^0-9]+')
    pageno = -1
    paras, para = [], []
    h1, h2, h3 = None, None, None
    in_etymon = False

    new_lines = []
    for i, line in enumerate(lines, start=1):
        m = pageno_left_pattern.fullmatch(line) or pageno_right_pattern.fullmatch(line)
        if m:  # Page number line.
            pageno = int(m.group('no'))
            assert not in_etymon, pageno
            new_lines.append(line)
            continue

        if not line:  # Empty line.
            if not in_etymon:
                new_lines.append(line)
            else:  # An empty line delimits paragraphs.
                if para:
                    paras.append(para)
                para = []
            continue

        if line == '<':  # Etymon start marker.
            assert not in_etymon, i
            in_etymon = True
            paras, para = [], []
            continue
        if line == '>':  # Etymon end marker.
            if para:
                paras.append(para)
            assert paras, i
            etymon_id = yield h1, h2, h3, pageno, etymon(paras)
            assert in_etymon
            in_etymon = False
            new_lines.append(etymon_id)
            continue

        if not in_etymon:
            m = h1_pattern.match(line)
            if m:
                h1 = (m.group('a'), m.group('title'))
                h2, h3 = None, None
            else:
                m = h2_pattern.match(line)
                if m:
                    assert m.group('a') == h1[0], line
                    h2 = (m.group('b'), m.group('title'))
                    h3 = None
                else:
                    m = h3_pattern.match(line)
                    if m:
                        assert h2 and m.group('b') == h2[0], line
                        h3 = (m.group('c'), m.group('title'))
            new_lines.append(line)
        else:
            para.append(line)
    return new_lines
