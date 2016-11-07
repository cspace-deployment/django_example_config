taxon_template = """
<document name="taxon">
    <ns2:taxon_common xmlns:ns2="http://collectionspace.org/services/taxonomy" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <taxonTermGroupList>
      <taxonTermGroup>
        <termName>{termName}</termName>
        <termSource/>
        <termSourceID></termSourceID>
        <taxonomicStatus>accepted</taxonomicStatus>
        <termSourceNote/>
        <termLanguage/>
        <termPrefForLang>true</termPrefForLang>
        <termDisplayName>{termName}</termDisplayName>
        <termType>descriptor</termType>
        <termStatus>accepted</termStatus>
        <termFormattedDisplayName></termFormattedDisplayName>
        <termQualifier/>
        <termSourceDetail/>
      </taxonTermGroup>
    </taxonTermGroupList>
    <taxonYear/>
    <taxonCurrency>current</taxonCurrency>
    <taxonCitationList>
      <taxonCitation/>
    </taxonCitationList>
    <shortIdentifier></shortIdentifier>
    <commonNameGroupList/>
    <inAuthority>87036424-e55f-4e39-bd12</inAuthority>
    <taxonIsNamedHybrid>false</taxonIsNamedHybrid>
    <taxonAuthorGroupList>
      <taxonAuthorGroup>
        <taxonAuthor/>
        <taxonAuthorType/>
      </taxonAuthorGroup>
    </taxonAuthorGroupList>
    <taxonRank>species</taxonRank>
  </ns2:taxon_common>
  <ns2:taxon_naturalhistory xmlns:ns2="http://collectionspace.org/services/taxon/domain/naturalhistory" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <plantAttributesGroupList/>
    <naturalHistoryCommonNameGroupList/>
    <family>{family}</family>
    <relatedTermGroupList/>
  </ns2:taxon_naturalhistory>
  <ns2:taxon_ucjeps xmlns:ns2="http://collectionspace.org/services/taxon/local/ucjeps" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <taxonMajorGroup>{taxonMajorGroup}</taxonMajorGroup>
  </ns2:taxon_ucjeps>
</document>
"""
