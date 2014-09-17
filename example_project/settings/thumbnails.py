# Class attribute so as not to activate and get caught in a circle
from easy_thumbnails.conf import Settings

_processors = []
for processor in Settings.THUMBNAIL_PROCESSORS:
    # Before the default scale_and_crop, insert our face_crop
    if processor == 'easy_thumbnails.processors.scale_and_crop':
        _processors.append('speeches.thumbnail_processors.face_crop')
    _processors.append(processor)

THUMBNAIL_PROCESSORS = tuple(_processors)
