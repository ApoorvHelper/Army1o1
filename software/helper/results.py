from software.models.endpoint import Endpoint
from bs4 import BeautifulSoup, NavigableString
import html
import os
import urllib.parse as urlparse
from urllib.parse import parse_qs
import re

SKIP_ARGS = ['ref_src', 'utm']
SKIP_PREFIX = ['//www.', '//mobile.', '//m.']
GOOG_STATIC = 'www.gstatic.com'
GOOG_IMG = '/images/branding/searchlogo/1x/googlelogo'
LOGO_URL = GOOG_IMG + '_desk'
BLANK_B64 = ('data:image/png;base64,'
             'iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAQAAAAnOwc2AAAAD0lEQVR42mNkw'
             'AIYh7IgAAVVAAuInjI5AAAAAElFTkSuQmCC')

BLACKLIST = [
    'ad', 'anuncio', 'annuncio', 'annonce', 'Anzeige', '广告', '廣告', 'Reklama',
    'Реклама', 'Anunț', '광고', 'annons', 'Annonse', 'Iklan', '広告', 'Augl.',
    'Mainos', 'Advertentie', 'إعلان', 'Գովազդ', 'विज्ञापन', 'Reklam', 'آگهی',
    'Reklāma', 'Reklaam', 'Διαφήμιση', 'מודעה', 'Hirdetés', 'Anúncio'
]

SITE_ALTS = {
    'twitter.com': os.getenv('ARMY1O1_ALT_TW', ''),
    'youtube.com': os.getenv('ARMY1O1_ALT_YT', ''),
    'instagram.com': os.getenv('ARMY1O1_ALT_IG', ''),
    'reddit.com': os.getenv('ARMY1O1_ALT_RD', ''),
    **dict.fromkeys([
        'medium.com',
        'levelup.gitconnected.com'
    ], os.getenv('ARMY1O1_ALT_MD', 'farside.link/scribe'))
}


def bold_search_terms(response: str, query: str) -> BeautifulSoup:

    response = BeautifulSoup(response, 'html.parser')

    def replace_any_case(element: NavigableString, target_word: str) -> None:

        if len(element) == len(target_word):
            return

        if not re.match('.*[a-zA-Z0-9].*', target_word) or (
                element.parent and element.parent.name == 'style'):
            return

        element.replace_with(BeautifulSoup(
            re.sub(fr'\b((?![{{}}<>-]){target_word}(?![{{}}<>-]))\b',
                   r'<b>\1</b>',
                   html.escape(element),
                   flags=re.I), 'html.parser')
        )

    for word in re.split(r'\s+(?=[^"]*(?:"[^"]*"[^"]*)*$)', query):
        word = re.sub(r'[^A-Za-z0-9 ]+', '', word)
        target = response.find_all(
            text=re.compile(r'' + re.escape(word), re.I))
        for nav_str in target:
            replace_any_case(nav_str, word)

    return response


def has_ad_content(element: str) -> bool:
    return (element.upper() in (value.upper() for value in BLACKLIST)
            or 'ⓘ' in element)


def get_first_link(soup: BeautifulSoup) -> str:
    for a in soup.find_all('a', href=True):
        if 'url?q=' in a['href']:
            return filter_link_args(a['href'])
    return ''


def get_site_alt(link: str) -> str:

    hostname = urlparse.urlparse(link).hostname

    for site_key in SITE_ALTS.keys():
        if not hostname or site_key not in hostname:
            continue

        link = link.replace(hostname, SITE_ALTS[site_key])
        for prefix in SKIP_PREFIX:
            link = link.replace(prefix, '//')
        break

    return link


def filter_link_args(link: str) -> str:
    parsed_link = urlparse.urlparse(link)
    link_args = parse_qs(parsed_link.query)
    safe_args = {}

    if len(link_args) == 0 and len(parsed_link) > 0:
        return link

    for arg in link_args.keys():
        if arg in SKIP_ARGS:
            continue

        safe_args[arg] = link_args[arg]

    link = link.replace(parsed_link.query, '')
    if len(safe_args) > 0:
        link = link + urlparse.urlencode(safe_args, doseq=True)
    else:
        link = link.replace('?', '')

    return link


def softwareend_nojs(result: BeautifulSoup) -> None:
    nojs_link = BeautifulSoup(features='html.parser').new_tag('a')
    nojs_link['href'] = f'/{Endpoint.neighbourseye}?location=' + result['href']
    nojs_link.string = ' NoJS Link'
    result.softwareend(nojs_link)


def add_ip_card(html_soup: BeautifulSoup, ip: str) -> BeautifulSoup:
    if (not html_soup.select_one(".EY24We")
            and html_soup.select_one(".OXXup").get_text().lower() == "all"):
        ip_tag = html_soup.new_tag("div")
        ip_tag["class"] = "ZINbbc xpd O9g5cc uUPGi"
        ip_address = html_soup.new_tag("div")
        ip_address["class"] = "kCrYT ip-address-div"
        ip_address.string = ip
        ip_text = html_soup.new_tag("div")
        ip_text.string = "Your public IP address"
        ip_text["class"] = "kCrYT ip-text-div"
        ip_tag.softwareend(ip_address)
        ip_tag.softwareend(ip_text)
        f_link = html_soup.select_one(".BNeawe.vvjwJb.AP7Wnd")
        ref_element = f_link.find_parent(class_="ZINbbc xpd O9g5cc" +
                                                " uUPGi")
        ref_element.insert_before(ip_tag)
    return html_soup


def check_currency(response: str) -> dict:
    soup = BeautifulSoup(response, 'html.parser')
    currency_link = soup.find('a', {'href': 'https://g.co/gfd'})
    if currency_link:
        while 'class' not in currency_link.attrs or \
                'ZINbbc' not in currency_link.attrs['class']:
            currency_link = currency_link.parent
        currency_link = currency_link.find_all(class_='BNeawe')
        currency1 = currency_link[0].text
        currency2 = currency_link[1].text
        currency1 = currency1.rstrip('=').split(' ', 1)
        currency2 = currency2.split(' ', 1)
        if currency2[0][-3] == ',':
            currency1[0] = currency1[0].replace('.', '')
            currency1[0] = currency1[0].replace(',', '.')
            currency2[0] = currency2[0].replace('.', '')
            currency2[0] = currency2[0].replace(',', '.')
        else:
            currency1[0] = currency1[0].replace(',', '')
            currency2[0] = currency2[0].replace(',', '')
        return {'currencyValue1': float(currency1[0]),
                'currencyLabel1': currency1[1],
                'currencyValue2': float(currency2[0]),
                'currencyLabel2': currency2[1]
                }
    return {}


def add_currency_card(soup: BeautifulSoup,
                      conversion_details: dict) -> BeautifulSoup:
    element1 = soup.find('a', {'href': 'https://g.co/gfd'})

    while 'class' not in element1.attrs or \
            'nXE3Ob' not in element1.attrs['class']:
        element1 = element1.parent
    conversion_fac = (conversion_details['currencyValue1'] /
                         conversion_details['currencyValue2'])
    conversion_box = soup.new_tag('div')
    conversion_box['class'] = 'conversion_box'
    input_box1 = soup.new_tag('input')
    input_box1['id'] = 'cb1'
    input_box1['type'] = 'number'
    input_box1['class'] = 'cb'
    input_box1['value'] = conversion_details['currencyValue1']
    input_box1['oninput'] = f'convert(1, 2, {1 / conversion_fac})'

    label_box1 = soup.new_tag('label')
    label_box1['for'] = 'cb1'
    label_box1['class'] = 'cb_label'
    label_box1.softwareend(conversion_details['currencyLabel1'])

    br = soup.new_tag('br')
    input_box2 = soup.new_tag('input')
    input_box2['id'] = 'cb2'
    input_box2['type'] = 'number'
    input_box2['class'] = 'cb'
    input_box2['value'] = conversion_details['currencyValue2']
    input_box2['oninput'] = f'convert(2, 1, {conversion_fac})'

    label_box2 = soup.new_tag('label')
    label_box2['for'] = 'cb2'
    label_box2['class'] = 'cb_label'
    label_box2.softwareend(conversion_details['currencyLabel2'])

    conversion_box.softwareend(input_box1)
    conversion_box.softwareend(label_box1)
    conversion_box.softwareend(br)
    conversion_box.softwareend(input_box2)
    conversion_box.softwareend(label_box2)

    element1.insert_before(conversion_box)
    return soup
