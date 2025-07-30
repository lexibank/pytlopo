import pytest

from pytlopo.parser.lines import *


@pytest.mark.parametrize(
    'i,o',
    [
        (['First  ', '  Second'], lambda s: s == 'First Second'),
        (['Figure 1: Cap'], lambda s: 'fig-1-1' in s and 'Cap]' in s),
    ]
)
def test_make_paragraph(i, o, tmp_path):
    tmp_path.joinpath('vol1', 'maps').mkdir(parents=True)
    tmp_path.joinpath('vol1', 'maps', 'fig_1.png').write_text('t')
    assert o(make_paragraph(i, tmp_path / 'vol1'))


def test_iter_chapters(tmp_path):
    iterator = iter_chapters("""\
1 Chapter

1.1 Section

1.1.1 Subsection
""".split('\n'), tmp_path)
    inchapter, text, toc = next(iterator)
    assert inchapter
    assert '## 1. Section' in text
    assert '### 1.1. Subsection' in text
