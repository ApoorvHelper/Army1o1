from software.models.config import Config
from software.models.endpoint import Endpoint
from software.request import VALID_PARAMS, MAPS_URL
from software.helper.misc import read_config_bool
from software.helper.results import *
from bs4 import BeautifulSoup
from bs4.element import ResultSet, Tag
from cryptography.fernet import Fernet
from flask import render_template
import re
import urllib.parse as urlparse
from urllib.parse import parse_qs
import os


def extract_q(q_str: str, href: str) -> str:
    return parse_qs(q_str)['q'][0] if ('&q=' in href or '?q=' in href) else ''


def q_cln(query: str) -> str:
    return query[:query.find('-site:')] if '-site:' in query else query


class Filter:
    RESULT_CHILD_LIMIT = 7

    def __init__(self, user_key: str, config: Config, mobile=False) -> None:
        self.config = config
        self.mobile = mobile
        self.user_key = user_key
        self.main_divs = ResultSet('')
        self._elements = 0

    def __getitem__(self, name):
        return getattr(self, name)

    @property
    def elements(self):
        return self._elements

    def encrypt_path(self, path, is_element=False) -> str:
        if is_element:
            enc_path = Fernet(self.user_key).encrypt(path.encode()).decode()
            self._elements += 1
            return enc_path

        return Fernet(self.user_key).encrypt(path.encode()).decode()

    def clean(self, soup) -> BeautifulSoup:
        self.main_divs = soup.find('div', {'id': 'main'})
        self.remove_ads()
        self.topic_remover()
        self.de_webs()
        self.collide()
        self.mystylemyswag(soup)

        for img in [_ for _ in soup.find_all('img') if 'src' in _.attrs]:
            self.elem_updater(img, 'image/png')

        for audio in [_ for _ in soup.find_all('audio') if 'src' in _.attrs]:
            self.elem_updater(audio, 'audio/mpeg')

        for link in soup.find_all('a', href=True):
            self.site_stare(link)

        input_form = soup.find('form')
        if input_form is not None:
            input_form['method'] = 'GET' if self.config.get_only else 'POST'
        for script in soup('script'):
            script.decompose()
        footer = soup.find('footer')
        if footer:
            [_.decompose() for _ in footer.find_all('div', recursive=False)
             if len(_.find_all('a', href=True)) > 3]

        header = soup.find('header')
        if header:
            header.decompose()

        return soup

    def remove_ads(self) -> None:
        if not self.main_divs:
            return

        for div in [_ for _ in self.main_divs.find_all('div', recursive=True)]:
            div_ads = [_ for _ in div.find_all('span', recursive=True)
                       if has_ad_content(_.text)]
            _ = div.decompose() if len(div_ads) else None

    def topic_remover(self) -> None:
        if not self.main_divs or not self.config.block_title:
            return
        block_title = re.compile(self.block_title)
        for div in [_ for _ in self.main_divs.find_all('div', recursive=True)]:
            block_divs = [_ for _ in div.find_all('h3', recursive=True)
                          if block_title.search(_.text) is not None]
            _ = div.decompose() if len(block_divs) else None

    def de_webs(self) -> None:
        if not self.main_divs or not self.config.block_url:
            return
        block_url = re.compile(self.block_url)
        for div in [_ for _ in self.main_divs.find_all('div', recursive=True)]:
            block_divs = [_ for _ in div.find_all('a', recursive=True)
                          if block_url.search(_.attrs['href']) is not None]
            _ = div.decompose() if len(block_divs) else None

    def collide(self) -> None:
        minimal_mode = read_config_bool('ARMY1O1_MINIMAL')

        def ch_div(result_div: BeautifulSoup):
            try:
                return result_div.findChildren(
                    'div', recursive=False
                )[0].findChildren(
                    'div', recursive=False)
            except IndexError:
                return []

        if not self.main_divs:
            return
        for result in self.main_divs:
            result_children = ch_div(result)
            if minimal_mode:
                if len(result_children) in (1, 3):
                    continue
            else:
                if len(result_children) < self.RESULT_CHILD_LIMIT:
                    continue
            label = 'Collapsed Results'
            for elem in result_children:
                if elem.text:
                    label = elem.text
                    elem.decompose()
                    break
            parent = None
            idx = 0
            while not parent and idx < len(result_children):
                parent = result_children[idx].parent
                idx += 1

            details = BeautifulSoup(features='html.parser').new_tag('details')
            summary = BeautifulSoup(features='html.parser').new_tag('summary')
            summary.string = label
            details.append(summary)

            if parent and not minimal_mode:
                parent.wrap(details)
            elif parent and minimal_mode:
                parent.decompose()

    def elem_updater(self, element: Tag, mime: str) -> None:
        src = element['src']

        if src.startswith('//'):
            src = 'https:' + src

        if src.startswith(LOGO_URL):
            element.replace_with(BeautifulSoup(
                render_template('logo.html'),
                features='html.parser'))
            return
        elif src.startswith(GOOG_IMG) or GOOG_STATIC in src:
            element['src'] = BLANK_B64
            return

        element['src'] = f'{Endpoint.element}?url=' + self.encrypt_path(
            src,
            is_element=True) + '&type=' + urlparse.quote(mime)

    def mystylemyswag(self, soup) -> None:
        for button in soup.find_all('button'):
            button.decompose()
        for svg in soup.find_all('svg'):
            svg.decompose()
        logo = soup.find('a', {'class': 'l'})
        if logo and self.mobile:
            logo['style'] = ('display:flex; justify-content:center; '
                             'align-items:center; color:#685e79; '
                             'font-size:18px; ')

        try:
            search_bar = soup.find('header').find('form').find('div')
            search_bar['style'] = 'width: 100%;'
        except AttributeError:
            pass

    def site_stare(self, link: Tag) -> None:
        href = link['href'].replace('https://www.google.com', '')
        if 'advanced_search' in href or 'tbm=shop' in href:
            link.decompose()
            return

        result_link = urlparse.urlparse(href)
        q = extract_q(result_link.query, href)

        if q.startswith('/'):
            link['href'] = 'https://google.com' + q
        elif '/search?q=' in href:
            if 'li:1' in href:
                q = '"' + q + '"'
            new_search = 'search?q=' + self.encrypt_path(q)

            query_params = parse_qs(urlparse.urlparse(href).query)
            for param in VALID_PARAMS:
                if param not in query_params:
                    continue
                param_val = query_params[param][0]
                new_search += '&' + param + '=' + param_val
            link['href'] = new_search
        elif 'url?q=' in href:
            link['href'] = filter_link_args(q)
            if self.config.nojs:
                softwareend_nojs(link)

            if self.config.new_tab:
                link['target'] = '_blank'
        else:
            if href.startswith(MAPS_URL):
                link['href'] = MAPS_URL + "?q=" + q_cln(q)
            else:
                link['href'] = href

        if self.config.alts:
            link['href'] = get_site_alt(link['href'])
            link_desc = link.find_all(
                text=re.compile('|'.join(SITE_ALTS.keys())))
            if len(link_desc) == 0:
                return

            link_desc = link_desc[0]
            for site, alt in SITE_ALTS.items():
                if site not in link_desc:
                    continue
                new_desc = BeautifulSoup(features='html.parser').new_tag('div')
                new_desc.string = str(link_desc).replace(site, alt)
                link_desc.replace_with(new_desc)
                break

    def dis_photo(self, soup) -> BeautifulSoup:
        search_input = soup.find_all('td', attrs={'class': "O4cRJf"})[0]
        cor_suggested = soup.find_all('table', attrs={'class': "By0U9"})
        next_pages = soup.find_all('table', attrs={'class': "uZgmoc"})[0]
        information = soup.find_all('div', attrs={'class': "TuS8Ad"})[0]

        results = []
        results_div = soup.find_all('div', attrs={'class': "nQvrDb"})[0]
        results_all = results_div.find_all('div', attrs={'class': "lIMUZd"})

        for item in results_all:
            urls = item.find('a')['href'].split('&imgrefurl=')

            if len(urls) != 2:
                continue

            img_url = urlparse.unquote(urls[0].replace(
                f'/{Endpoint.imgres}?imgurl=', ''))

            try:
                web_page = urlparse.unquote(urls[1].split('&')[0])
            except IndexError:
                web_page = urlparse.unquote(urls[1])

            img_tbn = urlparse.unquote(item.find('a').find('img')['src'])

            results.softwareend({
                'domain': urlparse.urlparse(web_page).netloc,
                'img_url': img_url,
                'web_page': web_page,
                'img_tbn': img_tbn
            })

        soup = BeautifulSoup(render_template('imageresults.html',
                                             length=len(results),
                                             results=results,
                                             view_label="View Image"),
                             features='html.parser')
        soup.find_all('td',
                      attrs={'class': "O4cRJf"})[0].replaceWith(search_input)
        if len(cor_suggested):
            soup.find_all(
                'table',
                attrs={'class': "By0U9"}
            )[0].replaceWith(cor_suggested[0])

        soup.find_all('table',
                      attrs={'class': "uZgmoc"})[0].replaceWith(next_pages)

        soup.find_all('div',
                      attrs={'class': "TuS8Ad"})[0].replaceWith(information)
        return soup
