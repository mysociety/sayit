import sys

from django.http import HttpResponse
from django.shortcuts import render
from django.conf import settings

from instances.models import Instance
from login_token.models import LoginToken

def login_tokens_for_user(request):
    logged_in = request.user.is_authenticated()
    instances_and_tokens = []
    if logged_in:
        instances = []
        if request.instance:
            instances.append(request.instance)
        else:
            instances = list(Instance.objects.all().order_by('label'))

        # FIXME: get login tokens from the LoginToken table
        instances_and_tokens = [(i, " ".join(LoginToken.generate_token()))
                                for i in instances]

    return render(request,
                  'login_token/tokens.html',
                  {'logged_in': logged_in,
                   'particular_instance': bool(request.instance),
                   'instances_and_tokens': instances_and_tokens,
                   'BASE_HOST': settings.BASE_HOST})
