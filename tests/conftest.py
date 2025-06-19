import pathlib

import pytest

from csvw.dsv import reader
from pycldf.sources import Source, Sources


@pytest.fixture(scope='session')
def repos():
    return pathlib.Path(__file__).parent / 'repos'


@pytest.fixture(scope='session')
def volume1(repos):
    from pytlopo.models import Volume

    return Volume(
        repos / 'raw' / 'vol1',
        {r['Name']: r for r in reader(repos / 'etc' / 'languages.csv', dicts=True)},
        Source.from_bibtex('@book{vol1,\nauthor={A B},\ntitle={T}\n}'),
        Sources.from_file(repos / 'etc' / 'sources.bib'),
    )
