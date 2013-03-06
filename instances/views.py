from functools import wraps
from django.contrib.auth.decorators import user_passes_test
from django.utils.decorators import method_decorator
from django.utils.decorators import available_attrs

def user_in_instance(view_func):
    """
    user_passes_test only passes request.user to the test function, but we need
    request itself in order to look at the instance. So wrap the wrapper, just
    so we don't need to duplicate e.g. the redirect-to-login code.
    """
    orig_wrapped_func = user_passes_test(lambda u: u.is_superuser)(view_func)
    @wraps(orig_wrapped_func, assigned=available_attrs(orig_wrapped_func))
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated() and request.instance in request.user.instances.all():
            return view_func(request, *args, **kwargs)
        return orig_wrapped_func(request, *args, **kwargs)
    return _wrapped_view

class InstanceViewMixin(object):
    def get_queryset(self):
        return self.model.objects.for_instance(self.request.instance)

class InstanceFormMixin(InstanceViewMixin):
    @method_decorator(user_in_instance)
    def dispatch(self, *args, **kwargs):
        return super(InstanceFormMixin, self).dispatch(*args, **kwargs)

    def form_valid(self, form):
        # If not present, fill in the instance from the request
        if not hasattr(form.instance, 'instance'):
            form.instance.instance = self.request.instance
        return super(InstanceFormMixin, self).form_valid(form)

