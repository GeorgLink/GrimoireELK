# -*- coding: utf-8 -*-
#
# GitLab Ocean feeder
#
# Copyright (C) 2015 Bitergia
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
#   Valerio Cosentino <valcos@bitergia.com>
#

from perceval.backends.core.gitlab import GitLabCommand

from .elastic import ElasticOcean
from ..elastic_mapping import Mapping as BaseMapping


class Mapping(BaseMapping):

    @staticmethod
    def get_elastic_mappings(es_major):
        """Get Elasticsearch mapping.

        :param es_major: major version of Elasticsearch, as string
        :returns:        dictionary with a key, 'items', with the mapping
        """

        mapping = '''
         {
            "dynamic":true,
                "properties": {
                    "data": {
                        "properties": {
                            "notes_data": {
                                "dynamic":false,
                                "properties": {
                                    "body": {
                                        "type": "text",
                                        "index": true
                                    }
                                }
                            },
                            "description": {
                                "type": "text",
                                "index": true
                            }
                        }
                    }
                }
        }
        '''

        return {"items": mapping}


class GitLabOcean(ElasticOcean):
    """GitLab Ocean feeder"""

    mapping = Mapping

    @classmethod
    def get_arthur_params_from_url(cls, url):
        """ Get the arthur params given a URL for the data source """
        params = {}

        args = cls.get_perceval_params_from_url(url)
        parser = GitLabCommand.setup_cmd_parser()

        parsed_args = parser.parse(*args)

        params['owner'] = parsed_args.owner
        params['repository'] = parsed_args.repository
        # include only blacklist ids information
        params['blacklist_ids'] = parsed_args.blacklist_ids

        return params

    @classmethod
    def get_perceval_params_from_url(cls, url):
        """ Get the perceval params given a URL for the data source """
        params = []

        tokens = url.split(' ')
        repo = tokens[0]

        owner = repo.split('/')[-2]
        repository = repo.split('/')[-1]

        params.append(owner)
        params.append(repository)

        if len(tokens) > 1:
            params.extend(tokens[1:])

        return params
