# API Resources
# Uses Tastypie to do most of the hard work
# http://django-tastypie.readthedocs.org/en/v0.9.11/tutorial.html
from tastypie import fields
from tastypie.resources import ModelResource
from tastypie.authentication import Authentication
from tastypie.authorization import ReadOnlyAuthorization
from speeches.models import Speech, Speaker

class SpeakerResource(ModelResource):
    def get_object_list(self, request):
        return super(SpeakerResource, self).get_object_list(request).filter(instance=request.instance)

    class Meta:
        queryset = Speaker.objects.all()
        resource_name = 'speaker'
        excludes = []
        allowed_methods = ['get']
        authentication = Authentication()
        authorization = ReadOnlyAuthorization()

class SpeechResource(ModelResource):
    speaker = fields.ForeignKey(SpeakerResource, 'speaker', null=True)

    def get_object_list(self, request):
        return super(SpeechResource, self).get_object_list(request).filter(instance=request.instance)

    class Meta:
        queryset = Speech.objects.all()
        resource_name = 'speech'
        excludes = ['celery_task_id']
        allowed_methods = ['get', 'post']
        authentication = Authentication()
        authorization = ReadOnlyAuthorization()
