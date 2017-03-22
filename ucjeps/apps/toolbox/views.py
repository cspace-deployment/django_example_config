__author__ = 'jblowe'

import operator

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, HttpResponse, redirect
from django import forms
from bson import json_util
import json

from utils import loginfo, handleJSONrequest, setconstants, APPS


def direct(request):
    return redirect('toolbox/')


# @login_required()
def toolbox(request):
    # APPS is a dict of configured webapps, show the list sorted by "app title"
    sorted_apps = sorted(APPS.items(), key=operator.itemgetter(1))
    context = setconstants({'apps': sorted_apps}, 'listapps')
    return render(request, 'toolbox.html', context)


# @login_required()
def tool(request, appname):
    if appname == 'json':
        return jsonrequest(request)
    # if we are here, we have been given a particular appname, e.g. "keyinfo", as part of the url
    context = setconstants({}, appname)
    if request.method == 'GET':
        form = forms.Form(request.GET)
    else:
        form = forms.Form()

    if form.is_valid():
        # context = dispatch(context, request.GET, appname)
        loginfo(appname, context, request)
        return render(request, 'toolbox.html', context)


def jsonrequest(request):
    if request.method == 'GET':
        form = forms.Form(request.GET)
        requestObject = request.GET

    if request.method == 'POST':
        form = forms.Form(request.POST)
        requestObject = request.POST

    if form.is_valid():
        context = setconstants({}, 'json')
        del context['additionalInfo']
        del context['extra_nav']
        del context['searchrows']
        del context['searchcolumns']
        context = handleJSONrequest(context, requestObject)

        loginfo(context['appname'], context, request)
        #if check_json(context):
        # context['items'] = []
        return HttpResponse(json.dumps(context, default=json_util.default))
        #else:
        #    return HttpResponse(json.dumps(dump_errors(context))
    else:
        return HttpResponse(json.dumps({'error': 'form is not valid'}))
