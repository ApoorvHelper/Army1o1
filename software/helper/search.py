import os
import re
from typing import Any

from software.sieve import Filter, get_first_link
from software.request import getting_qry
from bs4 import BeautifulSoup as bsoup
from cryptography.fernet import Fernet, InvalidToken
from flask import g

TOR_BANNER = '<hr><h1 style="text-align: center">You are using Tor</h1><hr>'
CAPTCHA = 'div class="g-recaptcha"'


def requiressl(url: str) -> bool:
    https_only = bool(os.getenv('HTTPS_ONLY', 0))
    is_http = url.startswith('http://')

    return (is_http) or (https_only and is_http)


def has_captcha(results: str) -> bool:
    return CAPTCHA in results


class Search:
    def __init__(self, request, config, session_key, cookies_disabled=False):
        method = request.method
        self.request_params = request.args if method == 'GET' else request.form
        self.user_agent = request.headers.get('User-Agent')
        self.feeling_lucky = False
        self.config = config
        self.session_key = session_key
        self.query = ''
        self.cookies_disabled = cookies_disabled
        self.search_type = self.request_params.get(
            'tbm') if 'tbm' in self.request_params else ''

    def __getitem__(self, name) -> Any:
        return getattr(self, name)

    def __setitem__(self, name, value) -> None:
        return setattr(self, name, value)

    def __delitem__(self, name) -> None:
        return delattr(self, name)

    def __contains__(self, name) -> bool:
        return hasattr(self, name)

    def new_search_query(self) -> str:
        q = self.request_params.get('q')

        if q is None or len(q) == 0:
            return ''
        else:
            try:
                q = Fernet(self.session_key).decrypt(q.encode()).decode()
            except InvalidToken:
                pass
        self.feeling_lucky = q.startswith('! ')
        self.query = q[2:] if self.feeling_lucky else q
        return self.query

    def generate_response(self) -> str:
        mobile = 'Android' in self.user_agent or 'iPhone' in self.user_agent

        content_filter = Filter(self.session_key,
                                mobile=mobile,
                                config=self.config)
        full_query = getting_qry(self.query,
                               self.request_params,
                               self.config)
        dis_photo = ('tbm=isch' in full_query
                      and self.config.dis_photo
                      and not g.user_request.mobile)

        get_body = g.user_request.send(query=full_query,
                                       force_mobile=dis_photo)
        html_soup = bsoup(get_body.text, 'html.parser')
        if dis_photo:
            html_soup = content_filter.dis_photo(html_soup)

        if self.feeling_lucky:
            return get_first_link(html_soup)
        else:
            formatted_results = content_filter.clean(html_soup)
            param_str = ''.join('&{}={}'.format(k, v)
                                for k, v in
                                self.request_params.to_dict(flat=True).items()
                                if self.config.is_safe_key(k))
            for link in formatted_results.find_all('a', href=True):
                if 'search?' not in link['href'] or link['href'].index(
                        'search?') > 1:
                    continue
                link['href'] += param_str

            return str(formatted_results)

    def check_kw_ip(self) -> re.Match:
        return re.search("([^a-z0-9]|^)my *[^a-z0-9] *(ip|internet protocol)" +
                         "($|( *[^a-z0-9] *(((addres|address|adres|" +
                         "adress)|a)? *$)))", self.query.lower())
