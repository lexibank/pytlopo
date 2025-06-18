import pytest

from pytlopo.parser.forms import *
from pytlopo.parser.lines import extract_etyma


@pytest.mark.parametrize(
    'i,pos,o',
    [
        ('(abc)cde', 'start', ('abc', 'cde')),
        ('( abc ) cde', 'start', ('abc', 'cde')),
        ('( (a) bc ) cde', 'start', ('(a) bc', 'cde')),
        ('cde(abc)', 'end', ('abc', 'cde')),
    ]
)
def test_strip_comment(i, pos, o):
    assert strip_comment(i, pos) == o


@pytest.mark.parametrize(
    'i,o',
    [
        ('a', 'a'),
        ('ab', 'a b'),
        ('äöü', 'ä ö ü'),
        ('aɛ̃a', 'a ɛ̃ a'),
    ]
)
def test_iter_graphemes(i, o):
    """
    list(iter_graphemes('ᵑgu-ᵑgum'))
['ᵑg', 'u', '-', 'ᵑg', 'u', 'm']
list(iter_graphemes('buar̃a'))
['b', 'u', 'a', 'r̃', 'a']
    """
    assert list(iter_graphemes(i)) == o.split()


@pytest.mark.parametrize(
    's,r',
    [
        ("[1] 'gloss'", lambda g: g['fn'] == '1'),
        ("'gloss' [7]", lambda g: g['fn'] == '7'),
        ("(V) 'gloss'", lambda g: g['pos'] == 'V'),
    ]
)
def test_iter_glosses(s, r):
    g = next(iter_glosses(s))
    assert r(g)


def test_iter_glosses_multiple():
    assert len(list(iter_glosses("'a'; 'b'; 'c' ('x'; y)"))) == 3


@pytest.mark.parametrize(
    'i,o',
    [
        ("bubuŋ (Dempwolff 1938) 'ridgepole'", (["bubuŋ"], "(Dempwolff 1938) 'ridgepole'")),
        ("bubuŋ, *second 'ridgepole'", (["bubuŋ", "second"], "'ridgepole'")),
        ("bu(b,g)uŋ 'ridgepole'", (["bu(b,g)uŋ"], "'ridgepole'")),
        ("bu[b,g]uŋ 'ridgepole'", (["bu[b,g]uŋ"], "'ridgepole'")),
        ("bu<b>uŋ 'ridgepole'", (["bu<b>uŋ"], "'ridgepole'")),
        ("|bubuŋ  second| 'ridgepole'", (["bubuŋ second"], "'ridgepole'")),
        #("pa, (ADV) *qa-pa ‘t’", (["pa", "qa-pa"], "‘t’")),  FIXME: requires parser reading POS spec again!
    ]
)
def test_parse_protoform(i, o):
    assert parse_protoform(i, 'PMP') == o


def test_iter_etyma():
    lines = """
1 H1
1.1 H2
1.1.1 H3

\x0c                                        Architecturalforms and settlement patterns              49

<
PMP (N) *balay 'open-sided building'
POc *pale 'open-sided building'
 Adm: Mussau             ale               'house'
 cf. also: loans
 NNG: Bebeli             bele              'house'
>

"""
    h1, h2, h3, pageno, et = list(extract_etyma(lines.split('\n')))[0]
    assert pageno == 49
    assert h1 == ('1', 'H1')
    assert h2 == ('1', 'H2')
    assert h3 == ('1', 'H3')
    forms = et
    forms, cfs = forms
    assert len(forms) == 3
    assert cfs and cfs[0][0] == 'loans' and len(cfs[0][1]) == 1

    gen = extract_etyma(lines.split('\n'))
    et = next(gen)[-1][0][0]
    while True:
        try:  # Send the proto-language of the first reconstruction into the generator.
            et = gen.send('xyz')
        except StopIteration as e:
            text = e.value
            break
    assert 'xyz' in text[4:]
