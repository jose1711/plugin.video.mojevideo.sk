# -*- coding: UTF-8 -*-
# /*
# *      Copyright (C) 2017 BrozikCZ
# *
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
from xml.etree.ElementTree import fromstring
from demjson import demjson

import util
import resolver
from provider import ResolveException
from provider import ContentProvider


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
        if url.find("#related#") == 0:
            return self.list_related(util.request(self._url(url[9:])))
        elif url.find("#newest#") == 0:
            return self.list_newest(util.request(self._url(url[8:])))
        else:
            return self.list_content(util.request(self._url(url)), self._url(url))

    def search(self, keyword):
        return self.list_searchresults(util.request(self._url('/srch/' + urllib.quote(keyword))))

    def list_searchresults(self, page, url=None):
        result = []
        if not url:
            url = self.base_url
        data = util.substr(page, '<ul id="search_main">', '<div id="nv">')
        pattern = '<a href="(?P<url>/video/[^"]+)" title="(?P<title>[^"]+)".*?<img src="(?P<img>[^"]+)"'
        for m in re.finditer(pattern, data, re.IGNORECASE | re.DOTALL):
            item = self.video_item()
            item['title'] = m.group('title')
            item['img'] = 'http://' + m.group('img')
            item['url'] = m.group('url')
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
        return result

    def list_content(self, page, url=None):
        result = []
        if not url:
            url = self.base_url
        data = util.substr(page, '<div id="cntnt">', '<div id="fc">')
        pattern = '<a href="(?P<url>/video/[^"]+)"[^<]*<img src="(?P<img>[^"]+)" alt="(?P<title>[^"]+)"'
        for m in re.finditer(pattern, data, re.IGNORECASE | re.DOTALL):
            item = self.video_item()
            item['title'] = m.group('title')
            item['img'] = 'http://' + m.group('img')
            item['url'] = m.group('url')
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

        data = util.substr(page, '<ul class=\"easy-wp-page-nav', '</div>')
        n = re.search('<li><a class=\"prev page-numbers\" href=\"(?P<url>[^\"]+)\"', data)
        k = re.search('<li><a class=\"next page-numbers\" href=\"(?P<url>[^\"]+)\"', data)
        if n is not None:
            item = self.dir_item()
            item['type'] = 'prev'
            item['url'] = n.group('url')
            result.append(item)
        if k is not None:
            item = self.dir_item()
            item['type'] = 'next'
            item['url'] = k.group('url')
            result.append(item)
        return result

    def list_newest(self, page, url=None):
        result = []
        if not url:
            url = self.base_url
        data = util.substr(page, '<ul id="browsing_main">', '<div id="fc">')
        pattern = '<a href="(?P<url>/video/[^"]+)" title="(?P<title>[^"]+)".*?<img src="(?P<img>[^"]+)"'
        for m in re.finditer(pattern, data, re.IGNORECASE | re.DOTALL):
            item = self.video_item()
            item['title'] = m.group('title')
            item['img'] = 'http://' + m.group('img')
            item['url'] = m.group('url')
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

        data = util.substr(page, '<ul class=\"easy-wp-page-nav', '</div>')
        n = re.search('<li><a class=\"prev page-numbers\" href=\"(?P<url>[^\"]+)\"', data)
        k = re.search('<li><a class=\"next page-numbers\" href=\"(?P<url>[^\"]+)\"', data)
        if n is not None:
            item = self.dir_item()
            item['type'] = 'prev'
            item['url'] = n.group('url')
            result.append(item)
        if k is not None:
            item = self.dir_item()
            item['type'] = 'next'
            item['url'] = k.group('url')
            result.append(item)
        return result

    def list_related(self, page):
        result = []
        data = util.substr(page,
                           '<div id="video_sim">',
                           '</div')
        pattern = '<a href="(?P<url>[^"]+)"[^<]+<img src="(?P<img>[^"]+)" alt="(?P<title>[^"]+)"'
        for m in re.finditer(pattern, data, re.IGNORECASE | re.DOTALL):
            item = self.video_item()
            item['title'] = m.group('title')
            item['img'] = 'http://' + m.group('img')
            item['url'] = m.group('url')
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
        video_url += vid
        video_url += '.mp4'

        resolved += video_url[:]

        item = self.video_item()
        item['url'] = video_url
        item['quality'] = 'ukn'
        item['surl'] = video_url
        result.append(item)
        return result
