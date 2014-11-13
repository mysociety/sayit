import logging

logger = logging.getLogger(__name__)


class ImporterBase (object):
    def __init__(self, instance=None, commit=True, clobber=None, **kwargs):
        self.instance = instance
        self.commit = commit
        self.clobber = clobber
        self.speakers = {}

    def make(self, cls, **kwargs):
        s = cls(instance=self.instance, **kwargs)
        if self.commit:
            s.save()
        elif s.heading:
            logger.info(s.heading)
        return s
