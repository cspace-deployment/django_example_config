from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.template import RequestContext, loader
from recordstats import RecordStats

@login_required()
def index(request):
   stats = RecordStats()
   doccount = stats.getDocCount()
   docytd = stats.getDocYTD()
   personcount = stats.getNameCount()
   personytd = stats.getNameYTD()
   orgcount = stats.getOrgCount()
   orgytd = stats.getOrgYTD()
   committeecount = stats.getCommitteeCount()
   committeeytd = stats.getCommitteeYTD()
   pagecount = stats.getPageCount()
   pageytd = stats.getPageYTD()
   filmcount = stats.getFilmCount()
   filmytd = stats.getFilmYTD()
   subjcount = stats.getSubjectCount()
   subjytd = stats.getSubjectYTD()
   allnames = personcount+orgcount+committeecount

   accesscounts = stats.getAccessCounts()

   template = loader.get_template('cinestats/stats.html')

   context = RequestContext(request, {
      'allnames_count': allnames,
      'allnames_ytd': personytd+orgytd+committeeytd,
      'person_count': personcount,
      'person_ytd': personytd,
      'org_count': orgcount,
      'org_ytd': orgytd,
      'committee_count': committeecount,
      'committee_ytd':committeeytd,
      'film_count': filmcount,
      'film_ytd': filmytd,
      'doc_count': doccount,
      'doc_ytd': docytd,
      'page_count': pagecount,
      'page_ytd': pageytd,
      'subject_count': subjcount,
      'subject_ytd': subjytd,
       'accesscounts': accesscounts
   })
   return HttpResponse(template.render(context))
 
