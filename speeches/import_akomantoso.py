import calendar
import datetime
import logging
import os

from lxml import etree
from lxml import objectify

from django.db import models
from django.utils import timezone

from popit.models import Person
from speeches.models import Section, Speech

logger = logging.getLogger(__name__)

class SpeechImportException (Exception):
    pass

class ImportAkomaNtoso (object):

    def __init__(self, instance=None):
        self.instance = instance

    def import_xml(self, document_path):
        # try:
        tree = objectify.parse(document_path)
        xml = tree.getroot()

        debateBody = xml.debate.debateBody
        mainSection = debateBody.debateSection 

        title = '%s (%s)' % (
                mainSection.heading.text, 
                etree.tostring(xml.debate.preface.p, method='text'))

        section = Section.objects.create(instance=self.instance, title=title)

        self.visit(mainSection, section)

        return section

        #except Exception as e:
            #'raise e
            # raise SpeechImportException(str(e))

    def visit(self, node, section):
       for child in node.iterchildren():
            tagname = etree.QName(child.tag).localname
            if tagname == 'debateSection':
                title = child.heading.text
                childSection = section.children.create(instance=self.instance, title=title)
                self.visit(child, childSection)
            elif tagname == 'speech':
                text = etree.tostring(child, method='text')
                speech = section.speech_set.create(
                        instance = self.instance,
                        # title
                        # event
                        # location
                        # speaker
                        # {start,end}_{date,time}
                        # tags
                        # source_url
                        text = text,
                        )
            else:
                text = etree.tostring(child, method='text')
                speech = section.speech_set.create(
                        instance = self.instance,
                        # title
                        # event
                        # location
                        # speaker # UNKNOWN
                        # {start,end}_{date,time}
                        # tags
                        # source_url
                        text = text,
                        )
