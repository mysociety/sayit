import logging

logger = logging.getLogger(__name__)


class ImporterBase(object):
    def __init__(self, instance=None, commit=True, clobber=None, verify=True, **kwargs):
        self.instance = instance
        self.commit = commit
        self.clobber = clobber
        self.verify = verify
        self.speakers = {}

        self.stats = {}

    def make(self, cls, **kwargs):
        self.stats.setdefault(cls, 0)
        self.stats[cls] += 1

        s = cls(instance=self.instance, **kwargs)
        if self.commit:
            s.save()
        elif s.heading:
            logger.info(s.heading)
        return s
