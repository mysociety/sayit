import json
import sys

from django.conf import settings
from django.contrib.auth import authenticate
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from instances.models import Instance
from login_token.models import LoginToken, generate_token

from datetime import timedelta

def login_tokens_for_user(request):
    logged_in = request.user.is_authenticated()
    instances_and_tokens = []
    if logged_in:
        instances = []
        if request.instance:
            instances.append(request.instance)
        else:
            instances = list(Instance.objects.all().order_by('label'))

        instances_and_tokens = [(lt.instance, lt.token)
                                for lt in LoginToken.objects.filter(instance__in=instances)]

    return render(request,
                  'login_token/tokens.html',
                  {'logged_in': logged_in,
                   'particular_instance': bool(request.instance),
                   'instances_and_tokens': instances_and_tokens,
                   'BASE_HOST': settings.BASE_HOST})

@csrf_exempt
def check_login_token(request):
    '''Checks that a login token is valid and returns a session token, etc.'''

    key = 'login-token'

    if key not in request.POST:
        data = {'error': 'No login token supplied'}
        return HttpResponse(json.dumps(data),
                            content_type='text/json',
                            status=401)
    token = request.POST[key]

    def instance_dict(i):
        return {'label': i.label,
                'title': i.title}

    user = authenticate(token=token)
    if user is None:
        return HttpResponse(json.dumps({'error': 'Unknown login token'}),
                            content_type='text/json',
                            status=401)

    lt = LoginToken.objects.get(token=token, user=user)
    other_instances = [i for i in lt.user.instances.all()
                       if i != lt.instance]

    request.session['instance'] = lt.instance

    data = {'result': {'user': lt.user.username,
                       'session-token': request.session.session_key,
                       'instance': instance_dict(lt.instance),
                       'other-instances': [instance_dict(i) for i in other_instances]}}
    return HttpResponse(json.dumps(data),
                        content_type='text/json')
