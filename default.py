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
import os
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import util
import xbmcprovider
import xbmcutil
import resolver
import utmain
from provider import ResolveException

__scriptid__ = 'plugin.video.mojevideo.sk'
__scriptname__ = 'mojevideo.sk'
__addon__ = xbmcaddon.Addon(id=__scriptid__)
__language__ = __addon__.getLocalizedString
__settings__ = __addon__.getSetting

sys.path.append(os.path.join(__addon__.getAddonInfo('path'), 'resources', 'lib'))
import mojevideo
settings = {'downloads': __addon__.getSetting('downloads'), 'quality': __addon__.getSetting('quality')}


def vp8_youtube_filter(stream):
    # some embedded devices running xbmc doesnt have vp8 support, so we
    # provide filtering ability for youtube videos
    # ======================================================================
    #     5: "240p h263 flv container",
    #      18: "360p h264 mp4 container | 270 for rtmpe?",
    #      22: "720p h264 mp4 container",
    #      26: "???",
    #      33: "???",
    #      34: "360p h264 flv container",
    #      35: "480p h264 flv container",
    #      37: "1080p h264 mp4 container",
    #      38: "720p vp8 webm container",
    #      43: "360p h264 flv container",
    #      44: "480p vp8 webm container",
    #      45: "720p vp8 webm container",
    #      46: "520p vp8 webm stereo",
    #      59: "480 for rtmpe",
    #      78: "seems to be around 400 for rtmpe",
    #      82: "360p h264 stereo",
    #      83: "240p h264 stereo",
    #      84: "720p h264 stereo",
    #      85: "520p h264 stereo",
    #      100: "360p vp8 webm stereo",
    #      101: "480p vp8 webm stereo",
    #      102: "720p vp8 webm stereo",
    #      120: "hd720",
    #      121: "hd1080"
    # ======================================================================
    try:
        if stream['fmt'] in [38, 44, 45, 46, 100, 101, 102]:
            return True
    except KeyError:
        return False
    return False


class MojevideoXBMCContentProvider(xbmcprovider.XBMCMultiResolverContentProvider):
    def play(self, item):
        stream = self.resolve(item['url'])[0]
        if stream:
            xbmcutil.reportUsage(self.addon_id, self.addon_id + '/play')
            if 'headers' in list(stream.keys()):
                for header in stream['headers']:
                    stream['url'] += '|%s=%s' % (header, stream['headers'][header])
            print('Sending %s to player' % stream['url'])
            li = xbmcgui.ListItem(path=stream['url'])

            sub = False
            if xbmcaddon.Addon('xbmc.addon').getAddonInfo('version') > "16":
                sub = True
                if stream['subs'] is not None and stream['subs'] != '':
                    li.setSubtitles([stream['subs']])

            xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, li)
            if not sub:
                xbmcutil.load_subtitles(stream['subs'])

    def resolve(self, url):
        item = self.provider.video_item()
        item.update({'url': url})

        host = 'mojevideo.sk'
        tc = 'UA-110229735-1'
        try:
            utmain.main({'id': __scriptid__, 'host': host, 'tc': tc, 'action': url})
        except:
            pass

        try:
            return self.provider.resolve(item)
        except ResolveException as e:
            self._handle_exc(e)

xbmcplugin.setContent(int(sys.argv[1]), 'movies')

params = util.params()
if params == {}:
    xbmcutil.init_usage_reporting(__scriptid__)
MojevideoXBMCContentProvider(mojevideo.MojevideoContentProvider(tmp_dir=xbmc.translatePath(__addon__.getAddonInfo('profile'))), settings, __addon__).run(params)
