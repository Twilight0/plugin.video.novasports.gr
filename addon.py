# -*- coding: utf-8 -*-

'''
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''


import sys
from resources.lib import novasports
from tulip.compat import parse_qsl

params = dict(parse_qsl(sys.argv[2].replace('?','')))

action = params.get('action')
url = params.get('url')
query = params.get('query')

if action is None or action == 'root':
    novasports.Indexer().root()

elif action == 'videos':
    novasports.Indexer().videos(url=url, query=query)

elif action == 'matches':
    novasports.Indexer().matches(query=query)

elif action == 'event':
    novasports.Indexer().event(url)

elif action == 'add_date':
    novasports.Indexer().add_date()

elif action == 'webtv':
    novasports.Indexer().webtv()

elif action == 'webtv_collection':
    novasports.Indexer().webtv_collection()

elif action == 'go_to_root':
    from tulip.directory import run_builtin
    run_builtin(action='root', path_history='replace')

elif action == 'play':
    novasports.Indexer().play(url)

elif action == 'cache_clear':
    from tulip import cache
    cache.clear(withyes=False)
