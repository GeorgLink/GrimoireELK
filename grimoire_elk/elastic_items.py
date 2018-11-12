# -*- coding: utf-8 -*-
#
#
# Copyright (C) 2017 Bitergia
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
# Authors:
#   Alvaro del Castillo San Felix <acs@bitergia.com>
#

"""Generates items from ElasticSearch based on filters """


import logging
import json

from .enriched.utils import get_repository_filter, grimoire_con
from .elastic_mapping import Mapping

logger = logging.getLogger(__name__)


class ElasticItems():

    mapping = Mapping

    # In large projects like Eclipse commits, 100 is too much
    # Change it from p2o command line or mordred config
    scroll_size = 100

    def __init__(self, perceval_backend, from_date=None, insecure=True, offset=None):

        self.perceval_backend = perceval_backend
        self.last_update = None  # Last update in ocean items index for feed
        self.from_date = from_date  # fetch from_date
        self.offset = offset  # fetch from offset
        self.filter_raw = None  # to filter raw items from Ocean
        self.filter_raw_should = None  # to filter raw items from Ocean

        self.requests = grimoire_con(insecure)
        self.elastic = None
        self.elastic_url = None

    def get_repository_filter_raw(self, term=False):
        """ Returns the filter to be used in queries in a repository items """
        perceval_backend_name = self.get_connector_name()
        filter_ = get_repository_filter(self.perceval_backend, perceval_backend_name, term)
        return filter_

    def get_field_date(self):
        """ Field with the update in the JSON items. Now the same in all. """
        return "metadata__updated_on"

    def get_incremental_date(self):
        """
        Field with the date used for incremental analysis.
        """
        return "metadata__timestamp"

    def set_filter_raw(self, filter_raw):
        """ Filter to be used when getting items from Ocean index """
        self.filter_raw = filter_raw

    def set_filter_raw_should(self, filter_raw_should):
        """ Bool filter should to be used when getting items from Ocean index """
        self.filter_raw_should = filter_raw_should

    def get_connector_name(self):
        """ Find the name for the current connector """
        from .utils import get_connector_name
        return get_connector_name(type(self))

    # Items generator
    def fetch(self, _filter=None):
        """ Fetch the items from raw or enriched index. An optional _filter
        could be provided to filter the data collected """

        logger.debug("Creating a elastic items generator.")

        filter = None
        if _filter:
            filter = self.create_filter(_filter)

        items = self.elastic.search(query=filter)
        for item in items:
            yield item

        logger.debug("Fetching from %s: done receiving", self.elastic.index_url)

    def create_filter(self, _filter=None):
        """ Get the items from the index related to the backend applying and
        optional _filter if provided"""

        # If using a perceval backends always filter by repository
        # to support multi repository indexes
        # We need the filter dict as a string to join with the rest
        filters_dict = self.get_repository_filter_raw(term=True)
        if filters_dict:
            filters = json.dumps(filters_dict)
        else:
            filters = ''

        if self.filter_raw:
            filters += '''
                , {"term":
                    { "%s":"%s"  }
                }
            ''' % (self.filter_raw['name'], self.filter_raw['value'])

        if _filter:
            filter_str = '''
                , {"terms":
                    { "%s": %s }
                }
            ''' % (_filter['name'], _filter['value'])
            # List to string conversion uses ' that are not allowed in JSON
            filter_str = filter_str.replace("'", "\"")
            filters += filter_str

        if self.from_date:
            date_field = self.get_incremental_date()
            from_date = self.from_date.isoformat()

            filters += '''
                , {"range":
                    {"%s": {"gte": "%s"}}
                }
            ''' % (date_field, from_date)
        elif self.offset:
            filters += '''
                , {"range":
                    {"offset": {"gte": %i}}
                }
            ''' % (self.offset)

        # Order the raw items from the old ones to the new so if the
        # enrich process fails, it could be resume incrementally
        order_query = ''
        order_field = None
        if self.perceval_backend:
            order_field = self.get_incremental_date()
        if order_field is not None:
            order_query = ', "sort": { "%s": { "order": "asc" }} ' % order_field

        filters_should = ''
        if self.filter_raw_should:
            filters_should = json.dumps(self.filter_raw_should)[1:-1]
            # We need to add a bool should query to the outer must query
            query_should = '{"bool": {%s}}' % filters_should
            filters += ", " + query_should

        # Fix the filters string if it starts with "," (empty first filter)
        if filters.lstrip().startswith(','):
            filters = filters.lstrip()[1:]

        filters_dict = json.loads("[" + filters + "]")
        if len(filters_dict) == 0:
            # Avoid empty list of filters, ES 6.x doesn't like it
            # In this case, ensure that order_query does not start with ,
            if order_query.startswith(','):
                order_query = order_query[1:]
            query = """
            {
              %s
            }
            """ % (order_query)
        else:
            query = """
            {
                "query": {
                    "bool": {
                        "must": [%s]
                    }
                } %s
            }
            """ % (filters, order_query)

        return json.loads(query)
