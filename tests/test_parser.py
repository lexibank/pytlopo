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
    'i,o',
    [
        ("bubuŋ (Dempwolff 1938) 'ridgepole'", (["bubuŋ"], "(Dempwolff 1938) 'ridgepole'")),
        ("bubuŋ, *second 'ridgepole'", (["bubuŋ", "second"], "'ridgepole'")),
        ("bu(b,g)uŋ 'ridgepole'", (["bu(b,g)uŋ"], "'ridgepole'")),
        ("bu[b,g]uŋ 'ridgepole'", (["bu[b,g]uŋ"], "'ridgepole'")),
        ("bu<b>uŋ 'ridgepole'", (["bu<b>uŋ"], "'ridgepole'")),
        ("|bubuŋ  second| 'ridgepole'", (["bubuŋ second"], "'ridgepole'")),
        ("pa, (ADV) *qa-pa ‘t’", (["pa", "qa-pa"], "‘t’")),
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

comment.
>

"""
    h1, h2, h3, pageno, et = list(extract_etyma(lines.split('\n')))[0]
    assert pageno == 49
    assert h1 == 'H1'
    assert h2 == 'H2'
    assert h3 == 'H3'
    forms, pre, post = et
    assert post[0] == 'comment.'
    forms, cfs = forms
    assert len(forms) == 3
    assert cfs and cfs[0][0] == 'loans' and len(cfs[0][1]) == 1

    gen = extract_etyma(lines.split('\n'))
    et = next(gen)[-1][0][0]
    while True:
        try:  # Send the proto-language of the first reconstruction into the generator.
            et = gen.send(et[0].split()[0])
        except StopIteration as e:
            text = e.value
            break
    assert '<--PMP-->' in text
