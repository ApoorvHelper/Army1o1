import argparse
import base64
import io
import json
import pickle
import urllib.parse as urlparse
import uuid
from datetime import timedelta
from functools import wraps

import waitress
from software import software
from software.models.config import Config
from software.models.endpoint import Endpoint
from software.request import Request
from software.helper.setr import resolve_bang
from software.helper.misc import read_config_bool, get_client_ip, get_request_url
from software.helper.results import add_ip_card, bold_search_terms,\
    add_currency_card, check_currency
from software.helper.search import *
from software.helper.session import human_code, valid_user_session
from bs4 import BeautifulSoup as bsoup
from flask import jsonify, make_response, request, redirect, render_template, \
    send_file, session, url_for
from requests import exceptions, get
from requests.models import PreparedRequest


bang_json = json.load(open(software.config['BANG_FILE']))




def need_login(f):
    @wraps(f)
    def beautified(*args, **kwargs):
        auth = request.authorization

        
        army1o1_user = os.getenv('ARMY1O1_USER', '')
        army1o1_pass = os.getenv('ARMY1O1_PASS', '')
        if (not army1o1_user or not army1o1_pass) or (
                auth
                and army1o1_user == auth.username
                and army1o1_pass == auth.password):
            return f(*args, **kwargs)
        else:
            return make_response('Not logged in', 401, {
                'WWW-Authenticate': 'Basic realm="Login Required"'})

    return beautified


def must_want(f):
    @wraps(f)
    def beautified(*args, **kwargs):
        if (valid_user_session(session) and
                'cookies_disabled' not in request.args):
            g.session_key = session['key']
        else:
            session.pop('_permanent', None)
            g.session_key = software.default_key

        
        invalid_sessions = []
        for user_session in os.listdir(software.config['SESSION_FILE_DIR']):
            session_path = os.path.join(
                software.config['SESSION_FILE_DIR'],
                user_session)
            try:
                with open(session_path, 'rb') as session_file:
                    _ = pickle.load(session_file)
                    data = pickle.load(session_file)
                    if isinstance(data, dict) and 'valid' in data:
                        continue
                    invalid_sessions.append(session_path)
            except (EOFError, FileNotFoundError):
                pass

        for invalid_session in invalid_sessions:
            os.remove(invalid_session)

        return f(*args, **kwargs)

    return beautified


@software.before_request
def predecessor_function():
    g.request_params = (
        request.args if request.method == 'GET' else request.form
    )    
    if '/session' in request.path and not valid_user_session(session):
        return

    default_config = json.load(open(software.config['DEFAULT_CONFIG'])) \
        if os.path.exists(software.config['DEFAULT_CONFIG']) else {}
    if (not valid_user_session(session) and
            'cookies_disabled' not in request.args):
        session['config'] = default_config
        session['uuid'] = str(uuid.uuid4())
        session['key'] = human_code()
        if (not Endpoint.autocomplete.in_path(request.path) and
                not Endpoint.healthz.in_path(request.path)):
            return redirect(url_for(
                'sess_mang',
                session_id=session['uuid'],
                follow=get_request_url(request.url)), code=307)
        else:
            g.user_config = Config(**session['config'])
    elif 'cookies_disabled' not in request.args:
        session.permanent = True
        software.permanent_session_lifetime = timedelta(days=365)
        g.user_config = Config(**session['config'])
    else:
        session.pop('_permanent', None)
        g.user_config = Config(**default_config)

    if not g.user_config.url:
        g.user_config.url = get_request_url(request.url_root)

    g.user_request = Request(
        request.headers.get('User-Agent'),
        get_request_url(request.url_root),
        config=g.user_config)

    g.software_location = g.user_config.url


@software.after_request
def successerfunc(resp):
    resp.headers['X-Content-Type-Options'] = 'nosniff'
    resp.headers['X-Frame-Options'] = 'DENY'

    if os.getenv('ARMY1O1_CSP', False):
        resp.headers['Content-Security-Policy'] = software.config['CSP']
        if os.environ.get('HTTPS_ONLY', False):
            resp.headers['Content-Security-Policy'] += \
                'upgrade-insecure-requests'

    return resp


@software.errorhandler(404)
def land_nowhere(e):
    software.logger.warn(e)
    return redirect(g.software_location)


@software.route(f'/{Endpoint.healthz}', methods=['GET'])
def healthz():
    return ''


@software.route(f'/{Endpoint.session}/<session_id>', methods=['GET', 'PUT', 'POST'])
def sess_mang(session_id):
    if 'uuid' in session and session['uuid'] == session_id:
        session['valid'] = True
        return redirect(request.args.get('follow'), code=307)
    else:
        follow_url = request.args.get('follow')
        req = PreparedRequest()
        req.prepare_url(follow_url, {'cookies_disabled': 1})
        session.pop('_permanent', None)
        return redirect(req.url, code=307)


@software.route('/', methods=['GET'])
@software.route(f'/{Endpoint.home}', methods=['GET'])
@need_login
def index():
    if 'error_message' in session and session['error_message']:
        error_message = session['error_message']
        session['error_message'] = ''
        return render_template('error.html', error_message=error_message)

    return render_template('index.html',
                           newest_version=1,
                           languages=software.config['LANGUAGES'],
                           countries=software.config['COUNTRIES'],
                           themes=software.config['THEMES'],
                           translation=software.config['TRANSLATIONS'][
                               g.user_config.get_localization_lang()
                           ],
                           logo=render_template(
                               'logo.html',
                               dark=g.user_config.dark),
                           config_disabled=(
                                   software.config['CONFIG_DISABLE'] or
                                   not valid_user_session(session) or
                                   'cookies_disabled' in request.args),
                           config=g.user_config,
                           version_number=software.config['VERSION_NUMBER'])


@software.route(f'/{Endpoint.opensearch}', methods=['GET'])
def opensearch():
    globalsearchurl = g.software_location
    if globalsearchurl.endswith('/'):
        globalsearchurl = globalsearchurl[:-1]
    if requiressl(globalsearchurl):
        globalsearchurl = globalsearchurl.replace('http://', 'https://', 1)

    get_only = g.user_config.get_only or 'Chrome' in request.headers.get(
        'User-Agent')

    return render_template(
        'opensearch.xml',
        main_url=globalsearchurl,
        request_type='' if get_only else 'method="post"'
    ), 200, {'Content-Disposition': 'attachment; filename="opensearch.xml"'}


@software.route(f'/{Endpoint.findingpage}', methods=['GET'])
def findingpage():
    gatheringlink = g.software_location
    if gatheringlink.endswith('/'):
        gatheringlink = gatheringlink[:-1]
    return render_template('search.html', url=gatheringlink)


@software.route(f'/{Endpoint.autocomplete}', methods=['GET', 'POST'])
def autocomplete():
    ac_var = 'ARMY1O1_AUTOCOMPLETE'
    if os.getenv(ac_var) and not read_config_bool(ac_var):
        return jsonify({})

    q = g.request_params.get('q')
    if not q:
        q = str(request.data).replace('q=', '')

    if q.startswith('!') and len(q) > 1 and not q.startswith('! '):
        return jsonify([q, [bang_json[_]['suggestion'] for _ in bang_json if
                            _.startswith(q)]])

    if not q and not request.data:
        return jsonify({'?': []})
    elif request.data:
        q = urlparse.unquote_plus(
            request.data.decode('utf-8').replace('q=', ''))


@software.route(f'/{Endpoint.search}', methods=['GET', 'POST'])
@must_want
@need_login
def search():
    g.user_config = g.user_config.from_params(g.request_params)

    search_util = Search(request, g.user_config, g.session_key)
    query = search_util.new_search_query()

    bang = resolve_bang(query=query, bangs_dict=bang_json)
    if bang != '':
        return redirect(bang)

    if not query:
        return redirect(url_for('.index'))

    response = search_util.generate_response()

    if search_util.feeling_lucky:
        return redirect(response, code=303)

    localization_lang = g.user_config.get_localization_lang()
    translation = software.config['TRANSLATIONS'][localization_lang]
    translate_to = localization_lang.replace('lang_', '')

    response = bold_search_terms(response, query)
    if search_util.check_kw_ip():
        html_soup = bsoup(str(response), 'html.parser')
        response = add_ip_card(html_soup, get_client_ip(request))
    conversion = check_currency(str(response))
    if conversion:
        html_soup = bsoup(str(response), 'html.parser')
        response = add_currency_card(html_soup, conversion)

    return render_template(
        'display.html',
        newest_version=1,
        query=urlparse.unquote(query),
        search_type=search_util.search_type,
        config=g.user_config,
        lingva_url=software.config['TRANSLATE_URL'],
        translation=translation,
        translate_to=translate_to,
        translate_str=query.replace(
            'translate', ''
        ).replace(
            translation['translate'], ''
        ),
        is_translation=any(
            _ in query.lower() for _ in [translation['translate'], 'translate']
        ) and not search_util.search_type,  
        response=response,
        version_number=software.config['VERSION_NUMBER'],
        search_header=(render_template(
            'header.html',
            config=g.user_config,
            logo=render_template('logo.html', dark=g.user_config.dark),
            query=urlparse.unquote(query),
            search_type=search_util.search_type,
            mobile=g.user_request.mobile)
                       if 'isch' not in
                          search_util.search_type else '')), 200


@software.route(f'/{Endpoint.config}', methods=['GET', 'POST', 'PUT'])
@must_want
@need_login
def config():
    config_disabled = (
            software.config['CONFIG_DISABLE'] or
            not valid_user_session(session))
    if request.method == 'GET':
        return json.dumps(g.user_config.__dict__)
    elif request.method == 'PUT' and not config_disabled:
        if 'name' in request.args:
            config_pkl = os.path.join(
                software.config['CONFIG_PATH'],
                request.args.get('name'))
            session['config'] = (pickle.load(open(config_pkl, 'rb'))
                                 if os.path.exists(config_pkl)
                                 else session['config'])
            return json.dumps(session['config'])
        else:
            return json.dumps({})
    elif not config_disabled:
        config_data = request.form.to_dict()
        if 'url' not in config_data or not config_data['url']:
            config_data['url'] = g.user_config.url

        if 'name' in request.args:
            pickle.dump(
                config_data,
                open(os.path.join(
                    software.config['CONFIG_PATH'],
                    request.args.get('name')), 'wb'))

        session['config'] = config_data
        return redirect(config_data['url'])
    else:
        return redirect(url_for('.index'), code=403)


@software.route(f'/{Endpoint.url}', methods=['GET'])
@must_want
@need_login
def url():
    if 'url' in request.args:
        return redirect(request.args.get('url'))

    q = request.args.get('q')
    if len(q) > 0 and 'http' in q:
        return redirect(q)
    else:
        return render_template(
            'error.html',
            error_message='Unable to resolve query: ' + q)


@software.route(f'/{Endpoint.imgres}')
@must_want
@need_login
def imgres():
    return redirect(request.args.get('imgurl'))


@software.route(f'/{Endpoint.element}')
@must_want
@need_login
def element():
    cipher_suite = Fernet(g.session_key)
    src_url = cipher_suite.decrypt(request.args.get('url').encode()).decode()
    src_type = request.args.get('type')

    try:
        file_data = g.user_request.send(base_url=src_url).content
        tmp_mem = io.BytesIO()
        tmp_mem.write(file_data)
        tmp_mem.seek(0)

        return send_file(tmp_mem, mimetype=src_type)
    except exceptions.RequestException:
        pass

    empty_gif = base64.b64decode(
        'R0lGODlhAQABAIAAAP///////yH5BAEKAAEALAAAAAABAAEAAAICTAEAOw==')
    return send_file(io.BytesIO(empty_gif), mimetype='image/gif')


@software.route(f'/{Endpoint.neighbourseye}')
@need_login
def neighbourseye():
    get_body = g.user_request.send(base_url=request.args.get('location')).text
    get_body = get_body.replace('src="/',
                                'src="' + request.args.get('location') + '"')
    get_body = get_body.replace('href="/',
                                'href="' + request.args.get('location') + '"')

    results = bsoup(get_body, 'html.parser')

    for script in results('script'):
        script.decompose()

    return render_template(
        'display.html',
        response=results,
        translation=software.config['TRANSLATIONS'][
            g.user_config.get_localization_lang()
        ]
    )


def thereyougo() -> None:
    parser = argparse.ArgumentParser(
        description='Army1o1 starter')
    parser.add_argument(
        '--proxyauth',
        default='',
        metavar='<username:password>',
        help='Username and key for the HTTP/SOCKS proxy again by default there is nope')

    parser.add_argument(
        '--host',
        default='127.0.0.1',
        metavar='<ip address>',
        help='Please provide the host by default we take localhost')
    parser.add_argument(
        '--debug',
        default=False,
        action='store_true',
        help='AHAA there you see the debuger mode by default False)')
    parser.add_argument(
        '--https-only',
        default=False,
        action='store_true',
        help='redirects HTTPS for all requests ')
    parser.add_argument(
        '--userpass',
        default='',
        metavar='<username:password>',
        help='Username and key for the by default there is nope')
    parser.add_argument(
        '--proxytype',
        default='',
        metavar='<socks4|socks5|http>',
        help='You can set up the proxy again by default there is nope)')
    parser.add_argument(
        '--port',
        default=5000,
        metavar='<port number>',
        help='Please provide the port by default port [5000])')
    parser.add_argument(
        '--proxyloc',
        default='',
        metavar='<location:port>',
        help='Sets a proxy location for all connections (default None)')
    args = parser.parse_args()
    if args.debug:
        software.run(host=args.host, port=args.port, debug=args.debug)
    else:
        waitress.serve(software, listen="{}:{}".format(args.host, args.port))
