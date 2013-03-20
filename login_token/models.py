import random
import re

from django.contrib.auth.models import User
from django.db import models
from django.db import transaction
from django.db.models.signals import m2m_changed

from instances.models import InstanceMixin, Instance


NUMBER_OF_TOKEN_WORDS = 3

def generate_token():
    def useful_word(w):
        # FIXME: should try to exclude offensive words
        if len(w) < 4:
            return False
        if re.search('^[a-z]*$', w):
            return True
    words = []
    with open('/usr/share/dict/words') as fp:
        for line in fp:
            word = line.strip()
            if useful_word(word):
                words.append(word)
    return " ".join(random.choice(words)
                    for i in range(NUMBER_OF_TOKEN_WORDS))


class LoginToken(InstanceMixin, models.Model):
    '''Represents a readable login token for mobile devices

    To enable logging in to a SayIt instance as a particular user, we
    ask the user to type in a three word phrase; this model records
    tokens that allow login for a particular instance by a particular
    user.'''

    user = models.ForeignKey(User)
    token = models.TextField(max_length=255,
                             default=generate_token)

    def regenerate_token(self):
        token = generate_token()
        token.save()

    def __repr__(self):
        repr_format = '<LoginToken: "%s" user="%s" instance="%s">'
        return repr_format % (self.token,
                              self.user.username,
                              self.instance.label)


@transaction.commit_on_success
def handle_instance_users_change(*args, **kwargs):
    '''Keep login_token_logintoken and instances_instance_users in sync

    We use this as an m2m_changed signal handler for the sender
    Instance.users.through, for example with:

        m2m_changed.connect(handle_instance_users_change,
                            sender=Instance.users.through)

    Essentially, if anything is added / removed to the
    instance_instance_users table, the corresponding change is made to
    the login_token_logintoken table.  It would be more elegant to
    just have token as an extra field on the Instance <=> User join
    table, but it seemed good to be able to keep this application as
    an optional addition to the instances application.'''

    action = kwargs['action']
    primary_keys = kwargs['pk_set']

    # We don't get primary keys from pre_clear, post_clear, pre_remove
    # or post_remove, so in both removal cases, we try to work out
    # which keys have disappeared and remove them from
    # login_token_logintoken:

    if kwargs['reverse']:
        # Then the modification came through user.instances:
        user = kwargs['instance']
        if action == 'post_clear':
            iids_in_user_instances = set(i.id for i in user.instances.all())
            iids_in_login_token = set(lt.instance.id for lt in LoginToken.objects.filter(user=user))
            iids_to_remove = iids_in_login_token - iids_in_user_instances
            LoginToken.objects.filter(user=user,
                                      instance__in=iids_to_remove).delete()
        elif action == 'post_add':
            for instance_id in primary_keys:
                LoginToken.objects.create(instance=Instance.objects.get(pk=instance_id),
                                          user=user)
    else:
        # Then the modification came through instance.users
        instance = kwargs['instance']
        if action == 'post_clear':
            uids_in_instance_users = set(u.id for u in instance.users.all())
            uids_in_login_token = set(lt.user.id for lt in LoginToken.objects.filter(instance=instance))
            uids_to_remove = uids_in_login_token - uids_in_instance_users
            LoginToken.objects.filter(instance=instance,
                                      user__in=uids_to_remove).delete()
        elif action == 'post_add':
            for user_id in primary_keys:
                LoginToken.objects.create(instance=instance,
                                          user=User.objects.get(pk=user_id))

m2m_changed.connect(handle_instance_users_change,
                    sender=Instance.users.through)
