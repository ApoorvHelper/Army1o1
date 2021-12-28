from software.models.config import Config
from datetime import datetime
import xml.etree.ElementTree as ET
import random
import requests
from requests import Response, ConnectionError
import urllib.parse as urlparse
import os
from stem import Signal, SocketError
from stem.control import Controller

MAPS_URL = 'https://maps.google.com/maps'
AUTOCOMPLETE_URL = ('https://suggestqueries.google.com/'
                    'complete/search?client=toolbar&')

MOBILE_UA = '{}/5.0 (Android 0; Mobile; rv:54.0) Gecko/54.0 {}/59.0'
DESKTOP_UA = '{}/5.0 (X11; {} x86_64; rv:75.0) Gecko/20100101 {}/75.0'

VALID_PARAMS = ['tbs', 'tbm', 'start', 'near', 'source', 'nfpr']


def getting_usr_agnt(is_mobile) -> str:
    firefox = random.choice(['Choir', 'Squier', 'Higher', 'Wire']) + 'fox'
    linux = random.choice(['Win', 'Sin', 'Gin', 'Fin', 'Kin']) + 'ux'

    if is_mobile:
        return MOBILE_UA.format("Mozilla", firefox)

    return DESKTOP_UA.format("Mozilla", linux, firefox)


def getting_qry(query, args, config) -> str:
    param_dict = {key: '' for key in VALID_PARAMS}
    lang = ''
    if ':past' in query and 'tbs' not in args:
        time_range = str.strip(query.split(':past', 1)[-1])
        param_dict['tbs'] = '&tbs=' + ('qdr:' + str.lower(time_range[0]))
    elif 'tbs' in args:
        result_tbs = args.get('tbs')
        param_dict['tbs'] = '&tbs=' + result_tbs

        result_params = [_ for _ in result_tbs.split(',') if 'lr:' in _]
        if len(result_params) > 0:
            result_param = result_params[0]
            lang = result_param[result_param.find('lr:') + 3:len(result_param)]
    query = urlparse.quote(query)

    if 'tbm' in args:
        param_dict['tbm'] = '&tbm=' + args.get('tbm')

    if 'start' in args:
        param_dict['start'] = '&start=' + args.get('start')

    if config.near:
        param_dict['near'] = '&near=' + urlparse.quote(config.near)

    if 'source' in args:
        param_dict['source'] = '&source=' + args.get('source')
        param_dict['lr'] = ('&lr=' + ''.join(
            [_ for _ in lang if not _.isdigit()]
        )) if lang else ''
    else:
        param_dict['lr'] = '&lr=' + (
            config.lang_search if config.lang_search else ''
        )

    if 'nfpr' in args:
        param_dict['nfpr'] = '&nfpr=' + args.get('nfpr')

    if 'chips' in args:
        param_dict['chips'] = '&chips=' + args.get('chips')

    param_dict['gl'] = ('&gl=' + config.country) if config.country else ''
    param_dict['hl'] = '&hl=' + (
        config.lang_interface.replace('lang_', '')
        if config.lang_interface else ''
    )
    param_dict['safe'] = '&safe=' + ('active' if config.safe else 'off')
    unquoted_query = urlparse.unquote(query)
    for blocked_site in config.block.replace(' ', '').split(','):
        if not blocked_site:
            continue
        block = (' -site:' + blocked_site)
        query += block if block not in unquoted_query else ''

    for val in param_dict.values():
        if not val:
            continue
        query += val

    return query


class Request:
    def __init__(self, normal_ua, root_path, config: Config):
        self.gatheringlink = 'https://www.google.com/search?gbv=1&num=' + str(
            os.getenv('ARMY1O1_RESULTS_PER_PAGE', 10)) + '&q='

        

        self.language = (
            config.lang_search if config.lang_search else ''
        )

        self.lang_interface = ''
        if config.accept_language:
            self.lang_interface = config.lang_interface

        self.mobile = bool(normal_ua) and ('Android' in normal_ua
                                           or 'iPhone' in normal_ua)
        self.modified_user_agent = getting_usr_agnt(self.mobile)
        if not self.mobile:
            self.modified_user_agent_mobile = getting_usr_agnt(True)


        self.root_path = root_path

    def __getitem__(self, name):
        return getattr(self, name)

    def autocomplete(self, query) -> list:
        ac_query = dict(hl=self.language, q=query)
        response = self.send(base_url=AUTOCOMPLETE_URL,
                             query=urlparse.urlencode(ac_query)).text

        if not response:
            return []

        root = ET.fromstring(response)
        return [_.attrib['data'] for _ in
                root.findall('.//suggestion/[@data]')]

    def send(self, base_url='', query='', attempt=0,
             force_mobile=False) -> Response:
        if force_mobile and not self.mobile:
            modified_user_agent = self.modified_user_agent_mobile
        else:
            modified_user_agent = self.modified_user_agent

        headers = {
            'User-Agent': modified_user_agent
        }

        if self.lang_interface:
            headers.update({'Accept-Language':
                            self.lang_interface.replace('lang_', '')
                            + ';q=1.0'})
        now = datetime.now()
        cookies = {
            'CONSENT': 'YES+cb.{:d}{:02d}{:02d}-17-p0.de+F+678'.format(
                now.year, now.month, now.day
            )
        }

        response = requests.get(
            (base_url or self.gatheringlink) + query,
            
            headers=headers,
            cookies=cookies)
       

        return response
