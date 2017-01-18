from __future__ import unicode_literals

import time
from .jwplatform import JWPlatformBaseIE
from ..utils import (
    ExtractorError,
    sanitized_Request,
    urlencode_postdata,
)


class FetLifeIE(JWPlatformBaseIE):
    _VALID_URL = r'https?://fetlife\.com/users/[0-9]+/videos/(?P<id>[0-9]+)'
    _LOGIN_URL = 'https://fetlife.com/users/sign_in'
    _NETRC_MACHINE = 'fetlife'

    _TEST = {
        'url': 'https://fetlife.com/users/1537262/videos/660686',
        'md5': 'TODO: md5 sum of the first 10241 bytes of the video file (use --test)',
        'info_dict': {
            'id': '660686',
            'thumbnail': r'https://cap[0-9]\.fetlife\.com/thumbnails/660686/thumb_0000_345\.jpg\?token=[^\s]+',
            'timestamp': 1484020451,
            'ext': 'mp4',
            'title': 'Sully Savage and Violet Monroe ',
            'uploader': 'MissBratDom',
            'uploader_id': '1537262',
        },
    }

    def _real_initialize(self):
        (username, password) = self._get_login_info()
        if username is None:
            return
        webpage = self._download_webpage(self._LOGIN_URL, 'login')
        authenticity_token = self._search_regex(r'<input[^>]*?authenticity_token[^>]*?value=\"([^\"]*)\"[^>]/>', webpage, 'authenticity_token')

        login_form = {
            'utf8': '&#x2713;',
            'authenticity_token': authenticity_token,
            'user[otp_attempt]': 'step_1',
            'user[locale]': 'en',
            'user[login]': username,
            'user[password]': password,
        }

        request = sanitized_Request(self._LOGIN_URL, urlencode_postdata(login_form))
        request.add_header('Referer', self._LOGIN_URL)
        response = self._download_webpage(request, None, 'Logging in as %s' % username)

        login_error = self._html_search_regex(r'Login to FetLife', response, 'login error', default=None)
        if login_error:
            raise ExtractorError('Unable to login.', expected=True)

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        try:
            video_data = self._extract_jwplayer_data(webpage, video_id, require_title=False)
        except TypeError:
            raise ExtractorError('Unable to extract video data. Not a FetLife Supporter?', expected=True)

        title = self._search_regex(r'<section[^>]+id=\"video_caption\">[\s\S]+?<p[^>]+class=\"description\">([^<]+)', webpage, 'title')
        uploader = self._search_regex(r'<div[^>]+class=\"member-info\">[\s\S]+?<a[^>]+class=\"nickname\"[\s\S]+?>([^<]+)', webpage, 'uploader')
        uploader_id = self._search_regex(r'<div[^>]+class=\"member-info\">[\s\S]+?<a[^>]+href=\"/users/([0-9]+)', webpage, 'uploader')
        timestamp = int(time.mktime(time.strptime(self._search_regex(r'<section[^>]+id=\"video_caption\">[\s\S]+?<time[^>]+>([^<]+)', webpage, 'timestamp'), "%Y/%m/%d %H:%M:%S +0000")))

        video_data.update({
            'id': video_id,
            'title': title,
            'uploader': uploader,
            'timestamp': timestamp,
            'uploader_id': uploader_id,
            'age_limit': 18,
        })

        return video_data
