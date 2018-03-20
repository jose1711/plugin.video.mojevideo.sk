# -*- coding: UTF-8 -*-
# /*
# *
# *  This Program is free software; you can redistribute it and/or modify
# *  it under the terms of the GNU General Public License as published by
# *  the Free Software Foundation; either version 2, or (at your option)
# *  any later version.
# *
# *  This Program is distributed in the hope that it will be useful,
# *  but WITHOUT ANY WARRANTY; without even the implied warranty of
# *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# *  GNU General Public License for more details.
# *
# *  You should have received a copy of the GNU General Public License
# *  along with this program; see the file COPYING.  If not, write to
# *  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
# *  http://www.gnu.org/copyleft/gpl.html
# *
# */

import re
import urllib
import urllib2
import cookielib
import xbmcaddon
from xml.etree.ElementTree import fromstring
from demjson import demjson

import util
import resolver
from provider import ResolveException
from provider import ContentProvider


__addon__ = xbmcaddon.Addon()


class MojevideoContentProvider(ContentProvider):
    def __init__(self, username=None, password=None, filter=None,
                 tmp_dir='/tmp'):
        ContentProvider.__init__(self, 'mojevideo.sk',
                                 'http://www.mojevideo.sk',
                                 username, password, filter, tmp_dir)
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookielib.LWPCookieJar()))
        urllib2.install_opener(opener)

    def capabilities(self):
        return ['categories', 'resolve', 'search']

    def list(self, url):
        print('xxx url: %s' % url)
        if url.find("#related#") == 0:
            return self.list_related(util.request(self._url(url[9:])))
        elif url.find("#newest#") == 0:
            return self.list_newest(util.request(self._url(url[8:])))
        elif "srch/" in url:
            return self.list_searchresults(util.request(self._url(url)))
        else:
            return self.list_content(util.request(self._url(url)), self._url(url))

    def search(self, keyword):
        return self.list_searchresults(util.request(self._url('/srch/' + urllib.quote(keyword))))

    def list_searchresults(self, page, url=None):
        result = []
        if not url:
            url = self.base_url
        data = util.substr(page, '<ul id="search_', '<div id="nv">')
        pattern = '<a href="(?P<url>/video/[^"]+)" title="(?P<title>[^"]+)".*?<img src="(?P<img>[^"]+?)"(?P<id>.*?)<span>(?P<duration>[^<]+)</span>.*?</div>.*?<p class="c">(?P<plot>[^<]+)<'
        for m in re.finditer(pattern, data, re.IGNORECASE | re.DOTALL):
            over18 = __addon__.getSetting('over18')
            if 'id="im' in m.group('id') and not (over18 == 'true'):
                continue
            item = self.video_item()
            item['title'] = m.group('title')
            item['img'] = 'http://' + m.group('img')
            item['url'] = m.group('url')
            item['duration'] = self.mmss_to_seconds(m.group('duration'))
            item['plot'] = m.group('plot')
            item['menu'] = {'$30060': {'list': '#related#' + item['url'],
                                       'action-type': 'list'}}
            self._filter(result, item)

        data = util.substr(page, '<div id="nv">', '<div class="r">')
        n = re.search('<a href="(?P<url>[^"]+)"[^>]+>ďalej', page)
        if n:
            item = self.dir_item()
            item['type'] = 'next'
            item['url'] = n.group('url')
            result.append(item)
        n = re.search('<a href="(?P<url>[^"]+)"[^>]+>späť', page)
        if n:
            item = self.dir_item()
            item['type'] = 'prev'
            item['url'] = n.group('url')
            result.append(item)
        return result

    def categories(self):
        result = []
        item = self.dir_item()
        item['type'] = 'new'
        item['url'] = '#newest#'
        result.append(item)

        data = util.request(self.base_url + '/kategorie/')
        data = util.substr(data, '<ul id="cat"', '</div>')
        pattern = '<a href="(?P<url>[^"]+)" title="(?P<name>[^"]+)">'
        for m in re.finditer(pattern, data, re.IGNORECASE | re.DOTALL):
            if m.group('url') == '#':
                break
            item = self.dir_item()
            item['title'] = m.group('name')
            item['url'] = m.group('url')
            result.append(item)
        over18 = __addon__.getSetting('over18')
        if (over18 == 'true'):
            item = self.dir_item()
            item['title'] = 'erotika'
            item['url'] = self.base_url + '/erotika'
            result.append(item)
        return result

    def list_content(self, page, url=None):
        result = []
        if not url:
            url = self.base_url
        data = util.substr(page, '<div id="cntnt">', '<div id="fc">')
        pattern = '<a href="(?P<url>/video/[^"]+)"[^<]*<img src="(?P<img>[^"]+)" alt="(?P<title>[^"]+)".*?<div>(?P<duration>[^<]+)<'
        for m in re.finditer(pattern, data, re.IGNORECASE | re.DOTALL):
            item = self.video_item()
            item['title'] = m.group('title')
            item['img'] = 'http://' + m.group('img')
            item['url'] = m.group('url')
            item['duration'] = self.mmss_to_seconds(m.group('duration'))
            item['menu'] = {'$30060': {'list': '#related#' + item['url'],
                                       'action-type': 'list'}}
            self._filter(result, item)

        n = re.search('<a href="(?P<url>[^"]+)"[^>]+>Ďalej', page)
        if n:
            item = self.dir_item()
            item['type'] = 'next'
            item['url'] = n.group('url')
            result.append(item)
        n = re.search('<a href="(?P<url>[^"]+)">Späť', page)
        if n:
            item = self.dir_item()
            item['type'] = 'prev'
            item['url'] = n.group('url')
            result.append(item)

        return result

    def mmss_to_seconds(self, mmss):
        minutes, seconds = [int(x) for x in mmss.split(':')]
        return (minutes * 60 + seconds)

    def list_newest(self, page, url=None):
        result = []
        if not url:
            url = self.base_url
        data = util.substr(page, '<ul id="browsing_main">', '<div id="fc">')
        pattern = '<a href="(?P<url>/video/[^"]+)" title="(?P<title>[^"]+)".*?<img src="(?P<img>[^"]+?)"(?P<id>.*?)<span>(?P<duration>[^<]+)</span>.*?</div>.*?<p class="c">(?P<plot>[^<]+)<'
        for m in re.finditer(pattern, data, re.IGNORECASE | re.DOTALL):
            item = self.video_item()
            over18 = __addon__.getSetting('over18')
            if 'id="im' in m.group('id') and not (over18 == 'true'):
                continue
            item['title'] = m.group('title')
            item['img'] = 'http://' + m.group('img')
            item['url'] = m.group('url')
            item['plot'] = m.group('plot')
            item['duration'] = self.mmss_to_seconds(m.group('duration'))
            item['menu'] = {'$30060': {'list': '#related#' + item['url'],
                                       'action-type': 'list'}}
            self._filter(result, item)

        n = re.search('<a href="(?P<url>[^"]+)"[^>]+>Ďalej', page)
        if n:
            item = self.dir_item()
            item['type'] = 'next'
            item['url'] = n.group('url')
            result.append(item)
        n = re.search('<a href="(?P<url>[^"]+)">Späť', page)
        if n:
            item = self.dir_item()
            item['type'] = 'prev'
            item['url'] = n.group('url')
            result.append(item)

        k = re.search('<a href="(?P<url>[^"]+)" title="nasledujúca strana" rel="next"', page)
        n = re.search('<a href="(?P<url>[^"]+)" title="predošlá strana" rel="prev"', page)
        if k:
            item = self.dir_item()
            item['type'] = 'next'
            item['url'] = '#newest#' + k.group('url')
            result.append(item)
        if n:
            item = self.dir_item()
            item['type'] = 'prev'
            if n.group('url') in '//www.mojevideo.sk/':
                item['url'] = '#newest#'
            else:
                item['url'] = '#newest#' + n.group('url')
            result.append(item)
        return result

    def list_related(self, page):
        result = []
        data = util.substr(page,
                           '<div id="video_sim">',
                           '</div')
        pattern = '<a href="(?P<url>[^"]+)"[^<]+<img src="(?P<img>[^"]+)" alt="(?P<title>[^"]+)"(?P<id> id="im0")?'
        for m in re.finditer(pattern, data, re.IGNORECASE | re.DOTALL):
            item = self.video_item()
            item['title'] = m.group('title')
            item['img'] = 'http://' + m.group('img')
            item['url'] = m.group('url')
            if m.group('id'):
                continue
            self._filter(result, item)
        return result

    def resolve(self, item, captcha_cb=None, select_cb=None):
        result = []
        resolved = []
        item = item.copy()
        url = self._url(item['url'])
        data = util.request(url)
        print('data start ----')
        print(data)
        print('data end ----')

        vid = re.search('vId=([0-9]+)', data).group(1)
        video_url = 'https://cache01.mojevideo.sk/securevideos69/'
        quality = int(re.search('vVq=([0-9]+)', data).group(1))
        video_url += vid
        quality_string = ['_lq', '', '_hd']
        if quality > 0:
            selected_quality = int(__addon__.getSetting('quality'))
            resulting_quality = min(selected_quality, quality)
            qstring = quality_string[resulting_quality]
            video_url += '{0}.mp4'.format(qstring)

        else:
            video_url += '.mp4'

        resolved += video_url[:]

        item = self.video_item()
        item['url'] = video_url
        item['quality'] = 'ukn'
        item['surl'] = video_url
        result.append(item)
        return result
