from haystack.backends.elasticsearch_backend import ElasticsearchSearchBackend, ElasticsearchSearchEngine

class SayitElasticBackend(ElasticsearchSearchBackend):
    """Subclass in order to add and use a snowball_nostop analyzer - same as
    the snowball analyzer but without the stop token filter."""

    def __init__(self, connection_alias, **connection_options):
        super(SayitElasticBackend, self).__init__(connection_alias, **connection_options)

        self.DEFAULT_SETTINGS['settings']['analysis']['analyzer']['snowball_nostop'] = {
            'type': 'custom',
            'tokenizer': 'standard',
            'filter': [ 'standard', 'lowercase', 'snowball' ],
            'char_filter': [ 'html_strip' ]
        }

    def build_schema(self, fields):
        content_field_name, mapping = super(SayitElasticBackend, self).build_schema(fields)

        # Change all the mappings that were 'snowball' to 'snowball_nostop'
        for field_name, field_class in fields.items():
            field_mapping = mapping[field_class.index_fieldname]

            if field_mapping['type'] == 'string' and field_class.indexed:
                if not hasattr(field_class, 'facet_for') and not field_class.field_type in('ngram', 'edge_ngram'):
                    field_mapping["analyzer"] = "snowball_nostop"

            mapping.update({ field_class.index_fieldname: field_mapping })

        return (content_field_name, mapping)

class SayitElasticSearchEngine(ElasticsearchSearchEngine):
    """Subclass to use the new subclassed backend"""
    backend = SayitElasticBackend
