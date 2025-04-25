"""
Low-level parsing functionality for the pre-processed OCR text of the TloPO volumes.

What about the ca. 50 food plants reconstructions - without witnesses?

comparing with data from Mae:

>>> s1 = "ūŋ-wūŋ"
>>> s2 = "ūŋ-wūŋ"
>>> len(s1)
8
>>> len(s2)
6
>>> import unicodedata
>>> unicodedata.normalize('NFC', s1) == s2
True
>>> unicodedata.normalize('NFD', s2) == s1
True
"""
import re
import unicodedata

from .config import GROUPS, PROTO, POC_GRAPHEMES, POS

__all__ = ['iter_graphemes', 'parse_protoform', 'extract_etyma']

def re_choice(items):
    return r'|'.join(re.escape(i) for i in items)


proto_pattern = re.compile(r'(\((?P<relno>[0-9])\)\s*)?'
                           r'(?P<pl>({}))\s+'
                           r'(?P<root>root\s+)?'
                           r'(?P<pldoubt>\((POC)?\?\)\s*)?'
                           r'(?P<pos>\(({})\)\s*)?'
                           r'(?P<fn>\[[0-9]+]\s+)?'
                           r'(?P<pfdoubt>\?)?\*'.format(re_choice(PROTO), re_choice(POS)))
pos_pattern = re.compile(r'\s*\((?P<pos>{})\)\s*'.format(re_choice(POS)))

fn_pattern = re.compile(r'\[(?P<fn>[0-9]+)]')  # [2]
gloss_number_pattern = re.compile(r'\s*\(\s*(?P<qualifier>i|1|present meaning|E. dialect)\s*\)\s*')  # ( 1 )
CF_LINE_PREFIX = 'cf. also'


def iter_graphemes(s):
    c, prev = None, None
    for c in s:
        cat = unicodedata.name(c).split()[0]
        if cat in {'MODIFIER', 'COMBINING'}:
            assert prev
            yield prev + c
            prev = None
            continue
        if prev:
            yield prev
        prev = c
    if c:
        yield c


def parse_protoform(f, pl, allow_rem=True):
    """
    Assumes a string `f` immediately following a protoform marker `*`. Then consumes graphemes as
    long as they match the grapheme inventory for the proto-language.

    (x)       it cannot be determined whether x was present
    (x,y)     either x or y was present
    [x]       the item is reconstructable in two forms, one with and one without x
    [x,y]     the item is reconstructable in two forms, one with x and one with y
    x-y       x and y are separate morphemes
    x-        x takes an enclitic or a suffix
    <x>       x is an infix
    """
    if f.startswith('|'):  # multi-word protoform
        assert '|' in f[1:]
        f, _, rem = f[1:].partition('|')
        return (
            [' '.join(
                parse_protoform(word, pl, allow_rem=False)[0][0]
                for word in f.strip().split())],
            rem.strip())

    if '((' in f:
        assert '))' in f
        f = f.replace('))', ')')
        f = f.replace('((', '(')

    in_bracket, in_sbracket, in_abracket = False, False, False
    phonemes = POC_GRAPHEMES
    phonemes.append('-')
    phonemes.extend(PROTO[pl])
    form, length = '', 0
    for c in iter_graphemes(f):
        if c == '(':
            in_bracket = True
        elif c == ')':
            assert in_bracket, f
            in_bracket = False
        elif c == '[':
            in_sbracket = True
        elif c == ']':
            assert in_sbracket, f
            in_sbracket = False
        elif c == '<':
            in_abracket = True
        elif c == '>':
            assert in_abracket, f
            in_abracket = False
        elif c == ',':
            if not (in_bracket or in_sbracket):
                length += 1
                break
        elif c == ' ':
            break
        elif c in phonemes:
            pass
        else:
            raise ValueError(c, f, pl)
        length += len(c)
        form += c

    forms = [form]
    rem = f[length:].strip()
    if rem:
        assert allow_rem, f
        if rem.startswith('or '):
            assert rem[2:].strip().startswith('*')
            rem = rem[2:].strip()
        if rem.startswith('*'):
            f2, rem = parse_protoform(rem[1:].strip(), pl)
            forms.extend(f2)
        if rem:
            # FIXME: handle the remainder!
            # next token is a comment or source or a gloss or a doubt marker or a footnote.
            assert rem[0] in "('‘?[", f
    return forms, rem


h1_pattern = re.compile(r'([0-9]+)\.?\s+(?P<title>[A-Z].+)')
h2_pattern = re.compile(r'([0-9]+)(\.|\s)\s*([0-9]+)\.?\s+(?P<title>[A-Z].+)')
h3_pattern = re.compile(r'([0-9]+)(\.|\s)\s*([0-9]+)(\.|\s)\s*([0-9]+)\.?\s+(?P<title>[A-Z].+)')

witness_pattern = re.compile(r'\s+({})(\s*:\s+)'.format('|'.join(re.escape(g) for g in GROUPS)))
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
    return forms, [' '.join(para) for para in pre], [' '.join(para) for para in post]


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
            new_lines.append("<--{}-->".format(etymon_id))
            continue

        if not in_etymon:
            m = h1_pattern.match(line)
            if m:
                h1 = m.group('title')
                h2, h3 = None, None
            else:
                m = h2_pattern.match(line)
                if m:
                    h2 = m.group('title')
                    h3 = None
                else:
                    m = h3_pattern.match(line)
                    if m:
                        h3 = m.group('title')
            new_lines.append(line)
        else:
            para.append(line)
    return new_lines


#---------------------------------


def get_comment(s):
    # Find ( on matching level:
    if s.endswith(')'):
        cmt, level = [], 1
        assert '(' in s, s
        for i, c in enumerate(reversed(s[:-1])):
            if c == ')':
                level += 1
            elif c == '(':
                level -= 1
                if level == 0:
                    break
            cmt.append(c)
        else:
            raise ValueError(s)

        return ''.join(reversed(cmt)).strip(), s[:-i-2].strip()
    return None, s


def glosses_and_note(s, quotes="''"):
        glosses = []
        s = s.replace("n{}s".format(quotes[1]), "n__s")
        rem = s
        while quotes[1] in rem:
            gloss, _, rem = rem.partition(quotes[1])
            assert gloss.strip()
            glosses.append(gloss.strip())
            rem = rem.strip()
            if rem.startswith(","):
                rem = rem[1:].strip()
            if rem.startswith(quotes[0]):
                assert quotes[1] in rem[1:], s
                rem = rem[1:].strip()
            #
            # FIXME: parse nested protoforms ...
            #
            #elif proto_pattern.match(rem):
            #    # POc *bayat 'fence, boundary marker', POc *bayat-i 'make a garden boundary'
            #    #
            #    # FIXME: handle three reconstructions!
            #    #
            #    rec = Reconstruction.from_data(protoform=rem)
            #    glosses.extend(rec.glosses)
            #    break
            else:
                break
        return glosses, rem.strip()


def iter_bracketed_and_gloss(s, quotes):
    i = 0
    while s:
        assert s.startswith('('), s
        br, _, rem = s[1:].partition(')')
        w, _, rem = rem.partition(quotes[0])
        assert not w.strip()
        gl, _, rem = rem.partition(quotes[1])
        yield br.strip(), gl.strip()
        s = rem.strip().lstrip(';').strip()
        i += 1
        if i > 10:
            raise ValueError(s)


def get_quotes(s):
    return "‘’" if "‘" in s else "''"


def iter_glosses(s):
    quotes = "‘’" if "‘" in s else "''"

    def make_gloss(pos=None, gloss=None, fn=None, comment=None, qualifier=None, uncertain=False):
        return dict(
            pos=pos,
            gloss=gloss.replace("__s", quotes[1]) if gloss else gloss,
            fn=fn, comment=comment, qualifier=qualifier, uncertain=bool(uncertain))

    gloss, pos, qualifier, fn, uncertain, comment = None, None, None, None, False, None
    rem = s
    rem = re.sub(r"(?P<c>[a-z]){}s".format(quotes[1]), lambda m: m.group('c') + "__s", rem)
    done = False

    m = pos_pattern.match(rem)
    if m:
        # (N) 'stem' ; (V ) 'steer (a boat from the stem)'
        if re.fullmatch(r"(\([^)]+\)\s*{0}[^{1}]+{1}\s*;?\s*)+".format(quotes[0], quotes[1]), rem):
            for br, gl in iter_bracketed_and_gloss(rem, quotes):
                yield make_gloss(pos=br.replace('v', 'V'), gloss=gl)
            return
        pos = m.group('pos')
        rem = rem[m.end():].strip()

    m = gloss_number_pattern.match(rem)
    if m:
        # FIXME: assign glosses with number and comment
        # FIXME: must handle
        # (E. dialect) 'shed for yams'; (W. dialect) 'house with one side of roof only, made in garden' ; 'a shrine, small house on poles' (= _hare ni asi_)
        if re.fullmatch(r"(\([^)]+\)\s*'[^']+'\s*;?\s*)+", rem):
            for br, gl in iter_bracketed_and_gloss(rem, quotes):
                yield make_gloss(qualifier=br.replace('v', 'V'), gloss=gl)
            return
        qualifier = m.group('qualifier')
        rem = rem[m.end():].strip()

    m = fn_pattern.match(rem)
    if m:
        # FIXME: store fn, or load directly content into comment?
        fn = m.group('fn')
        rem = rem[m.end():].strip()

    if rem.startswith('?'):
        uncertain = True
        rem = rem[1].strip()

    m = fn_pattern.search(rem)
    if m and m.end() == len(rem):  # strip footnote from end.
        assert not fn, s
        fn = m.group('fn')
        rem = rem[:m.start()].strip()

    for src in [
        '(Lewis, 1978:33)',
        '(Chowning)',
        '(Elbert 1972)',
    ]:
        if rem.endswith(src):
            # FIXME: store source
            rem = rem.replace(src, '').strip()

    if rem == '(Horridge)':
        # FIXME: store source
        rem = ''

    if rem.startswith('(') and rem.endswith(')'):
        comment = rem[1:-1].strip()
        rem = ''

    # consume comment or source from the end.
    bcomment, rem = get_comment(rem)
    assert not (comment and bcomment), s
    comment = comment or bcomment

    if rem:
        assert rem[0] == quotes[0], s
        assert rem[-1] == quotes[1], s
        # FIXME: assertion below will work once the two cases above are handled!
        # assert rem[0] == "'" and rem[-1] == "'", line
        if quotes[0] in rem[1:-1]:
            # FIXME: deal with these cases!
            #print(rem)
            pass

    maybe_gloss = rem
    if "'" in maybe_gloss:
        assert maybe_gloss.count("'") >= 2, s
    stuff, _, maybe_gloss = maybe_gloss.partition("'")
    if maybe_gloss.strip():
        gloss = glosses_and_note(maybe_gloss)[0][0]
    if 0:  # stuff.strip():
        if not pos_pattern.fullmatch(stuff) and not gloss_number_pattern.fullmatch(stuff):
            # next part is a question mark, a footnote reference or a comment.
            assert stuff[0] in '?[(', stuff
            # print(words, line)
    yield gloss
