from optparse import make_option
from six.moves.urllib.request import urlopen
import xml.etree.ElementTree as etree

from django.core.management.base import BaseCommand, CommandError

from speeches.models import Section, Speech, Speaker
from instances.models import Instance

PLAYS = {
    "all_well.xml": "All's Well That Ends Well",
    "as_you.xml": "As You Like It",
    "a_and_c.xml": "Antony and Cleopatra",
    "com_err.xml": "A Comedy of Errors",
    "coriolan.xml": "Coriolanus",
    "cymbelin.xml": "Cymbeline",
    "dream.xml": "A Midsummer Night's Dream",
    "hamlet.xml": "Hamlet",
    "hen_iv_1.xml": "Henry IV, Part I",
    "hen_iv_2.xml": "Henry IV, Part II",
    "hen_v.xml": "Henry V",
    "hen_viii.xml": "Henry VIII",
    "hen_vi_1.xml": "Henry VI, Part 1",
    "hen_vi_2.xml": "Henry VI, Part 2",
    "hen_vi_3.xml": "Henry VI, Part 3",
    "john.xml": "The Life and Death of King John",
    "j_caesar.xml": "Julius Caesar",
    "lear.xml": "King Lear",
    "lll.xml": "Love's Labor's Lost",
    "macbeth.xml": "Macbeth",
    "merchant.xml": "The Merchant of Venice",
    "much_ado.xml": "Much Ado About Nothing",
    "m_for_m.xml": "Measure for Measure",
    "m_wives.xml": "The Merry Wives of Windsor",
    "othello.xml": "Othello",
    "pericles.xml": "Pericles",
    "rich_ii.xml": "Richard II",
    "rich_iii.xml": "Richard III",
    "r_and_j.xml": "Romeo and Juliet",
    "taming.xml": "The Taming of the Shrew",
    "tempest.xml": "The Tempest",
    "timon.xml": "Timon of Athens",
    "titus.xml": "Titus Andronicus",
    "troilus.xml": "Troilus and Cressida",
    "two_gent.xml": "Two Gentlemen of Verona",
    "t_night.xml": "Twelfth Night",
    "win_tale.xml": "A Winter's Tale",
}


class Command(BaseCommand):
    args = '<play>'
    help = 'Import a Shakespeare play into a SayIt instance'
    option_list = BaseCommand.option_list + (
        make_option('--commit', action='store_true', help='Whether to commit to the database or not'),
        make_option('--instance', action='store', default='shakespeare', help='Label of instance to add data to'),
        make_option('--list', action='store_true', help='List the plays available'),
    )

    def make(self, cls, **kwargs):
        s = cls(instance=self.instance, **kwargs)
        if self.commit:
            s.save()
        elif s.heading:
            print(s.heading)
        return s

    def handle(self, *args, **options):
        if options['list'] or len(args) != 1:
            self.stdout.write('Plays:\n')
            for play in sorted(PLAYS.values()):
                self.stdout.write('* %s\n' % play)
            if not options['list']:
                raise CommandError("Please specify a play")
            return

        play = args[0]
        file = None
        for f, p in PLAYS.items():
            if play == p:
                file = f
                break

        if not file:
            raise CommandError("No matching play found")

        try:
            self.instance = Instance.objects.get(label=options['instance'])
        except:
            raise CommandError("Instance specified not found")

        self.commit = options['commit']

        xml = urlopen('http://www.ibiblio.org/xml/examples/shakespeare/%s' % file).read()
        play_xml = etree.fromstring(xml)
        play_section = self.make(Section, heading=play)

        speakers = {}
        for act in play_xml:
            if act.tag != 'ACT':
                continue
            act_heading = act[0].text
            act_section = self.make(Section, heading=act_heading, parent=play_section)
            scenes = act[1:]
            for scene in scenes:
                scene_heading = scene[0].text
                scene_section = self.make(Section, heading=scene_heading, parent=act_section)
                speeches_xml = scene[1:]
                for sp in speeches_xml:
                    if sp.tag == 'STAGEDIR' or sp.tag == 'SUBHEAD' or sp.tag == 'SUBTITLE':
                        self.make(Speech, section=scene_section, text='<p><i>%s</i></p>' % sp.text, type='narrative')
                        continue

                    if not sp[0].text:
                        speaker = None
                    elif self.commit:
                        name = sp[0].text.replace('[', '').replace(']', '')
                        if name in speakers:
                            speaker = speakers[name]
                        else:
                            speaker = Speaker.objects.create(name=name, instance=self.instance)
                            speakers[name] = speaker
                    else:
                        speaker = Speaker(name=sp[0].text, instance=self.instance)

                    text = ""
                    lines = sp[1:]
                    for line in lines:
                        if len(line):
                            text += '<i>%s</i>' % line[0].text
                            if line[0].tail:
                                text += ' %s' % line[0].tail.strip()
                            text += '<br>\n'
                        elif line.tag == 'LINE':
                            text += '%s<br>\n' % line.text
                        elif line.tag == 'STAGEDIR':
                            text += '<i>%s</i><br>\n' % line.text

                    text = '<p>%s</p>' % text
                    self.make(Speech, speaker=speaker, section=scene_section, text=text, type='speech')
