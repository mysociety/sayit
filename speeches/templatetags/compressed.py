from __future__ import unicode_literals

from django.contrib.staticfiles.storage import staticfiles_storage

from django import template
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.conf import settings

register = template.Library()


class CompressedNode(template.Node):
    def __init__(self, name):
        self.name = template.Variable(name)

    def render(self, context):
        package_name = self.name.resolve(context)
        package = getattr(settings, self.setting_var, {}).get(package_name, {})
        return self.render_individual(package, package['source_filenames'])

    def render_thing(self, package, path):
        template_name = self.template_name
        context = package.get('extra_context', {})
        context.update({
            'type': self.content_type,
            'url': mark_safe(staticfiles_storage.url(path))
        })
        return render_to_string(template_name, context)

    def render_individual(self, package, paths):
        paths = [path.replace('.scss','.css') for path in paths]
        tags = [self.render_thing(package, path) for path in paths]
        return '\n'.join(tags)

class CompressedCSSNode(CompressedNode):
    setting_var = "PIPELINE_CSS"
    template_name = "pipeline/css.html"
    content_type = 'text/css'

class CompressedJSNode(CompressedNode):
    setting_var = 'PIPELINE_JS'
    template_name = 'pipeline/js.html'
    content_type = 'text/javascript'


@register.tag
def compressed_css(parser, token):
    try:
        tag_name, name = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError('%r requires exactly one argument: the name of a group in the PIPELINE_CSS setting' % token.split_contents()[0])
    return CompressedCSSNode(name)


@register.tag
def compressed_js(parser, token):
    try:
        tag_name, name = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError('%r requires exactly one argument: the name of a group in the PIPELINE_JS setting' % token.split_contents()[0])
    return CompressedJSNode(name)
