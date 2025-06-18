"""
>>> r = species.name_lookup(q='Dorcopsis')
>>> for res in r['results']:
...     print(res['key'], res.get('nubKey'))  # This is used as ID for link https://www.gbif.org/species/2440137 the
...     break
...
261643299 2440137

                vernacular_names = pygbif.species.name_usage(key=nub, data="vernacularNames")
                english_names = [name["vernacularName"] for name in vernacular_names["results"] if name["language"] == "eng" and name.get("preferred")]
                if not english_names:
                    english_names = [name["vernacularName"] for name in vernacular_names["results"]
                                     if name["language"] == "eng"]
                #if english_names:
                print(','.join([row['Scientific_Name'], fmt(row['Name']), str(nub), fmt(english_names[0] if english_names else '')]))



Get the first image with suitable license:

>>> res = occ.search(taxonKey=2470752, basisOfRecord='HUMAN_OBSERVATION', mediatype='STILL_IMAGE', limit=1)

>>> res['results'][0]['extensions']['http://rs.gbif.org/terms/1.0/Multimedia']
[{
    'http://purl.org/dc/terms/references': 'https://www.inaturalist.org/photos/463681711',
    'http://purl.org/dc/terms/created': '2025-01-06T01:46:24Z',
    'http://rs.tdwg.org/dwc/terms/catalogNumber': '463681711',
    'http://purl.org/dc/terms/identifier': 'https://inaturalist-open-data.s3.amazonaws.com/photos/463681711/original.jpg',
    'http://purl.org/dc/terms/format': 'image/jpeg',
    'http://purl.org/dc/terms/rightsHolder': 'susanpteranodon',
    'http://purl.org/dc/terms/creator': 'susanpteranodon',
    'http://purl.org/dc/terms/license': 'http://creativecommons.org/licenses/by-nc/4.0/',
    'http://purl.org/dc/terms/type': 'StillImage',
    'http://purl.org/dc/terms/publisher': 'iNaturalist'}]


"""