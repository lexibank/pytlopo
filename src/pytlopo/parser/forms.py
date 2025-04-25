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
import typing
import unicodedata

from pytlopo.config import PROTO, POC_GRAPHEMES, POS, re_choice

__all__ = ['iter_graphemes', 'parse_protoform', 'strip_comment', 'strip_footnote_reference']

pos_pattern = re.compile(r'\s*\((?P<pos>{})\)\s*'.format(re_choice(POS)))

fn_pattern = re.compile(r'\[(?P<fn>[0-9]+)]')  # [2]
gloss_number_pattern = re.compile(r'\s*\(\s*(?P<qualifier>i|1|present meaning|E. dialect)\s*\)\s*')  # ( 1 )


def strip_pos(rem):
    pos = None
    m = pos_pattern.match(rem)
    if m:
        rem = rem[m.end():].strip()
        pos = m.group('pos')
    return rem, pos

def strip_footnote_reference(rem):
    fn, position = None, None
    m = fn_pattern.match(rem)
    if m:
        fn = m.group('fn')
        rem = rem[m.end():].strip()
        position = 'start'
    else:
        m = fn_pattern.search(rem)
        if m and m.end() == len(rem):  # strip footnote from end.
            fn = m.group('fn')
            rem = rem[:m.start()].strip()
            position = 'end'
    return rem, fn, position


def strip_comment(s, position='end'):
    if position == 'end':
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
    else:
        assert position == 'start'
        if s.startswith('('):
            cmt, level = [], 1
            for i, c in enumerate(s[1:]):
                if c == '(':
                    level += 1
                elif c == ')':
                    level -= 1
                    if level == 0:
                        break
                cmt.append(c)
            else:
                raise ValueError(s)
            return ''.join(cmt).strip(), s[i+2:].strip()
    return None, s


def iter_graphemes(s):
    g, left = '', ''
    for c in s:
        cat = unicodedata.name(c).split()[0]
        if cat not in {'MODIFIER', 'COMBINING'}:
            if g:
                yield g
            if left:
                g = left + c
                left = ''
            else:
                g = c
        else:
            if cat == 'MODIFIER' and g in 'iau':
                left += c
            elif g and any(unicodedata.category(cc) == 'Ll' for cc in g):
                g += c
            else:
                left += c
    if g:
        yield g


def parse_protoform(f, pl, allow_rem=True) -> typing.Tuple[typing.List[str], str]:
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
        pos2 = None
        if pos_pattern.match(rem) and rem.partition(')')[2].strip().startswith('*'):
            rem, pos2 = strip_pos(rem)
        if rem.startswith('*'):
            # FIXME: add pos spec to forms!
            # PWOc (N LOC) *pa, (ADV) *qa-pa ‘to one’s left when facing the sea’
            f2, rem = parse_protoform(rem[1:].strip(), pl)
            forms.extend(f2)
        if rem:
            # FIXME: handle the remainder!
            # next token is a comment or source or a gloss or a doubt marker or a footnote.
            assert rem[0] in "('‘?[", f
    return forms, rem


def glosses_and_note(s, quotes="''"):
    """
    Chop off comma-separated glosses.
    """
    glosses = []
    rem = s
    while quotes[1] in rem:
        gloss, _, rem = rem.partition(quotes[1])
        assert gloss.strip(), s
        glosses.append(gloss.strip())
        rem = rem.strip()
        if rem.startswith(","):
            rem = rem[1:].strip()
        if rem.startswith(quotes[0]):
            assert quotes[1] in rem[1:], s
            rem = rem[1:].strip()
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
    rem = re.sub(r"(?P<c>[a-z\.]){}s".format(quotes[1]), lambda m: m.group('c') + "__s", rem)
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

    rem, fn, fnpos = strip_footnote_reference(rem)
    if rem.startswith('?'):
        uncertain = True
        rem = rem[1].strip()

    for src in [
        '(Lewis, 1978:33)',
        '(Chowning)',
        '(Elbert 1972)',
        '(Lichtenberk 1994)',
        '(ACD)',
        '(Grace 1969)',
        '(Horridge)',
    ]:
        if rem.endswith(src):
            # FIXME: store source
            rem = rem.replace(src, '').strip()

    if rem.startswith('(') and rem.endswith(')'):
        comment = rem[1:-1].strip()
        rem = ''

    # consume comment or source from the end.
    bcomment, rem = strip_comment(rem)
    assert not (comment and bcomment), s
    comment = comment or bcomment

    if rem:
        assert rem[0] == quotes[0], s
        assert rem[-1] == quotes[1], s
        # FIXME: assertion below will work once the two cases above are handled!
        # assert rem[0] == "'" and rem[-1] == "'", line
        if quotes[0] in rem[1:-1]:
            # FIXME: deal with these cases!
            #print(rem, s)
            pass

    maybe_gloss = rem
    if "'" in maybe_gloss:
        assert maybe_gloss.count("'") >= 2, s
    stuff, _, maybe_gloss = maybe_gloss.partition(quotes[0])
    if maybe_gloss.strip():
        gloss, rem = glosses_and_note(maybe_gloss[1:], quotes)
        if rem:
            # FIXME: Categories:
            # if rem.startswith(';') -> additional gloss in reflexes
            # if rem.startswith('*') -> additional proto-form
            #if rem[0] not in '*;':
            #    print(rem, s)
            pass
        gloss = gloss[0]  # FIXME: There may be more!
    if 0:  # stuff.strip():
        if not pos_pattern.fullmatch(stuff) and not gloss_number_pattern.fullmatch(stuff):
            # next part is a question mark, a footnote reference or a comment.
            assert stuff[0] in '?[(', stuff
            # print(words, line)
    yield gloss
