from uploadmedia.cswaExtras import postxml, relationsPayload, getConfig, getCSID


TITLE = 'Taxon Editor'
numberWanted = 10

taxon_authority_csid = '87036424-e55f-4e39-bd12'
tropicos_api_key = 'd0a905a9-75c9-466e-bbab-5b568f4e8b91'
termTypeDropdowns = [('descriptor', 'descriptor'), ('Leave empty', '')]
termStatusDropdowns = [('accepted', 'accepted'), ('Leave empty', '')]
taxonRankDropdowns = [('species', 'species'), ('genus', 'genus')]
taxonfields = [
    ('select', '', 'ignore'),
    ('n', 'N', 'ignore'),
    ('family', 'Family', 'refName'),
    ('taxonMajorGroup', 'Major Group', 'string'),
    ('termDisplayName', 'Scientific Name with Authors', 'string'),
    ('termName', 'Scientific Name', 'string'),
    ('commonName', 'Common Name', 'refName'),
    ('termSource', 'Source', 'string'),
    ('termSourceID', 'Source ID', 'string'),
    # these are constants or derived (i.e. not from service)
    ('termFormattedDisplayName', 'Formatted Scientific Name', 'string'),
    ('taxonomicStatus', 'Taxonomic Status', 'string'),
    ('termPrefForLang', 'Term Language', 'string'),
    ('termType', 'Term Type', 'dropdown', termTypeDropdowns),
    ('termStatus', 'Term Status', 'dropdown', termStatusDropdowns),
    ('taxonCurrency', 'Taxon Currency', 'string'),
    ('inAuthority', 'Authority CSID', 'ignore'),
    ('taxonRank', 'Rank', 'dropdown', taxonRankDropdowns),
]

# labels = 'n,family,major group,scientific name with authors,scientific name,idsource,id'.split(',')
labels = [n[1] for n in taxonfields]
labels = labels[:9]

formfields = [{'name': f[0], 'label': f[1], 'fieldtype': f[2], 'value': '', 'type': 'text'} for f in taxonfields]


def lookupMajorGroup(phylum):
    """
    Dictionary function translating GBIF phylum values to UCJEPS major group
    Input the phylum; get back the major group
    """
    MajorGroups = {
        'Magnoliophyta': 'Spermatophytes',
        'Streptophyta': 'Spermatophytes',
        'Pteridophyta': 'Pteridophytes',
        'Bryophyta': 'Bryophytes',
        'Chlorophyta': 'Algae',
        'Bacillariophyta': 'Algae',
        'Rhodophyta': 'Algae',
        'Pinophyta': 'Spermatophytes',
        'Lycopodiophyta': 'Pteridophytes',
        'Marchantiophyta': 'Bryophytes',
        'Cycadophyta': 'Spermatophytes',
        'Prasinophyta': 'Algae',
        'Equisetophyta': 'Pteridophytes',
        'Gnetophyta': 'Spermatophytes',
        'Ginkgophyta': 'Spermatophytes',
        'Anthocerotophyta': 'Bryophytes',
        'Psilophyta': 'Pteridophytes',
        'Cyanidiophyta': 'Algae',
        'Glaucophyta': 'Algae',
        'phylum': 'not found',
    }
    return MajorGroups[phylum]


def xName(name, fieldname, idx):
    csname = taxonfields[idx + 1][0]
    if fieldname in name:
        if name[fieldname] is not None:
            return [csname, name[fieldname]]
        else:
            return [csname, '']
    else:
        return [csname, 'not found']


def extractTag(xml, tag):
    element = xml.find('.//%s' % tag)
    try:
        if "urn:" in element.text:
            element_text = deURN(str(element.text))
        else:
            element_text = element.text
    except:
        element_text = ''
    return element_text

