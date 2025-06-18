import re


fn_pattern = re.compile(r'\[(?P<fn>[0-9]+)]')  # [2]

# Graphemes used in reconstructions of POc:
POC_GRAPHEMES = "a e i o u ā w p b m t d s n r dr l c j y k g q R ŋ ñ pʷ bʷ mʷ kʷ".split()
# Unexpected: ā and kʷ
# See https://en.wikipedia.org/wiki/Proto-Oceanic_language for a mapping to BIPA
# dr: ⁿr   pre-nasalized voiced alveolar trill consonant
# R: ʀ   voiced uvular trill consonant
POC_BIPA_GRAPHEMES = {
    "dr": "ⁿr",
    "R": "ʀ",
    "ñ": "ɲ",
}
TRANSCRIPTION = [
    '=',  # enclitic boundary
    'ᵐp', 'ʷa', 'ñʰ', 'jᵐ', 'N', 'ɸ', 'ɸʷ', 'h', 'vʰ', 'pʰ', 'kʰ', 'nʰ', 'mʰ', 'tʰ', 'bˠ', 'ᵑk', 'h́',
    'ᵐb', 'ᵑr', 'lᵐ', 'lʰ',
    'á', 'ˀa', 'yʰ', 'wʷ', 'kʰ', 'oᵑ',
    'à', 'a̰', 'ä',
    'ā',  # macron
    'ã',  # tilde
    'â',  # circumflex
    'æ', 'ʙ', 'œ','œ̄',
    'oᵐ', 'ᴂ', 'ø̄',
    'ǣ', 'aᵐ',
    'ɒ', 'eᵐ',
    'ɒ̄',
    'ūᵑ', 'fʰ', 'f',
    'z', 'ẓ',
    'tᫀ', 'dᫀ', 'nᫀ',
    'ʔ',
    'ð', 'ð̫', 'ðᫀ', 'dᫀ',
    'ɢ', 'g', 'gʷ', 'ᵑg', 'qʷ', 'tʷ', 'lʷ', 'ḷʷ', 'vʷ', 'ᵑgʷ', 'kʷ', 'nʷ', 'fʷ',
    '(', ')', '[', ']', '<', '>', '-', '~',
    'ɣ',
    'ɔ̀', 'χ', # chi
    'ɔ', 'ʊ',
    'ɔ̄',
    'v', 'v̈',
    'ɵ̄', 'ọ', 'öᵐ', 'ø',
    'ö', 'ō', 'õ',
    'ò', 'ó', 'ô',
    'î',  # circumflex
    'ĩ',  # tilde
    'ì',  # grave
    'ī',  # macron
    'ɨ', 'ⁿ', 'ɨ̈', # stroke and diaresis
    'í',
    'I',
    'ɨ̈', 'ĩ̄', 'ɨ̄',
    'ị', 'ı', 'ıː', 'ɪ',
    'ʈ', '̄t',
    't', 'ṭ', '†', 'tᫀ',
    'x',
    'θ', 'ø', 'φ',
    'b',
    'ŋ', 'ŋʷ',
    'ñ',  # tilde
    'ɲ', 'ɳ', 'nᫀ',
    'è', 'ẽ', # tilde
    'ɛ', 'ɛ́', 'ɛ̄', 'ɛ̃', "ɛ̄", 'ɛ̃́', 'ɛ̀',
    'ə', 'ə̄',
    'é',
    'ē', # macron
    'ê', 'ë',
    'ū', 'ũ', 'ǖ', 'ú̄',
    'ü', 'û',
    'ù',
    'ú',
    'ʉ̄', 'ʉ',
    'm̫', 'm̥', 'm̀',
    'ṣ', 'š', 'ʃ', 'ʒ',
    'ẓ',
    'ḍ', 'ɖ',
    'ʃ',
    'č',
    'c̣', 'cʰ', 'ç',
    'ɬ',
    'ʌ', 'ʌ̃', 'ʟ', 'ʌ̃',
    'ḷ', 'ʎ',
    'ȴ', 'bʸ',
    'l̥',  # ring below
    'ʋ',
    'v̈', 'vʸ', 'vᫀ', 'rʰ', 'kʸ', 'ɣʷ',
    'ɯ', 'ᶭ', 'lᶭ', 'mʸ', 'mᶭ', 'nᶭ', 'pᶭ', 'ᶭp',
    'β',  # LATIN SMALL LETTER TURNED M - used as superscript!
    'ṛ', 'ṛᶭ', 'ʁ', 'rᶭ',
    'r̃', 'ɹ', 'ɾ̄',
    'ɾ',  # r with fishhook
    'ɽ', 'z̧', # z with cedilla
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
    "TM",  # Temotu
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
    "Early Oceanic": [],
    "POc": [],  # Yap
    "PEAd": [], # Adm
    "PAdm": [], # same thing as above?
    "Proto Central Papuan": [],
    "Proto Eastern Admiralty": [],  # FIXME: identify with PEAd
    "PWOc": ['pᵂ'],  # MM, SJ
    "Proto Northwest Solomonic": [],
    "Proto North Bougainville": [],
    "Proto Meso-Melanesian": [],  # MM
    "PNGOc": ['kʷ'],  # Proto New Guinea Oceanic, i.e. PWOc without reflexes from MM
    "PNNG": [], # NNG
    "PPT": [], # PT
    "PEOc": ['ŋʷ', 'C'],  # NCal
    "PNCal": ['hʷ', 'kʰ'],
    "Proto Southeast Solomonic": [],  # FIXME: identify with PSS
    "PSS": ['ɣ'], # SES
    "PMic": ['x', 'ō', 'f', 'ū', 'z', 'V', 'ī', 'ə̄', 'ə'],  # Proto Micronesian Mic
    "Proto Western Micronesian": [],
    "Proto Central Micronesian": [],
    "Proto Chuukic-Ponapeic": [],
    "PChk": ['ɨ', 'ō', 'f', 'ū', 'z', 'V', 'ī', 'ə̄', 'ə'],
    "PNCV": ['v', 'vʷ'],  # NCV
    "Proto Central Vanuatu": [],
    "PSV": ['ɣ'],
    "PSOc": [],  # Proto Southern Oceanic
    "Proto Remote Oceanic": [], # NCV, SV, Mic
    "PCP": ['x', 'ð', 'ĩ', 'ē', 'v', 'ā', 'gʷ'],  # Proto Central Pacific, Fij
    "PPn": ['ʔ', 'h', 'ō', 'f', 'ū', 'z', 'V', 'ī', 'ə̄', 'ə'],  # PN
    "Proto Eastern Polynesian": [],
    "Proto Eastern Polynesian-Northern Outlier": [],
    "PCEPn": ['ō', 'f', 'ū', 'z', 'V', 'ī', 'ə̄', 'ə'],  # Proto Central Eastern Polynesian; Hawaiian, Maori, Tuamotuan
    "PNPn": ['ʔ', 'ā', 'h'],
    # Other Austronesian:
    "PAn": ['á', 'C', 'D', 'h', 'N', 'S', 'R', 'T', 'z', 'Z', 'L', '?', 'ə', '+'],
    "PAn/PMP": [],
    "PMP": ['á', 'C', 'D', 'h', 'N', 'S', 'R', 'T', 'z', 'Z', 'L', '?', 'ə', '+', 'W'],
    "PWMP": ['S'],
    "PCEMP": [],
    "PCMP": [],
    "PEMP": [],
    "PFij": [],
    "Proto South Halmahera/West New Guinea": [],
    "Proto Malaita-Makira": [],
    # Proto Erakor-Tafea is the immediate putative ancestor of S Efate and Proto Southern Vanuatu.
    "Proto Erakor-Tafea": [],
    # Proto South Melanesian is the putative ancestor of the Southern Vanuatu and New Caledonian languages
    "Proto South Melanesian": [],
    "Proto Tahitic": [],
    "Proto Markham": [],
    "Proto Tanna": [],
    "Proto Torres-Banks": [],
    "Proto Huon Gulf": [],
    "Proto Hote-Buang": [],
    "Proto Mengen": [],
    "Proto S Efate/SV": [],
    "Proto Willaumez": [],
    "Proto New Caledonia": [],
    "Proto Central/Eastern Polynesian": [],
}

# FIXME: Map POS patterns to lists of mormalized POS symbols.
POS = [
    'ADJ',
    'ADJ, VI',
    'ADV',
    'ADVERB OF INTENSITY',
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
    'N. V',
    'N, v',
    'N,V',
    'N,VI',
    'N, VI',
    'VI, N',
    'VI, U-verb',
    'VI, inanimate subject',
    'VT, inanimate object',
    'N LOC',
    'N, N Loc',
    'N + POSTPOSITION',
    'PLURAL SUBJECT',
    'V',
    'VSt',
    'N,VSt',
    'VSt, N',
    'VT, VSt',
    'V AUX',
    'V, DIR',
    'V PERFECTIVE',
    'V PASSIVE',
    'VF',
    'v',
    'VT', 'vT',
    'VI',
    'vI', 'vi',
    'VT,VI',
    'VI,VT',
    'VTI',
    'VI, VT',
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
    'PRO',
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
                           r'(?P<pfdoubt>\?)?†?\*'.format(re_choice(PROTO), re_choice(POS)))  # FIXME: record dagger!
witness_pattern = re.compile(r'\s+({})(\s*:\s+)'.format(re_choice(GROUPS)))
