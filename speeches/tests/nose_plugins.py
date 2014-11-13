from nose.plugins import Plugin


class SkipMigrations(Plugin):
    name = 'skip-migrations'
    enabled = True

    def configure(self, options, conf):
        pass

    def wantDirectory(self, dirname):
        if 'migrations' in dirname:
            return False
        return None
