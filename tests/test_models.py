import pytest

from pytlopo.models import *


def test_FormGroup(volume1):
    fg = FormGroup.from_data(
        volume1,
        ('2', 'Chapter'),
        ('3', 'Section'),
        ('4', 'Subsection'),
        '123',
        [" Adm: Language  form 'gloss'"]
    )
    assert len(fg.forms) == 1
    assert fg.forms[0].lang == 'Language'
    assert fg.id == '1-2-3-4-123-adm-language-form'
    assert 'cf.csv#cldf:' in fg.cldf_markdown_link()
