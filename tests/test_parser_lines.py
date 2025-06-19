import pytest

from pytlopo.parser.lines import *


@pytest.mark.parametrize(
    'i,o',
    [
        (['First  ', '  Second'], lambda s: s == 'First Second'),
        (['Figure 1: Cap'], lambda s: 'cldf:fig-1-1.png' in s and 'Cap]' in s),
    ]
)
def test_make_paragraph(i, o, tmp_path):
    tmp_path.joinpath('vol1', 'maps').mkdir(parents=True)
    tmp_path.joinpath('vol1', 'maps', 'fig_1.png').write_text('t')
    assert o(make_paragraph(i, tmp_path / 'vol1'))
