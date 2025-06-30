"""
Parse line-level markup.
"""
import re
import functools

from tabulate import tabulate

from pytlopo.config import proto_pattern, witness_pattern, fn_pattern

CF_LINE_PREFIX = 'cf. also'

h1_pattern = re.compile(r'(?P<a>[0-9]+)\.?\s+(?P<title>[A-Z].+)')
h2_pattern = re.compile(r'(?P<a>[0-9]+)(\.|\s)\s*(?P<b>[0-9]+)\.?\s+(?P<title>[A-Z].+)')
h3_pattern = re.compile(r'(?P<a>[0-9]+)(\.|\s)\s*(?P<b>[0-9]+)(\.|\s)\s*(?P<c>[0-9]+)\.?\s+(?P<title>[A-Z].+)')
h4_pattern = re.compile(r'(?P<a>[0-9]+)(\.|\s)\s*(?P<b>[0-9]+)(\.|\s)\s*(?P<c>[0-9]+)(\.|\s)\s*(?P<d>[0-9]+)\.?\s+(?P<title>[A-Z].+)')

figure_pattern = re.compile(r'Figure\s+[0-9]+[a-z]*(\.[0-9])?:')
map_pattern = re.compile(r'(?P<type>Map|Figure)\s+(?P<num>[0-9]+[a-z]*(\.[0-9])?):')


def is_forms_line(line):
    return (re.match('-[A-Z]', line) or
            (proto_pattern.match(line) or
            witness_pattern.match(line) or
            line.strip().startswith(CF_LINE_PREFIX)))


def formblock(lines):
    reg, cfs = [], []
    in_cf, cf, cfspec = False, [], None

    for line in lines:
        assert is_forms_line(line), line
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


def igt_group(lines):
    return lines
    assert len(lines) % 3 == 1
    assert re.match(r'\([0-9]+\)', lines[0])
    return lines[0], [lines[i:i + 3] for i in range(0, len(lines), 3)]


def make_paragraph(lines, voldir):
    """
    Lines starting with "|" are a quote.
    If first line is __ul__ ...
    If firts line is __pre__ ...
    Figure ...
    Map ...
    """
    if lines[0].startswith('|'):
        return '> {}'.format(' '.join(line.lstrip('|').strip() for line in lines))
    if lines[0] == '__blockquote__':
        return '> {}'.format(' '.join(line.strip() for line in lines[1:]))
    if lines[0] == '__formgroup__':
        for line in lines[1:]:
            assert is_forms_line(line) or '**' in line, line
        #print(len(line[1:]))
        return '\n'.join('' if line.strip() == '#' else line for line in lines[1:])
    if lines[0] == '__ul__':
        return '\n'.join('- {}'.format(line.strip()) for line in lines[1:])
    if lines[0] == '__block__':
        return '\n'.join('' if line.strip() == '#' else line for line in lines[1:])
    if len(lines) > 1 and lines[1].strip().startswith(':'):
        # A definition list
        return '\n'.join(lines)
    if lines[0] == '__pre__':
        return "```\n{}\n```".format('\n'.join(lines[1:]))
    if lines[0] == '__table__':
        return tabulate(
            [[s.strip() or ' ' for s in l.split('|')] for l in lines[2:]],
            headers=[s.strip() or ' ' for s in lines[1].split('|')],
            tablefmt='pipe')
    if lines[0] == '__tablenh__':
        return tabulate(
            [[s.strip() or ' ' for s in l.split('|')] for l in lines[1:]],
            headers=[' '] * len(lines[1].split('|')),
            tablefmt='pipe')
    # __formset__, figure, map. __html__
    m = map_pattern.match(lines[0])
    if m:  # Turn figures and maps into CLDF Markdown links referencing MediaTable items.
        mtype = 'map' if m.group('type').lower() == 'map' else 'fig'
        fid = '{}-{}-{}'.format(
            mtype,
            voldir.name.replace('vol', ''),
            m.group('num').replace('.', '_'))
        p = voldir / 'maps' / '{}_{}.png'.format(mtype, m.group('num'))
        if p.exists():
            caption = ' '.join(l.strip() for l in lines)
            return """\
<a id="{}"> </a>

[{}](MediaTable#cldf:{})

""".format(fid, caption, fid)
    return ' '.join(l.strip() for l in lines)


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


def iter_chapters(lines, voldir):
    from pytlopo.parser.forms import strip_footnote_reference

    pageno_right_pattern = re.compile(r'\x0c\s+[^0-9]+(?P<no>[0-9]+)')
    pageno_left_pattern = re.compile(r'\x0c(?P<no>[0-9]+)\s+[^0-9]+')
    # replace page numbers with anchors p-...
    # add anchor to sections! s-...
    # Reformat footnotes [^1] and [^1]: ...
    # Turn footnotes into endnotes.
    # Split into markdown docs per chapter. -> remove chapter number from section headings
    chapter, toc, para = [], [], []
    in_chapter = None
    pageno = -1
    for line in lines:
        m = h1_pattern.match(line)
        if m:
            if in_chapter:
                yield in_chapter, make_chapter(chapter), toc
            chapter, toc, in_chapter = [], [], m.group('a')
            continue

        if not in_chapter:
            continue

        m = pageno_left_pattern.fullmatch(line) or pageno_right_pattern.fullmatch(line)
        if m:  # Page number line.
            chapter.append('\n<a id="p-{}"></a>'.format(m.group('no')))
            continue

        m = h2_pattern.match(line)
        if m:
            link = 's-{b}'.format(**m.groupdict())
            number = '{b}.'.format(**m.groupdict())
            title = '{title}'.format(**m.groupdict())
            chapter.append('\n<a id="{}"></a>\n\n## {} {}\n'.format(link, number, title))
            toc.append((1, link, strip_footnote_reference(title)[0]))
            continue

        m = h3_pattern.match(line)
        if m:
            link = 's-{b}-{c}'.format(**m.groupdict())
            number = '{b}.{c}.'.format(**m.groupdict())
            title = '{title}'.format(**m.groupdict())
            chapter.append('\n<a id="{}"></a>\n\n### {} {}\n'.format(link, number, title))
            toc.append((2, link, strip_footnote_reference(title)[0]))
            continue

        m = h4_pattern.match(line)
        if m:
            link = 's-{b}-{c}-{d}'.format(**m.groupdict())
            number = '{b}.{c}.{d}.'.format(**m.groupdict())
            title = '{title}'.format(**m.groupdict())
            chapter.append('\n<a id="{}"></a>\n\n#### {} {}\n'.format(link, number, title))
            toc.append((3, link, strip_footnote_reference(title)[0]))
            continue

        if not line.strip():
            if para:
                chapter.append(make_paragraph(para, voldir))
                para = []
        else:
            para.append(line)

    if para:
        chapter.append(make_paragraph(para, voldir))
    yield in_chapter, make_chapter(chapter), toc


def extract_blocks(lines, factory=formblock, start='<', end='>'):
    pageno_right_pattern = re.compile(r'\x0c\s+[^0-9]+(?P<no>[0-9]+)')
    pageno_left_pattern = re.compile(r'\x0c(?P<no>[0-9]+)\s+[^0-9]+')
    pageno = -1
    block = []
    h1, h2, h3 = None, None, None
    in_block = False

    new_lines = []
    for i, line in enumerate(lines, start=1):
        m = pageno_left_pattern.fullmatch(line) or pageno_right_pattern.fullmatch(line)
        if m:  # Page number line.
            pageno = int(m.group('no'))
            assert not in_block, pageno
            new_lines.append(line)
            continue

        if not line:  # Empty line.
            if not end and in_block:  # implicit end of block
                assert block, i
                etymon_id = yield h1, h2, h3, pageno, factory(block)
                in_block = False
                new_lines.append(etymon_id)
                new_lines.append('')
                continue

            #assert not in_block, pageno
            if not in_block:
                new_lines.append(line)
            continue

        if line == start:  # Etymon start marker.
            assert not in_block, i
            in_block = True
            block = []
            continue
        if end and line == end:  # Etymon end marker.
            assert block, i
            etymon_id = yield h1, h2, h3, pageno, factory(block)
            assert in_block, i
            in_block = False
            new_lines.append(etymon_id)
            continue

        if not in_block:
            m = h1_pattern.match(line)
            if m:
                h1 = (m.group('a'), m.group('title'))
                h2, h3 = None, None
            else:
                m = h2_pattern.match(line)
                if m:
                    assert h1, line
                    assert m.group('a') == h1[0], (line, h1)
                    h2 = (m.group('b'), m.group('title'))
                    h3 = None
                else:
                    m = h3_pattern.match(line)
                    if m:
                        assert h2 and m.group('b') == h2[0], line
                        h3 = (m.group('c'), m.group('title'))
            new_lines.append(line)
        else:
            block.append(line)
    return new_lines


extract_etyma = extract_blocks
extract_igts = functools.partial(extract_blocks, factory=igt_group, start='__igt__', end=None)
extract_formgroups = functools.partial(extract_blocks, factory=lambda lines: lines, start='__formgroup__', end=None)
