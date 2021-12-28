from software.sieve import q_cln
from software.helper.session import human_code
from software.helper.setr import gen_bangs_json
from software.helper.misc import gen_file_hash
from flask import Flask
from flask_session import Session
import json
import logging.config
import os
from stem import Signal
from dotenv import load_dotenv

software = Flask(__name__, static_folder=os.path.dirname(
    os.path.abspath(__file__)) + '/static')
if os.getenv('ARMY1O1_DOTENV', ''):
    dotenv_path = '../army1o1.env'
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             dotenv_path))

software.default_key = human_code()
software.config['SECRET_KEY'] = os.urandom(32)
software.config['SESSION_TYPE'] = 'filesystem'
software.config['SESSION_COOKIE_SAMESITE'] = 'strict'

if os.getenv('HTTPS_ONLY'):
    software.config['SESSION_COOKIE_NAME'] = '__Secure-session'
    software.config['SESSION_COOKIE_SECURE'] = True

software.config['VERSION_NUMBER'] = '0.7.0'
software.config['software_ROOT'] = os.getenv(
    'software_ROOT',
    os.path.dirname(os.path.abspath(__file__)))
software.config['STATIC_FOLDER'] = os.getenv(
    'STATIC_FOLDER',
    os.path.join(software.config['software_ROOT'], 'static'))
software.config['BUILD_FOLDER'] = os.path.join(
    software.config['STATIC_FOLDER'], 'build')
software.config['CACHE_BUSTING_MAP'] = {}
software.config['LANGUAGES'] = json.load(open(
    os.path.join(software.config['STATIC_FOLDER'], 'settings/languages.json'),
    encoding='utf-8'))
software.config['COUNTRIES'] = json.load(open(
    os.path.join(software.config['STATIC_FOLDER'], 'settings/countries.json')))
software.config['TRANSLATIONS'] = json.load(open(
    os.path.join(software.config['STATIC_FOLDER'], 'settings/translations.json')))
software.config['THEMES'] = json.load(open(
    os.path.join(software.config['STATIC_FOLDER'], 'settings/themes.json')))
software.config['CONFIG_PATH'] = os.getenv(
    'CONFIG_VOLUME',
    os.path.join(software.config['STATIC_FOLDER'], 'config'))
software.config['DEFAULT_CONFIG'] = os.path.join(
    software.config['CONFIG_PATH'],
    'config.json')
software.config['CONFIG_DISABLE'] = os.getenv('ARMY1O1_CONFIG_DISABLE', '')
software.config['SESSION_FILE_DIR'] = os.path.join(
    software.config['CONFIG_PATH'],
    'session')
software.config['BANG_PATH'] = os.getenv(
    'CONFIG_VOLUME',
    os.path.join(software.config['STATIC_FOLDER'], 'setr'))
software.config['BANG_FILE'] = os.path.join(
    software.config['BANG_PATH'],
    'bangs.json')
software.config['RELEASES_URL'] = 'https://github.com/' \
                             'benbusby/army1o1-search/releases'
translate_url = os.getenv('ARMY1O1_ALT_TL', '')
if not translate_url.startswith('http'):
    translate_url = 'https://' + translate_url
software.config['TRANSLATE_URL'] = translate_url

software.config['CSP'] = 'default-src \'none\';' \
                    'frame-src ' + translate_url + ';' \
                    'manifest-src \'self\';' \
                    'img-src \'self\' data:;' \
                    'style-src \'self\' \'unsafe-inline\';' \
                    'script-src \'self\';' \
                    'media-src \'self\';' \
                    'connect-src \'self\';'

if not os.path.exists(software.config['CONFIG_PATH']):
    os.makedirs(software.config['CONFIG_PATH'])

if not os.path.exists(software.config['SESSION_FILE_DIR']):
    os.makedirs(software.config['SESSION_FILE_DIR'])

if not os.path.exists(software.config['BANG_PATH']):
    os.makedirs(software.config['BANG_PATH'])
if not os.path.exists(software.config['BANG_FILE']):
    gen_bangs_json(software.config['BANG_FILE'])

if not os.path.exists(software.config['BUILD_FOLDER']):
    os.makedirs(software.config['BUILD_FOLDER'])

cache_busting_dirs = ['css', 'js']
for cb_dir in cache_busting_dirs:
    full_cb_dir = os.path.join(software.config['STATIC_FOLDER'], cb_dir)
    for cb_file in os.listdir(full_cb_dir):
        full_cb_path = os.path.join(full_cb_dir, cb_file)
        cb_file_link = gen_file_hash(full_cb_dir, cb_file)
        build_path = os.path.join(software.config['BUILD_FOLDER'], cb_file_link)

        try:
            os.symlink(full_cb_path, build_path)
        except FileExistsError:
            pass
        map_path = build_path.replace(software.config['software_ROOT'], '')
        if map_path.startswith('/'):
            map_path = map_path[1:]
        software.config['CACHE_BUSTING_MAP'][cb_file] = map_path
software.jinja_env.globals.update(q_cln=q_cln)
software.jinja_env.globals.update(
    cb_url=lambda f: software.config['CACHE_BUSTING_MAP'][f])

Session(software)

from software import routes
logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': True,
})
