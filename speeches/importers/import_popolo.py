import os.path
import json
import requests

from django.utils import six
from django.forms import ValidationError
from django.utils.translation import ugettext as _

from instances.models import Instance
from popolo.models import Membership, Organization, Post

from speeches.models import Speaker

import logging
logger = logging.getLogger(__name__)


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

    return record, created


class PopoloImporterCreationError(ValidationError):
    pass


class PopoloImporter(object):
    popit_meta = None
    source_data = None

    def __init__(self, source, instance=None):
        if instance:
            self.instance = instance
        else:
            self.instance, created = Instance.objects.get_or_create(label='default')

        self.source = source

        try:
            if os.path.exists(self.source):
                json_src = json.load(open(self.source))
            elif self.source.startswith('http'):
                json_src = requests.get(source).json()
            else:
                raise PopoloImporterCreationError(
                    _('Either a file path or a URL is needed.'))
        except:
            raise PopoloImporterCreationError(
                _('Failed to decode JSON at %(source)s' % {'source': source}))

        # Look for meta and persons_api to identify popit.
        if type(json_src) == dict:
            # Look for persons key to identify source like
            # https://raw.githubusercontent.com/mysociety/pombola/0fd988606c31a31516ac782ebce00b9abfbb0c4d/pombola/south_africa/data/south-africa-popolo.json
            if 'persons' in json_src:
                self.source_data = json_src
                return

            try:
                json_src['meta']['persons_api_url']

                # This looks like sayit.
                self.popit_meta = json_src['meta']
                return
            except KeyError:
                pass

        elif type(json_src) is list:
            # Look for a single list, if we find one, assume it's
            # a list of persons
            self.source_data = {'persons': json_src}

        else:
            raise PopoloImporterCreationError(
                _('The json must contain either an object or an array'))

    def get_popit(self, path):
        data_url = self.popit_meta.get('%s_api_url' % path)

        while data_url:
            data = requests.get(data_url).json()

            if 'result' in data:
                data_url = data.get('next_url')

                # Looks like we have paginated data a la PopIt
                results = data['result']
            else:
                data_url = None

                # Probably we have all the data in a single file.
                results = data

            for x in results:
                yield x

    def get(self, path):
        if self.popit_meta:
            return self.get_popit(path)
        else:
            return self.source_data.get(path, [])

    def import_organizations(self):
        for data in self.get('organizations'):
            # Other fields that could be in defaults:
            # parent dissolution_date founding_date
            defaults = {
                # Limit to 128 characters as that's how big the name field
                # is in django-popolo
                'name': data['name'][:128],
                # 'classification': data['classification'],
            }
            update_object(
                Organization.objects, data, extra=True,
                identifiers__identifier=data['id'],
                defaults=defaults
            )

    def import_persons(self):
        created_count = 0
        refreshed_count = 0

        for data in self.get('persons'):
            # Other fields that could be in defaults:
            # additional_name honorific_prefix/suffix patronymic_name
            # gender birth_date death_date summary biography
            defaults = {
                'name': data['name'][:128],
                'family_name': data.get('family_name', ''),
                'given_name': data.get('given_name', ''),
                'sort_name': data.get('sort_name', ''),
                'email': data.get('email'),
                'image': data.get('image'),
            }
            record, created = update_object(
                Speaker.objects, data, extra=True,
                instance=self.instance, identifiers__identifier=data['id'],
                defaults=defaults
            )

            if created:
                created_count += 1
            else:
                refreshed_count += 1

        return {'created': created_count, 'refreshed': refreshed_count}

    def import_posts(self):
        self.posts = {}
        for data in self.get('posts'):
            defaults = {
                'role': data['role'],
                'organization': Organization.objects.get(
                    identifiers__identifier=data['organization_id']),
                'start_date': data.get('start_date', None),
                'end_date': data.get('end_date', None),
            }
            record, created = update_object(
                Post.objects, data,
                label=data['label'],
                defaults=defaults
            )
            if 'id' in data:
                self.posts[data['id']] = record

    def import_memberships(self):
        skipped_count = 0

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

            if not data.get('organization_id'):
                # django-popolo doesn't yet cope with a membership
                # without an organization:
                # https://github.com/openpolis/django-popolo/pull/14
                logger.info(
                    'Skipping membership %s with no organization_id' %
                    data['id'])
                skipped_count += 1
                continue

            # XXX This uniqueness will fail for e.g. someone with multiple
            # memberships at the same organisation that don't have posts
            kwargs = {
                'organization': Organization.objects.get(
                    identifiers__identifier=data['organization_id']),
                'person': Speaker.objects.get(
                    identifiers__identifier=data['person_id']),
            }

            if data.get('post_id'):
                kwargs['post'] = self.posts[data['post_id']]

            update_object(
                Membership.objects, data,
                defaults=defaults, **kwargs
            )

        logger.info(
            'Skipped %d records for not having an organization' % skipped_count)

    def import_all(self):
        # Organizations, posts, and memberships in django-popolo are
        # not instance aware, and this really needs sorting out before
        # we start storing them. Fortunately, we only actually use
        # persons at the moment.

        # self.import_organizations()
        self.import_persons()
        # self.import_posts()
        # self.import_memberships()
