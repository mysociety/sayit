from datetime import datetime
import re

from leveson.names import fix_name

class Section(object):
    def __init__(self, title):
        self.title = title

class Speech(object):
    # Some state variables
    current_time = None
    current_section = None
    witness = None

    def __init__(self, speaker, text):
        self.speaker = speaker
        self.text = [ [ text ] ]
        self.time = self.current_time
        self.section = self.current_section

    def add_para(self, text):
        self.text.append([ text ])

    def add_text(self, text):
        self.text[-1].append(text)

    @classmethod
    def reset(cls):
        cls.current_time = None
        cls.current_section = None

def parse_transcript(text, url):
    print "PARSING %s" % url

    page, num = 1, 1
    if '2012-05-23pm' in url:
        # This transcript does not start again from page 1 unlike all the others
        page, num = 110, 7
    elif '2011-12-06am' in url:
        # This transcript we're ignoring a special correction, see below
        page, num = 1, 4

    indent = None
    first_indent = None
    interviewer = None
    state = 'text'
    speech = None
    Speech.reset()
    for line in text:
        # Page break
        if '\014' in line:
            page += 1
            num = 1
            first_indent = None
            continue

        # Empty line
        if re.match('\s*$', line):
            continue

        # Start of index, ignore from then on
        if re.match(' *\d+ +I ?N ?D ?E ?X$', line) or '...............' in line:
            state = 'index'
            continue
        if state == 'index':
            continue

        # Special case - ignore a one-off correction in this hearing
        if '2011-12-06am' in url and page == 1 and num <= 4 and not re.match(' +4', line):
            continue

        # Just after last line, there should be a page number
        if num == 26:
            m = re.match(' +(\d+)$', line)
            assert int(m.group(1)) == page
            continue

        # Let's check we haven't lost a line anywhere...
        assert re.match(' *%d( |$)' % num, line), '%s != %s' % (num, line)

        if not indent:
            left_space = len(line) - len(line.lstrip())
            if left_space == 1:
                indent = ' ' * 7
            if left_space == 13 or left_space == 11:
                indent = ' ' * 3

        line = re.sub('^ *%d(%s|$)' % (num, indent), '', line)
        num += 1

        # Okay, here we have a non-empty, non-page number, non-index line of just text
        # print page, num, line.encode('utf-8')

        # Empty line
        if re.match('\s*$', line):
            continue

        # Date at start
        m = re.match(' *((Mon|Tues|Wednes|Thurs|Fri)day,? ?)?\d+ (September|October|November|December|January|February|March|April|May|June|July) 201[12]$', line)
        if m:
            continue

        if state == 'adjournment':
            state = 'text'
            if re.match(' *(.*)\)$', line):
                speech.add_text(line.strip())
                continue

        # Time/message about lunch/adjournments
        if re.search('\(2.43$', line): line = '(2.43 pm)'
        line = re.sub('\((3.23 pm|3.07 pm|11.15 am)$', r'(\1)', line)
        # Special case one line of normal text that would be caught
        m = re.match(' *(\(.*\))(?:break|s)?$', line)
        if (m or '[Alarm sounded]' in line or 'Evidence by videolink' in line) \
          and 'published on the Hacked Off website at the time' not in line:
            try:
                line = m.group(1)
                line = line.replace('O2', '02')
                if re.match('\(1[3-9]\.', line):
                    time_format = '(%H.%M %p)'
                else:
                    time_format = '(%I.%M %p)'
                Speech.current_time = datetime.strptime(line, time_format).time()
            except:
                yield speech
                speech = Speech( speaker=None, text=line )
            continue
        # Multiline message about adjournment
        m = re.match(' *\(The (hearing|Inquiry|court) adjourned(?i)', line)
        if m:
            yield speech
            state = 'adjournment'
            speech = Speech( speaker=None, text=line.strip() )
            continue

        # Questions
        m = re.match('Further questions from ([A-Z ]*)$|Question(?:s|ed|) (?:from by|from|by) (.*?)(?: \(continued\))?$', line.strip())
        if m:
            interviewer = fix_name(m.group(1) or m.group(2))
            continue

        # Headings
        m = re.match('Reply to the Responses to his Application by [A-Z ]*$|Response to .* Application$|Directions [Hh]earing.*$|Application by [A-Z ]*$|Application to become a core participant$|Reading of evidence of [A-Z ]*$|RULING$|Ruling$|(Opening|Closing|Reply) submissions ((on|for) Module 3 )?by [A-Z ]*$|Statement by ([A-Z ]*|Lord Justice Leveson)$|Submissions? by ([A-Z ]*|Mr Garnham)$|Discussion$|Discussion re (procedure|timetable|administrative matters)$|Housekeeping$', line.strip())
        if m:
            Speech.current_section = Section( title=line.strip() )
            continue

        # Witness arriving
        m = re.match(" *((?:[A-Z]|Mr)(?:[A-Z' ,-]|Mc|Mr|and)+) \((.*)\)$", line)
        if m:
            Speech.witness = fix_name(m.group(1))
            if Speech.witness == 'DR GERALD PATRICK MCCANN AND DR KATE MARIE MCCANN':
                Speech.witness = 'MR MCCANN' # All the A.s are him
            if Speech.witness == 'MR JAMES WATSON AND MRS MARGARET WATSON':
                Speech.witness = 'MRS WATSON' # All the A.s are her
            if Speech.witness == 'MR MATTHEW BELL AND MR CHRISTOPHER JOHNSON':
                # The one A. is actually him from the following session
                Speech.witness = 'MR PIERS STEFAN PUGHE-MORGAN'
            if state == 'witness':
                Speech.current_section.title += ' / ' + line.strip()
            else:
                Speech.current_section = Section( title=line.strip() )
                state = 'witness'
            continue
        else:
            state = 'text'

        # Question/answer (speaker from previous lines)
        if '2011-11-30am' in url and line == 'Q.':
            line = 'Q. From the police.'
        m = re.match('([QA])\. (.*)', line)
        if m:
            yield speech
            if m.group(1) == 'A':
                assert Speech.witness
                speaker = Speech.witness
            else:
                assert interviewer
                speaker = interviewer
            speech = Speech( speaker=speaker, text=m.group(2) )
            continue

        # New speaker
        m = re.match(' *((?:[A-Z -]|Mc)+): (.*)', line)
        if m:
            yield speech
            speaker = fix_name(m.group(1))
            if not interviewer:
                interviewer = speaker
            speech = Speech( speaker=speaker, text=m.group(2) )
            continue

        if '2011-10-04' in url or '2011-09-06' in url:
            # New paragraph if indent a bit more than 'usual' for the page
            left_space = len(line) - len(line.lstrip())
            if left_space == 5: left_space = 4
            if page == 113: # Special manual fix for this one
                first_indent = 3
            elif not first_indent:
                first_indent = left_space
            elif first_indent > left_space + 1:
                # The first line must have been a new paragraph. Adjust accordingly.
                first_indent = left_space
                if len(speech.text[-1])>1:
                    speech.add_para(speech.text[-1][-1])
                    del speech.text[-2][-1]
            m = re.match(' ' * (first_indent+2), line)
        else:
            # New paragraph if indent at least 8 spaces
            m = re.match('        ', line)
        if m:
            speech.add_para(line.strip())
            continue

        # If we've got this far, hopefully just a normal line of speech
        speech.add_text(line.strip())

    yield speech
