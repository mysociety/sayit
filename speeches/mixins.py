from django.views.generic.detail import SingleObjectMixin
from django.http import HttpResponseRedirect, Http404

from speeches.utils.base32 import MistypedIDException, base32_to_int


class UnmatchingSlugException(Exception):
    pass


class Base32SingleObjectMixin(SingleObjectMixin):
    """Assumes pk is in base32, and decodes that before passing on to the
    parent to be resolved."""

    def get(self, request, *args, **kwargs):
        try:
            return super(Base32SingleObjectMixin, self).get(request, *args, **kwargs)
        except UnmatchingSlugException as e:
            return HttpResponseRedirect(e.args[0].get_absolute_url())

    def get_context_data(self, **kwargs):
        """Copy of 1.6's SingleObjectMixin, then we skip
        SingleObjectMixin's own class as it's broken in 1.4."""
        context = {}
        if self.object:
            context['object'] = self.object
            context_object_name = self.get_context_object_name(self.object)
            if context_object_name:
                context[context_object_name] = self.object
        context.update(kwargs)
        return super(SingleObjectMixin, self).get_context_data(**context)

    def get_object(self, queryset=None):
        pk = self.kwargs.get(self.pk_url_kwarg, None)
        mistyped = False
        if pk is not None:
            try:
                pk = base32_to_int(pk)
            except MistypedIDException as e:
                mistyped = True
                pk = e.args[0]
            except:
                raise Http404('Could not match id %s' % pk)
            self.kwargs[self.pk_url_kwarg] = pk
        obj = super(Base32SingleObjectMixin, self).get_object(queryset)
        if (self.kwargs['slug'] != obj.slug) or mistyped:
            raise UnmatchingSlugException(obj)
        return obj
