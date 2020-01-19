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
from __future__ import unicode_literals, absolute_import

from time import sleep
import re
from tulip.compat import bytes, str
from tulip import directory, client, cache, control
from datetime import date


CACHE_SIZE = int(control.setting('cache_size'))


class Indexer:

    def __init__(self):

        self.list = []
        self.data = []
        self.base_link = 'https://www.novasports.gr'
        self.api_link = ''.join([self.base_link, '/api/v1'])
        self.latest_link = ''.join([self.api_link, '/videos/feed'])
        self.live_link = ''.join([self.api_link, '/videos/livetv'])
        self.live_by_date_link = ''.join([self.api_link, '/videos/livebydate/{date}'])
        self.matches_link = ''.join([self.api_link, '/matchcenter/events/date/{date}'])
        self.event_link = ''.join([self.api_link, '/videos/event/{event}/teama/{team_a}/teamb/team_b'])
        self.sports_link = ''.join([self.api_link, '/webtv/{type}/{sport_id}/range/{range_id}/number/24'])
        self.webtv_link = ''.join([self.base_link, '/web-tv'])

    def root(self):

        self.list = [
            {
                'title': control.lang(32002),
                'action': 'videos',
                'url': self.live_link
            }
            ,
            {
                'title': control.lang(32001),
                'action': 'videos',
                'url': self.latest_link
            }
            ,
            {
                'title': control.lang(32003),
                'action': 'matches'
            }
            ,
            {
                'title': control.lang(32009),
                'action': 'webtv'
            }
            # ,
            # {
            #     'title': control.lang(32009),
            #     'action': 'webtv'
            # }
        ]

        for item in self.list:

            cache_clear = {'title': 32010, 'query': {'action': 'cache_clear'}}
            item.update({'cm': [cache_clear]})

        directory.add(self.list, content='videos')

    def videos(self, url, query=None):

        self.list = cache.get(self.items_list, CACHE_SIZE, url)

        if self.list is None:
            return

        for i in self.list:
            i.update({'action': 'play', 'isFolder': 'False'})

        if url == self.live_link:

            more_live = {
                'title': control.lang(32013),
                'url': self.live_by_date_link.format(date=bytes(date.today()).replace('-', '')),
                'action': 'videos',
                'query': bytes(date.today()).replace('-', '')
            }

            self.list.append(more_live)

        elif 'livebydate' in url:

            go_to_root = {
                'title': control.lang(32012),
                'action': 'go_to_root',
                'isFolder': 'False',
                'isPlayable': 'False'
            }

            next_live = {
                'title': control.lang(32006),
                'url': self.live_by_date_link.format(date=int(query) + 1),
                'action': 'videos',
                'query': bytes(int(query) + 1)
            }

            previous_live = {
                'title': control.lang(32007),
                'url': self.live_by_date_link.format(date=int(query) - 1),
                'action': 'videos',
                'query': bytes(int(query) - 1)
            }

            self.list.insert(0, next_live)
            self.list.append(previous_live)
            self.list.append(go_to_root)

        directory.add(self.list, content='videos')

    def items_list(self, url):

        if '/api/v1' not in url:

            html = client.request(url)

            json_id = client.parseDOM(html, 'div', attrs={'class': 'web-tv-container-.+'}, ret='class')[0]
            type_ = client.parseDOM(html, 'div', attrs={'class': 'vocabulary hidden'})[0]
            json_id = re.search(r'(\d+)', json_id).group(1)

            urls = [
                self.sports_link.format(type=type_ ,sport_id=json_id, range_id=i) for i in list(range(0, int(control.setting('pages_size')) + 1))
            ]

            for url in urls:

                _json = client.request(url, output='json')
                sleep(0.1)
                items = _json['Items']

                self.data.extend(items)

        else:

            self.data = client.request(url, output='json')

        for r in self.data:

            try:
                title = client.replaceHTMLCodes(r['Title'])
            except KeyError:
                continue

            if 'Is_Live' in r:
                title = '[CR]'.join([title, r['Live_From']])

            try:
                plot = client.replaceHTMLCodes(r['Short_Desc'])
            except TypeError:
                plot = control.lang(32011)
            urls = r['VideoUrl']

            for u in urls:

                data = {'title': title, 'plot': plot}

                image = r.get('Image')

                if image:
                    image = ''.join([self.base_link, image])
                    data.update({'image': image})
                else:
                    data.update({'icon': control.icon()})

                url = u['uri']

                data.update({'url': url})

                self.list.append(data)

        return self.list

    def matches(self, query=None):

        def appender(events):

            _list = []

            for event in events:

                event_name = event['event_name']

                match_centers = event['match_centers']

                for match in match_centers:

                    team_a = match['team_a']
                    team_b = match['team_b']
                    score_a = str(match['score_a'])
                    score_b = str(match['score_b'])
                    desc = match['desc']
                    if not desc:
                        desc = control.lang(32011)
                    _date = str(match['date'])
                    url = ''.join([self.base_link, match['alias_url']])

                    title = ''.join(
                        [
                            event_name, u': ', team_a, u' - ', team_b, u'[CR]', control.lang(32004),
                            score_a, u' - ', score_b, u' (', desc, u' | ', _date, u')'
                        ]
                    )

                    data = {'title': title, 'url': url, 'action': 'event'}

                    _list.append(data)

            return _list

        if not query:
            date_ = bytes(date.today()).replace('-', '')
        else:
            date_ = bytes(query)

        result = client.request(self.matches_link.format(date=date_), output='json')

        if not result['events'] and not result['friendly']:

            self.list = [{'title': control.lang(32008), 'action': 'matches'}]

        else:

            if result['events']:

                self.list.extend(appender(result['events']))

            if result['friendly']:

                self.list.extend(appender(result['friendly']))

        previous_date = {
            'title': control.lang(32007),
            'action': 'matches',
            'query': bytes(int(date_) - 1)
        }

        next_date = {
            'title': control.lang(32006),
            'action': 'matches',
            'query': bytes(int(date_) + 1)
        }

        add_date = {
            'title': control.lang(32005),
            'action': 'add_date',
            'isFolder': 'False',
            'isPlayable': 'False'
        }

        go_to_root = {
            'title': control.lang(32012),
            'action': 'go_to_root',
            'isFolder': 'False',
            'isPlayable': 'False'
        }

        self.list.insert(0, previous_date)
        self.list.append(next_date)
        self.list.append(add_date)
        self.list.append(go_to_root)

        directory.add(self.list)

    def add_date(self):

        input_date = control.inputDialog(type=control.input_date)

        input_date = ''.join(input_date.split('/')[::-1]).replace(' ',  '0')

        directory.run_builtin(action='matches', query=input_date)

    def event(self, url):

        html = client.request(url)

        event_id = client.parseDOM(html, 'div', attrs={'id': 'event_id'})[0]
        teama_id = client.parseDOM(html, 'div', attrs={'id': 'teama_id'})[0]
        teamb_id = client.parseDOM(html, 'div', attrs={'id': 'teamb_id'})[0]

        items = client.request(self.event_link.format(event=event_id, team_a=teama_id, team_b=teamb_id), output='json')

        videos = [i for i in items if ('Has_Videos' in i and i['Has_Videos']) or ('MediaType' in i and i['MediaType'] == 'video')]

        for video in videos:

            title = client.replaceHTMLCodes(video['Title'])

            try:
                image = video['ImageLowQuality']
                if image:
                    image = ''.join([self.base_link, image])
                else:
                    image = control.icon()
                fanart = video['Image']
                if fanart:
                    fanart = ''.join([self.base_link, fanart])
                else:
                    fanart = None
            except KeyError:
                image = video['Image']
                if image:
                    image = ''.join([self.base_link, image])
                else:
                    image = control.icon()
                fanart = None

            url = ''.join([self.base_link, video['Link']])

            data = {'title': title, 'image': image, 'url': url, 'action': 'play', 'isFolder': 'False'}

            if fanart:
                data.update({'fanart': fanart})

            self.list.append(data)

        directory.add(self.list)

    def play(self, url):

        if '.mp4' in url or '.m3u8' in url:

            stream = url

        else:

            html = client.request(url)

            stream = re.search("video/mp4.+?'(.+?)'", html, re.S).group(1)

        try:
            addon_enabled = control.addon_details('inputstream.adaptive').get('enabled')
        except KeyError:
            addon_enabled = False

        dash = '.m3u8' in url and control.kodi_version() >= 18.0 and addon_enabled and control.setting('hls_dash') == 'true'

        if dash:
            directory.resolve(stream, dash=dash, mimetype='application/vnd.apple.mpegurl', manifest_type='hls')
        else:
            directory.resolve(stream)

    def _webtv(self):

        html = client.request(self.webtv_link)

        web_tv_nav = client.parseDOM(html, 'ul', attrs={'class': 'menu menu--web-tv nav'})[0]

        items = client.parseDOM(web_tv_nav, 'li')[1:]

        for item in items:

            title = client.parseDOM(item, 'a')[0]
            url = client.parseDOM(item, 'a', ret='href')[0]
            url = ''.join([self.base_link, url])

            self.list.append({'title': title, 'url': url})

        return self.list

    def webtv(self):

        self.list = cache.get(self._webtv, 24)

        if self.list is None:
            return

        for i in self.list:
            i.update({'action': 'videos'})

        directory.add(self.list)
