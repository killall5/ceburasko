from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
from ceburasko.stackwalk import accident_from_minidump
from ceburasko.utils import *
import os

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--limit',
                    action="store",
                    type="int",
                    dest="limit",
                    default=1000),
    )

    def handle(self, *args, **options):
        limit = options['limit']
        self.stdout.write('Import minidumps (%d max) ...' % limit)
        modified_issues = {}
        for minidump in Minidump.objects.all()[:limit]:
            self.stdout.write('Processing %s ...' % minidump.filepath)
            try:
                for raw_accident in accident_from_minidump(minidump.filepath, settings.BREAKPAD_SYMBOLS_PATH):
                    affected_binary = Binary.objects.filter(hash__in=raw_accident['ids'])[0]
                    # Get any of them
                    issue, accident = create_or_update_issue(
                        affected_binary,
                        raw_accident,
                        minidump.ip_address,
                        minidump.user_id,
                    )
                    if accident is not None:
                        modified_issues[issue.id] = issue
                    self.stdout.write('OK, issue #%d' % issue.id)
            except Exception as e:
                self.stderr.write('Error: %s' % str(e))
            finally:
                try:
                    os.unlink(minidump.filepath)
                except OSError as e:
                    self.stderr.write('Error removing %s: %s' % (minidump.filepath, str(e)))
                minidump.delete()
        update_modified_issues(modified_issues.values())
