import json
import os

from django.core.management.base import BaseCommand, CommandError
from django.utils import six

import requests

from instances.models import Instance
from popolo.models import Membership, Organization, Post
from speeches.models import Speaker


def update_or_create(qs, defaults=None, **kwargs):
    defaults = defaults or {}
    obj, created = qs.get_or_create(defaults=defaults, **kwargs)
    if created:
        return obj, created
    for k, v in six.iteritems(defaults):
        setattr(obj, k, v)
    obj.save()
    return obj, False


def update_object(qs, data, extra=False, defaults=None, **kwargs):
    record, created = update_or_create(qs, defaults=defaults, **kwargs)

    for l in ('sources', 'links'):
        for item in data.get(l, []):
            rel = getattr(record, l)
            update_or_create(
                rel,
                # The following two rows were finally fixed to not be needed
                # in Django 1.7
                content_type=rel.content_type,
                object_id=rel.pk_val,
                url=item['url'],
                defaults={'note': item.get('note', '')}
            )
    # for link in data.get('contact_details', []):
    #     update_or_create(record.contact_details,
    #         #ContactDetail: label contact_type value note sources
    #     )
    if extra:
        update_or_create(
            record.identifiers,
            content_type=record.identifiers.content_type,
            object_id=record.identifiers.pk_val,
            identifier=data['id'],
            scheme='Popolo',
        )
        for i in data.get('identifiers', []):
            update_or_create(
                record.identifiers,
                content_type=record.identifiers.content_type,
                object_id=record.identifiers.pk_val,
                identifier=i['identifier'],
                scheme=i.get('scheme', ''),
            )
        for name in data.get('other_names', []):
            update_or_create(
                record.other_names,
                content_type=record.other_names.content_type,
                object_id=record.other_names.pk_val,
                name=name['name'],
                defaults={'note': name.get('note', '')},
            )

    return record


class Command(BaseCommand):
    args = 'base-url'
    help = 'Imports people, memberships and organizations in Popolo format'

    def get(self, path):
        if self.source_data:
            return self.source_data.get(path, [])
        else:
            return requests.get(self.source + path).json()

    def handle(self, *args, **options):
        if not args:
            raise CommandError('Please specify a source URL or file')
        elif len(args) > 1:
            raise CommandError('Unexpected arguments: %s' % args[1:])

        self.source = args[0]
        if os.path.exists(self.source):
            self.source_data = json.load(open(self.source))
        elif self.source.startswith('http'):
            self.source_data = None
            if not self.source.endswith('/'):
                self.source += '/'
        else:
            raise CommandError('Please specify a source URL or file')

        instance, _ = Instance.objects.get_or_create(label='default')

        for data in self.get('organizations'):
            # Other fields that could be in defaults:
            # parent dissolution_date founding_date
            defaults = {
                'name': data['name'],
                'classification': data['classification'],
            }
            update_object(
                Organization.objects, data, extra=True,
                identifiers__identifier=data['id'],
                defaults=defaults
            )

        for data in self.get('persons'):
            # Other fields that could be in defaults:
            # additional_name honorific_prefix/suffix patronymic_name
            # gender birth_date death_date summary biography
            defaults = {
                'name': data['name'],
                'family_name': data.get('family_name', ''),
                'given_name': data.get('given_name', ''),
                'sort_name': data.get('sort_name', ''),
                'email': data.get('email'),
                'image': data.get('image'),
            }
            update_object(
                Speaker.objects, data, extra=True,
                instance=instance, identifiers__identifier=data['id'],
                defaults=defaults
            )

        # XXX Post and Membership ID from JSON data should be stored somewhere,
        # so updates are easier
        posts = {}
        for data in self.get('posts'):
            defaults = {
                'role': data['role'],
                'organization': Organization.objects.get(
                    identifiers__identifier=data['organization_id']),
                'start_date': data.get('start_date', None),
                'end_date': data.get('end_date', None),
            }
            record = update_object(
                Post.objects, data,
                label=data['label'],
                defaults=defaults
            )
            if 'id' in data:
                posts[data['id']] = record

        for data in self.get('memberships'):
            # Other fields that could be in defaults:
            # on_behalf_of
            defaults = {
                # @see https://github.com/openpolis/django-popolo/pull/12
                'label': data.get('label', ''),
                'role': data.get('role', ''),
                'start_date': data.get('start_date', None),
                'end_date': data.get('end_date', None),
            }
            # XXX This uniqueness will fail for e.g. someone with multiple
            # memberships at the same organisation that don't have posts
            kwargs = {
                'organization': Organization.objects.get(
                    identifiers__identifier=data['organization_id']),
                'person': Speaker.objects.get(
                    identifiers__identifier=data['person_id']),
            }
            if data.get('post_id'):
                kwargs['post'] = posts[data['post_id']]

            update_object(
                Membership.objects, data,
                defaults=defaults, **kwargs
            )
