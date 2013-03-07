"""Thanks to http://stackoverflow.com/a/12977709/669631, though I had to use
   __dict__ rather than _meta.fields for it to work in the admin."""

from django.db.models import signals
from django.utils.functional import curry

class WhoDidMiddleware(object):
    def process_request(self, request):
        if not request.method in ('GET', 'HEAD', 'OPTIONS', 'TRACE'):
            if hasattr(request, 'user') and request.user.is_authenticated():
                user = request.user
            else:
                user = None

            mark_whodid = curry(self.mark_whodid, user)
            signals.pre_save.connect(mark_whodid, dispatch_uid = (self.__class__, request,), weak = False)

    def process_response(self, request, response):
        signals.pre_save.disconnect(dispatch_uid = (self.__class__, request,))
        return response

    def mark_whodid(self, user, sender, instance, **kwargs):
        if 'created_by_id' in instance.__dict__ and not instance.created_by:
            instance.created_by = user

