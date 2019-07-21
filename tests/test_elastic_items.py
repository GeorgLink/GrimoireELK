# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2019 Bitergia
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
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
# Authors:
#     Valerio Cosentino <valcos@bitergia.com>
#

import logging
import sys
import unittest
from grimoire_elk.elastic_items import (ElasticItems,
                                        FILTER_DATA_ATTR)


if '..' not in sys.path:
    sys.path.insert(0, '..')


class TestElasticItems(unittest.TestCase):
    """Unit tests for ElasticItems class"""

    def test_set_filter_raw(self):
        """Test whether the filter raw is properly set"""

        ei = ElasticItems(None)

        filter_raws = [
            "{}product:Firefox, for Android,{}component:Logins, Passwords and Form Fill".format(FILTER_DATA_ATTR,
                                                                                                FILTER_DATA_ATTR),
            "{}product:Add-on SDK".format(FILTER_DATA_ATTR),
            "{}product:Add-on SDK,    {}component:Documentation".format(FILTER_DATA_ATTR, FILTER_DATA_ATTR),
            "{}product:Add-on SDK, {}component:General".format(FILTER_DATA_ATTR, FILTER_DATA_ATTR),
            "{}product:addons.mozilla.org Graveyard,       {}component:API".format(FILTER_DATA_ATTR, FILTER_DATA_ATTR),
            "{}product:addons.mozilla.org Graveyard,   {}component:Add-on Builder".format(FILTER_DATA_ATTR,
                                                                                          FILTER_DATA_ATTR),
            "{}product:Firefox for Android,{}component:Build Config & IDE Support".format(FILTER_DATA_ATTR,
                                                                                          FILTER_DATA_ATTR),
            "{}product:Firefox for Android,{}component:Logins, Passwords and Form Fill".format(FILTER_DATA_ATTR,
                                                                                               FILTER_DATA_ATTR),
            "{}product:Mozilla Localizations,{}component:nb-NO / Norwegian Bokm\u00e5l".format(FILTER_DATA_ATTR,
                                                                                               FILTER_DATA_ATTR),
            "{}product:addons.mozilla.org Graveyard,{}component:Add-on Validation".format(FILTER_DATA_ATTR,
                                                                                          FILTER_DATA_ATTR),
        ]

        expected = [
            [
                {
                    "name": FILTER_DATA_ATTR + "product",
                    "value": "Firefox, for Android"
                },
                {
                    "name": FILTER_DATA_ATTR + "component",
                    "value": "Logins, Passwords and Form Fill"
                }
            ],
            [
                {
                    "name": FILTER_DATA_ATTR + "product",
                    "value": "Add-on SDK"
                }
            ],
            [
                {
                    "name": FILTER_DATA_ATTR + "product",
                    "value": "Add-on SDK"
                },
                {
                    "name": FILTER_DATA_ATTR + "component",
                    "value": "Documentation"
                }
            ],
            [
                {
                    "name": FILTER_DATA_ATTR + "product",
                    "value": "Add-on SDK"
                },
                {
                    "name": FILTER_DATA_ATTR + "component",
                    "value": "General"
                }
            ],
            [
                {
                    "name": FILTER_DATA_ATTR + "product",
                    "value": "addons.mozilla.org Graveyard"
                },
                {
                    "name": FILTER_DATA_ATTR + "component",
                    "value": "API"
                }
            ],
            [
                {
                    "name": FILTER_DATA_ATTR + "product",
                    "value": "addons.mozilla.org Graveyard"
                },
                {
                    "name": FILTER_DATA_ATTR + "component",
                    "value": "Add-on Builder"
                }
            ],
            [
                {
                    "name": FILTER_DATA_ATTR + "product",
                    "value": "Firefox for Android"
                },
                {
                    "name": FILTER_DATA_ATTR + "component",
                    "value": "Build Config & IDE Support"
                }
            ],
            [
                {
                    "name": FILTER_DATA_ATTR + "product",
                    "value": "Firefox for Android"
                },
                {
                    "name": FILTER_DATA_ATTR + "component",
                    "value": "Logins, Passwords and Form Fill"
                }
            ],
            [
                {
                    "name": FILTER_DATA_ATTR + "product",
                    "value": "Mozilla Localizations"
                },
                {
                    "name": FILTER_DATA_ATTR + "component",
                    "value": "nb-NO / Norwegian Bokm\u00e5l"
                }
            ],
            [
                {
                    "name": FILTER_DATA_ATTR + "product",
                    "value": "addons.mozilla.org Graveyard"
                },
                {
                    "name": FILTER_DATA_ATTR + "component",
                    "value": "Add-on Validation"
                }
            ]
        ]

        for i, filter_raw in enumerate(filter_raws):
            ei.set_filter_raw(filter_raw)

            self.assertDictEqual(ei.filter_raw_dict[0], expected[i][0])

            if len(ei.filter_raw_dict) > 1:
                self.assertDictEqual(ei.filter_raw_dict[1], expected[i][1])

    def test_set_filter_raw_should(self):
        """Test whether the filter raw should is properly set"""

        ei = ElasticItems(None)

        filter_raws = [
            "{}product:Firefox, for Android,{}component:Logins, Passwords and Form Fill".format(
                FILTER_DATA_ATTR,
                FILTER_DATA_ATTR),
            "{}product:Add-on SDK".format(FILTER_DATA_ATTR),
            "{}product:Add-on SDK,    {}component:Documentation".format(FILTER_DATA_ATTR, FILTER_DATA_ATTR),
            "{}product:Add-on SDK, {}component:General".format(FILTER_DATA_ATTR, FILTER_DATA_ATTR),
            "{}product:addons.mozilla.org Graveyard,       {}component:API".format(FILTER_DATA_ATTR, FILTER_DATA_ATTR),
            "{}product:addons.mozilla.org Graveyard,   {}component:Add-on Builder".format(FILTER_DATA_ATTR,
                                                                                          FILTER_DATA_ATTR),
            "{}product:Firefox for Android,{}component:Build Config & IDE Support".format(FILTER_DATA_ATTR,
                                                                                          FILTER_DATA_ATTR),
            "{}product:Firefox for Android,{}component:Logins, Passwords and Form Fill".format(FILTER_DATA_ATTR,
                                                                                               FILTER_DATA_ATTR),
            "{}product:Mozilla Localizations,{}component:nb-NO / Norwegian Bokm\u00e5l".format(FILTER_DATA_ATTR,
                                                                                               FILTER_DATA_ATTR),
            "{}product:addons.mozilla.org Graveyard,{}component:Add-on Validation".format(FILTER_DATA_ATTR,
                                                                                          FILTER_DATA_ATTR)
        ]

        expected = [
            [
                {
                    "name": FILTER_DATA_ATTR + "product",
                    "value": "Firefox, for Android"
                },
                {
                    "name": FILTER_DATA_ATTR + "component",
                    "value": "Logins, Passwords and Form Fill"
                }
            ],
            [
                {
                    "name": FILTER_DATA_ATTR + "product",
                    "value": "Add-on SDK"
                }
            ],
            [
                {
                    "name": FILTER_DATA_ATTR + "product",
                    "value": "Add-on SDK"
                },
                {
                    "name": FILTER_DATA_ATTR + "component",
                    "value": "Documentation"
                }
            ],
            [
                {
                    "name": FILTER_DATA_ATTR + "product",
                    "value": "Add-on SDK"
                },
                {
                    "name": FILTER_DATA_ATTR + "component",
                    "value": "General"
                }
            ],
            [
                {
                    "name": FILTER_DATA_ATTR + "product",
                    "value": "addons.mozilla.org Graveyard"
                },
                {
                    "name": FILTER_DATA_ATTR + "component",
                    "value": "API"
                }
            ],
            [
                {
                    "name": FILTER_DATA_ATTR + "product",
                    "value": "addons.mozilla.org Graveyard"
                },
                {
                    "name": FILTER_DATA_ATTR + "component",
                    "value": "Add-on Builder"
                }
            ],
            [
                {
                    "name": FILTER_DATA_ATTR + "product",
                    "value": "Firefox for Android"
                },
                {
                    "name": FILTER_DATA_ATTR + "component",
                    "value": "Build Config & IDE Support"
                }
            ],
            [
                {
                    "name": FILTER_DATA_ATTR + "product",
                    "value": "Firefox for Android"
                },
                {
                    "name": FILTER_DATA_ATTR + "component",
                    "value": "Logins, Passwords and Form Fill"
                }
            ],
            [
                {
                    "name": FILTER_DATA_ATTR + "product",
                    "value": "Mozilla Localizations"
                },
                {
                    "name": FILTER_DATA_ATTR + "component",
                    "value": "nb-NO / Norwegian Bokm\u00e5l"
                }
            ],
            [
                {
                    "name": FILTER_DATA_ATTR + "product",
                    "value": "addons.mozilla.org Graveyard"
                },
                {
                    "name": FILTER_DATA_ATTR + "component",
                    "value": "Add-on Validation"
                }
            ]
        ]

        for i, filter_raw in enumerate(filter_raws):
            ei.set_filter_raw_should(filter_raw)

            self.assertDictEqual(ei.filter_raw_should_dict[0], expected[i][0])

            if len(ei.filter_raw_should_dict) > 1:
                self.assertDictEqual(ei.filter_raw_should_dict[1], expected[i][1])


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
    unittest.main()
