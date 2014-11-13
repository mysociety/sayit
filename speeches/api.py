# API Resources
# Uses Tastypie to do most of the hard work
# http://django-tastypie.readthedocs.org/en/v0.9.11/tutorial.html
from tastypie import fields
from tastypie.resources import NamespacedModelResource, ALL_WITH_RELATIONS, ALL
from tastypie.authentication import Authentication
from tastypie.authorization import ReadOnlyAuthorization

from haystack.query import SearchQuerySet

from speeches.models import Speech, Speaker, Section


class SectionResource(NamespacedModelResource):
    parent = fields.ForeignKey('self', 'parent', null=True)
    children = fields.ToManyField('self', 'children')

    def get_object_list(self, request):
        return super(SectionResource, self).get_object_list(request).filter(instance=request.instance)

    class Meta:
        queryset = Section.objects.all()
        resource_name = 'section'
        excludes = []
        allowed_methods = ['get']
        authentication = Authentication()
        authorization = ReadOnlyAuthorization()
        filtering = {
            'num': ALL,
            'heading': ALL,
            'subheading': ALL,
            'parent': ALL,
        }


class SpeakerResource(NamespacedModelResource):
    def get_object_list(self, request):
        return super(SpeakerResource, self).get_object_list(request).filter(instance=request.instance)

    class Meta:
        queryset = Speaker.objects.all()
        resource_name = 'speaker'
        excludes = []
        allowed_methods = ['get']
        authentication = Authentication()
        authorization = ReadOnlyAuthorization()
        filtering = {
            'name': ALL,
        }


class SpeechResource(NamespacedModelResource):
    speaker = fields.ForeignKey(SpeakerResource, 'speaker', null=True, full=True)

    def apply_filters(self, request, applicable_filters):
        objects = super(SpeechResource, self).apply_filters(request, applicable_filters)
        if 'q' in request.GET:
            objects = objects.auto_query(request.GET['q'])
            objects = [result.object for result in objects]
        return objects

    def get_object_list(self, request):
        if 'q' in request.GET:
            return SearchQuerySet().models(Speech).narrow('instance:%s' % request.instance.label).load_all()
        return super(SpeechResource, self).get_object_list(request).filter(instance=request.instance)

    class Meta:
        queryset = Speech.objects.filter(public=True)
        resource_name = 'speech'
        excludes = ['celery_task_id', 'public']
        allowed_methods = ['get', 'post']
        authentication = Authentication()
        authorization = ReadOnlyAuthorization()
        filtering = {
            'speaker': ALL_WITH_RELATIONS,
            'start_date': ALL,
        }
