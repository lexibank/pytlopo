import re

# Graphemes used in reconstructions of POc:
POC_GRAPHEMES = "w p b m i e t d s n r dr l a ā c j y u o k g q R ŋ ñ pʷ bʷ mʷ".split()
TRANSCRIPTION = [
    'N', 'ɸ', 'h', 'pʰ', 'kʰ', 'nʰ', 'mʰ', 'tʰ', 'bˠ', 'ᵑk', 'h́', 'ᵐb', 'ᵑr',
    'á', 'ˀa',
    'à',
    'ā',
    'ã',
    'æ',
    'ǣ',
    'ɒ',
    'ɒ̄',
    'f',
    'z',
    'ʔ',
    'ð',
    'g', 'gʷ', 'ᵑg', 'qʷ', 'tʷ', 'lʷ', 'ḷʷ', 'vʷ', 'ᵑgʷ',
    '(', ')', '[', ']', '<', '>', '-',
    'ɣ',
    'ɔ̀',
    'ɔ',
    'ɔ̄',
    'v',
    'ø',
    'ö',
    'ō',
    'ò',
    'ó',
    'î',  # i circumflex
    'ĩ',  # i tilde
    'ì',  # i grave
    'ī',  # i macron
    'ɨ',
    'í',
    'I',
    'ɨ̈',
    'ı',
    'ʈ',
    't',
    'x',
    'θ',
    'b',
    'ŋ', 'ŋʷ',
    'ɳ',
    'è',
    'ɛ', 'ɛ́', 'ɛ̃', "ɛ̄", 'ɛ̃́', 'ɛ̀',
    'ə̄',
    'é',
    'ē',
    'ê',
    'ə',
    'ū',
    'ü',
    'ù',
    'ú',
    'ʉ',
    'ñ',
    'm̀',
    'ṣ',
    'ẓ',
    'ḍ',
    'ʃ',
    'č',
    'c̣',
    'ɬ',
    'ʌ',
    'ḷ',
    'ȴ',
    'l̥',
    'ʋ',
    'v̈',
    'ɯ',
    'β',  # LATIN SMALL LETTER TURNED M - used as superscript!
    'ṛ',
    'r̃',
    'ɾ',
    'ɽ',
]

GROUPS = [
    # Oceanic:
    "Adm",  # Admiralty
    "Fij",  # Fijian
    "Mic",  # Micronesian
    "MM",  # Meso-Melanesian
    "NCal",  # New Caledonia
    "NCV",  # North and Central Vanuatu
    "NNG",  # North New Guinea
    "Pn",  # Polynesian
    "PT",  # Papuan Tip
    "SES",  # Southeast Solomons
    "SJ",  # Sarmi/Jayapura
    "SV",  # South Vanuatu
    "Yap",  # Yapese
    # Other Austronesian:
    "CMP",  # Central Malayo-Polynesian
    "Fma",  # Formosan
    "IJ",  # Irin Jaya
    "WMP",  # Western Malayo-Polynesian
    "SHWNG",
]
# Map proto-language ID to extra-graphemes in addition to POC_GRAPHEMES.
PROTO = {
    # Oceanic:
    "POc": [],  # Yap
    "PEAd": [], # Adm
    "Proto Eastern Admiralty": [],  # FIXME: identify with PEAd
    "PWOc": [],  # MM, SJ
    "Proto Northwest Solomonic": [],
    "Proto Meso-Melanesian": [],  # MM
    "PNGOc": ['kʷ'],  # Proto New Guinea Oceanic, i.e. PWOc without reflexes from MM
    "PNNG": [], # NNG
    "PPT": [], # PT
    "PEOc": ['C'],  # NCal
    "Proto Southeast Solomonic": [],  # FIXME: identify with PSS
    "PSS": [], # SES
    "PMic": ['ō', 'f', 'ū', 'z', 'V', 'ī', 'ə̄', 'ə'],  # Proto Micronesian Mic
    "PChk": ['ō', 'f', 'ū', 'z', 'V', 'ī', 'ə̄', 'ə'],
    "PNCV": ['v'],  # NCV
    "Proto Remote Oceanic": [], # NCV, SV, Mic
    "PCP": ['v', 'ā'],  # Proto Central Pacific, Fij
    "PPn": ['ʔ', 'h', 'ō', 'f', 'ū', 'z', 'V', 'ī', 'ə̄', 'ə'],  # PN
    "PCEPn": ['ō', 'f', 'ū', 'z', 'V', 'ī', 'ə̄', 'ə'],  # Proto Central Eastern Polynesian; Hawaiian, Maori, Tuamotuan
    "PNPn": ['ʔ', 'ā', 'h'],
    # Other Austronesian:
    "PAn": ['á', 'C', 'D', 'h', 'N', 'S', 'R', 'T', 'z', 'Z', 'L', '?', 'ə', '+'],
    "PMP": ['á', 'C', 'D', 'h', 'N', 'S', 'R', 'T', 'z', 'Z', 'L', '?', 'ə', '+', 'W'],
    "PWMP": ['S'],
    "PCEMP": [],
    "PCMP": [],
    "PEMP": [],
    "Proto South Halmahera/West New Guinea": [],
}

# FIXME: Map POS patterns to lists of mormalized POS symbols.
POS = [
    'ADJ',
    'ADV',
    'adverb',
    'ADV, ADJ',
    'ADN AFFIX',
    'DEM',
    'DIR',
    'DIR clause-final',
    'INTERJECTION',
    'LOC',
    'N',
    'N LOC',
    'N, N LOC',
    'N, ? N LOC',
    'N, V',
    'N, v',
    'N,V',
    'N LOC',
    'N + POSTPOSITION',
    'V',
    'V AUX',
    'V, DIR',
    'VF',
    'v',
    'VT',
    'VI',
    'vI',
    'VT,VI',
    'VT, VI',
    'V & N',
    'V, ADJ',
    '?? N LOC, V',
    'PP',
    'POSTVERBAL ADV',
    'PREPV',
    'preverbal clitic',
    'PASS',
    'postposed particle',
    'PREP',
    'POSTPOSITION',
    'R-',
    'R',
    'RELATIONAL N',
]


def re_choice(items):
    return r'|'.join(re.escape(i) for i in items)


proto_pattern = re.compile(r'(\((?P<relno>[0-9])\)\s*)?'
                           r'(?P<pl>({}))\s+'
                           r'(?P<root>root\s+)?'
                           r'(?P<pldoubt>\((POC)?\?\)\s*)?'
                           r'(?P<pos>\(({})\)\s*)?'
                           r'(?P<fn>\[[0-9]+]\s+)?'
                           r'(?P<pfdoubt>\?)?\*'.format(re_choice(PROTO), re_choice(POS)))
witness_pattern = re.compile(r'\s+({})(\s*:\s+)'.format(re_choice(GROUPS)))
