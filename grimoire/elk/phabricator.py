#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
#
# Copyright (C) 2015-2016 Bitergia
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

import logging

from datetime import datetime

from dateutil import parser

from grimoire.elk.enrich import Enrich

from .utils import get_time_diff_days, unixtime_to_datetime


TASK_OPEN_STATUS = 'open'
TASK_CLOSED_STATUS = 'resolved'

class PhabricatorEnrich(Enrich):

    def __init__(self, db_sortinghat=None, db_projects_map=None, json_projects_map=None, insecure=True):
        super().__init__(db_sortinghat, db_projects_map, json_projects_map, insecure)

        self.tasks_closed = 0
        self.tasks_opened = 0
        self.phab_ids_names = {}  # To convert from phab ids to phab names

    def get_field_event_unique_id(self):
        return "transactionID"

    def get_elastic_mappings(self):

        mapping = """
        {
            "properties": {
                "main_description_analyzed": {
                  "type": "string",
                  "index":"analyzed"
                },
                "author_roles_analyzed": {
                  "type": "string",
                  "index":"analyzed"
                },
                "assigned_to_roles_analyzed": {
                  "type": "string",
                  "index":"analyzed"
                 },
                "author_roles_analyzed": {
                   "type": "string",
                   "index":"analyzed"
                 },
                "tags_analyzed": {
                   "type": "string",
                   "index":"analyzed"
                 },
                "tags_custom_analyzed" : {
                    "type" : "string",
                    "analyzer" : "comma"
                }
           }
        } """

        return {"items":mapping}

    def get_identities(self, item):
        """ Return the identities from an item """
        identities = []

        if 'authorData' in item['data']['fields']:
            user = self.get_sh_identity(item['data']['fields']['authorData'])
            identities.append(user)

        if 'ownerData' in item['data']['fields']:
            user = self.get_sh_identity(item['data']['fields']['ownerData'])
            identities.append(user)

        return identities

    def get_sh_identity(self, user):
        identity = {}
        identity['email'] = None
        identity['username'] = user['userName']
        identity['name'] = user['realName']

        return identity

    def get_item_sh(self, item):
        """ Add sorting hat enrichment fields for the author of the item """

        eitem = {}  # Item enriched

        if 'authorData' in item['data']['fields']:
            identity  = self.get_sh_identity(item['data']['fields']['authorData'])
            eitem.update(self.get_item_sh_fields(identity, parser.parse(item[self.get_field_date()])))
        if 'ownerData' in item['data']['fields']:
            identity  = self.get_sh_identity(item['data']['fields']['ownerData'])
            assigned_to = {}
            assigned_to["assigned_to_name"] = identity['name']
            assigned_to["assigned_to_user_name"] = identity['username']
            assigned_to["assigned_to_uuid"] = self.get_uuid(identity, self.get_connector_name())
            assigned_to["assigned_to_org_name"] = self.get_enrollment(assigned_to["assigned_to_uuid"], parser.parse(item[self.get_field_date()]))
            assigned_to["assigned_to_bot"] = self.is_bot(assigned_to['assigned_to_uuid'])
            assigned_to["assigned_to_domain"] = self.get_identity_domain(identity)
            eitem.update(assigned_to)

        return eitem

    def get_rich_events(self, item):
        """
        In the events there are some common fields with the task. The name
        of the field must be the same in the task and in the event
        so we can filer using it in task and event at the same time.

        * Fields that don't change: the field does not change with the events
        in a task so the value is always the same in the events of a task.

        * Fields that change: the value of teh field changes with events
        """
        events = []

        # To get values from the task
        eitem = self.get_rich_item(item)

        # Fields that don't change never
        task_fields_nochange = ['author_userName', 'creation_date', 'url', 'id', 'bug_id']

        # Follow changes in this fields
        task_fields_change = ['priority_value', 'status', 'assigned_to_userName', 'tags_custom_analyzed']
        task_change = {}
        for f in task_fields_change:
            task_change[f] = None
        task_change['status'] = TASK_OPEN_STATUS
        task_change['tags_custom_analyzed'] = eitem['tags_custom_analyzed']

        # Events are in transactions field (changes in fields)
        # We need to revert them to go from older to newer
        item['data']['transactions'].reverse()
        transactions = item['data']['transactions']
        for t in transactions:
            event = {}
            # Needed for incremental updates from the item
            event['metadata__updated_on'] = item['metadata__updated_on']
            event['origin'] = item['origin']
            # Real event data
            event['transactionID'] = t['transactionID']
            event['type'] = t['transactionType']
            event['username'] = None
            if 'authorData' in t and 'userName' in t['authorData']:
                event['event_author_name'] = t['authorData']['userName']
            event['update_date'] = unixtime_to_datetime(float(t['dateCreated'])).isoformat()
            event['oldValue'] = ''
            event['newValue'] = ''
            if event['type'] == 'core:edge':
                for val in t['oldValue']:
                    if val in self.phab_ids_names:
                        val = self.phab_ids_names[val]
                    event['oldValue'] += "," + val
                event['oldValue'] = event['oldValue'][1:]  # remove first comma
                for val in t['newValue']:
                    if val in self.phab_ids_names:
                        val = self.phab_ids_names[val]
                    event['newValue'] += "," + val
                event['newValue'] = event['newValue'][1:]  # remove first comma
            elif event['type'] in  ['status', 'description', 'priority', 'reassign', 'title', 'space', 'core:create', 'parent']:
                # Convert to str so the field is always a string
                event['oldValue'] = str(t['oldValue'])
                if event['oldValue'] in self.phab_ids_names:
                    event['oldValue'] = self.phab_ids_names[event['oldValue']]
                event['newValue'] = str(t['newValue'])
                if event['newValue'] in self.phab_ids_names:
                    event['newValue'] = self.phab_ids_names[event['newValue']]
            elif event['type'] == 'core:comment':
                event['newValue'] = t['comments']
            elif event['type'] == 'core:subscribers':
                event['newValue']= ",".join(t['newValue'])
            else:
                # logging.debug("Event type %s old to new value not supported", t['transactionType'])
                pass

            for f in task_fields_nochange:
                # The field name must be the same than in task for filtering
                event[f] = eitem[f]

            # To track history of some fields
            if event['type'] in ['status']:
                task_change['status'] = event['newValue']
            elif event['type'] == 'priority':
                task_change['priority'] =  event['newValue']
            elif event['type'] == 'core:edge':
                task_change['tags_custom_analyzed'] =  event['newValue']
            if event['type'] in  ['reassign']:
                # Try to get the userName and not the user id
                if event['newValue'] in self.phab_ids_names:
                    task_change['assigned_to_userName'] = self.phab_ids_names[event['newValue']]
                    event['newValue'] = task_change['assigned_to_userName']
                else:
                    task_change['assigned_to_userName'] = event['newValue']
                if event['oldValue'] in self.phab_ids_names:
                    # Try to get the userName and not the user id
                    event['oldValue'] = self.phab_ids_names[event['oldValue']]


            for f in task_change:
                event[f] = task_change[f]

            # For the burn vis
            if event['type'] in  ['core:create']:
                self.tasks_opened += 1
            if event['newValue'] in ['resolved']:
                self.tasks_closed += 1
            event['tasks_opened'] = self.tasks_opened
            event['tasks_closed'] = self.tasks_closed
            event['tasks_burn'] = self.tasks_opened-self.tasks_closed

            events.append(event)

        return events


    def __fill_phab_ids(self, item):
        """ Get mappings between phab ids and names """
        for p in item['projects']:
            self.phab_ids_names[p['phid']] = p['name']
        self.phab_ids_names[item['fields']['authorData']['phid']] = item['fields']['authorData']['userName']
        if 'ownerData' in item['fields']:
            self.phab_ids_names[item['fields']['ownerData']['phid']] = item['fields']['ownerData']['userName']
        if 'priority' in item['fields']:
            val = item['fields']['priority']['value']
            self.phab_ids_names[str(val)] = item['fields']['priority']['name']
        for t in item['transactions']:
            if 'userName' in t['authorData']:
                self.phab_ids_names[t['authorData']['phid']] = t['authorData']['userName']
            elif 'name' in t['authorData']:
                # Herald
                self.phab_ids_names[t['authorData']['phid']] = t['authorData']['name']

    def get_rich_item(self, item):
        eitem = {}

        self.__fill_phab_ids(item['data'])

        # metadata fields to copy
        copy_fields = ["metadata__updated_on", "metadata__timestamp", "ocean-unique-id", "origin"]
        for f in copy_fields:
            if f in item:
                eitem[f] = item[f]
            else:
                eitem[f] = None
        # The real data
        phab_item = item['data']

        # data fields to copy
        copy_fields = ["phid", "id", "type"]
        for f in copy_fields:
            if f in phab_item:
                eitem[f] = phab_item[f]
            else:
                eitem[f] = None
        # Fields which names are translated
        map_fields = {
            "id": "bug_id"
        }
        for f in map_fields:
            if f in phab_item:
                eitem[map_fields[f]] = phab_item[f]
            else:
                eitem[map_fields[f]] = None

        eitem['num_changes'] = len(phab_item['transactions'])

        if 'authorData' in phab_item['fields']:
            eitem['author_roles'] = ",".join(phab_item['fields']['authorData']['roles'])
            eitem['author_roles_analyzed'] = eitem['author_roles']
            eitem['author_userName'] = phab_item['fields']['authorData']['userName']
            eitem['author_realName'] = phab_item['fields']['authorData']['realName']
        if 'ownerData' in phab_item['fields']:
            eitem['assigned_to_roles'] = ",".join(phab_item['fields']['ownerData']['roles'])
            eitem['assigned_to_roles_analyzed'] = eitem['assigned_to_roles']
            eitem['assigned_to_userName'] = phab_item['fields']['ownerData']['userName']
            eitem['assigned_to_realName'] = phab_item['fields']['ownerData']['realName']

        eitem['priority'] = phab_item['fields']['priority'] ['name']
        eitem['priority_value'] = phab_item['fields']['priority']['value']
        eitem['status'] = phab_item['fields']['status']['value']
        eitem['creation_date'] = unixtime_to_datetime(phab_item['fields']['dateCreated']).isoformat()
        eitem['modification_date'] = unixtime_to_datetime(phab_item['fields']['dateModified']).isoformat()
        eitem['update_date'] = unixtime_to_datetime(item['updated_on']).isoformat()
        # raise
        eitem['main_description'] = phab_item['fields']['name']
        eitem['main_description_analyzed'] = eitem['main_description']
        eitem['url'] = eitem['origin']+"/T"+str(eitem['bug_id'])

        eitem['timeopen_days'] = \
            get_time_diff_days(eitem['creation_date'], eitem['update_date'])
        if eitem['status'] == TASK_OPEN_STATUS:
            eitem['timeopen_days'] = \
                get_time_diff_days(eitem['creation_date'], datetime.utcnow())

        eitem['changes'] = len(phab_item['transactions'])
        # Number of assignments changes
        eitem['changes_assignment'] = 0
        # Number of assignees in the changes
        eitem['changes_assignee_number'] = 0
        # List the changes assignees
        changes_assignee_list = []
        for change in phab_item['transactions']:
            if change["transactionType"] == "reassign":
                if change['authorData']['userName'] not in changes_assignee_list:
                    changes_assignee_list.append(change['authorData']['userName'])
                eitem['changes_assignment'] += 1
        eitem['changes_assignee_number'] = len(changes_assignee_list)
        eitem['changes_assignee_list'] = ','.join(changes_assignee_list)
        eitem['comments'] = 0
        for tr in phab_item['transactions']:
            if tr ['comments']:
                eitem['comments'] += 1

        eitem['tags'] = None
        for project in phab_item['projects']:
            if not eitem['tags']:
                eitem['tags'] = project['name']
            else:
                eitem['tags'] += ',' + project['name']
        eitem['tags_analyzed'] = eitem['tags']
        eitem['tags_custom_analyzed'] = eitem['tags']

        if self.sortinghat:
            eitem.update(self.get_item_sh(item))

        eitem.update(self.get_grimoire_fields(eitem['creation_date'], "task"))

        return eitem
