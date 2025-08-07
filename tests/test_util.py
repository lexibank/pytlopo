import pytest

from pytlopo.util import variants, strip_morphemeseparator


@pytest.mark.parametrize(
    'form,res',
    [
        ('', ''),
        ('-', '-'),
        ('--', '--'),
        ('-a', '-a'),
        ('b-', 'b-'),
        ('-b-', '-b-'),
        ('a-b', 'ab'),
    ]
)
def test_strip_morphemeseparator(form, res):
    assert strip_morphemeseparator(form) == res


@pytest.mark.parametrize(
    'form,var',
    [
        ('', []),
        ('a', ['a']),
        ('(x)', ['', 'x']),
        ('a(x)', ['a', 'ax']),
        ('a(x,y)', ['ax', 'ay']),
        ('a((x,y))', ['a', 'ax', 'ay']),
        ('a[x,y]', ['ax', 'ay']),
        ('a(x)b(y)', ['ab', 'axb', 'aby', 'axby']),
        (
            '((r,l)(a,u))mo(g,k)o',
            ['ramogo', 'ramoko', 'rumogo', 'rumoko', 'lamogo', 'lamoko', 'lumogo', 'lumoko']),
    ]
)
def test_variants(form, var):
    assert set(variants(form)) == set(var)
