from instances.models import Instance

class InstanceMiddleware:
    """This middleware sets request.instance to the default Instance for all
    requests. This can be changed/overridden if you use SayIt in a way that
    uses multiple instances."""
    def process_request(self, request):
        request.instance = Instance.objects.get(label='default')
        request.is_user_instance = (
            request.user.is_authenticated() and
            ( request.instance in request.user.instances.all() or request.user.is_superuser )
        )
