from django.db.models import Aggregate
from django.db.models.sql.aggregates import Aggregate as SQLAggregate

class SQLLength(SQLAggregate):
    sql_function = 'LENGTH'

class Length(Aggregate):
    name = 'Length'

    def add_to_query(self, query, alias, col, source, is_summary):
        aggregate = SQLLength(col, source=source, is_summary=is_summary, **self.extra)
        query.aggregates[alias] = aggregate
