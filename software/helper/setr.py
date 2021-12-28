import json
import requests

DDG_BANGS = 'https://duckduckgo.com/bang.v255.js'


def gen_bangs_json(file_bng: str) -> None:

    try:
        r = requests.get(DDG_BANGS)
        r.raise_for_status()
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)

    data = json.loads(r.text)

    bangs_data = {}

    for row in data:
        bang_command = '!' + row['t']
        bangs_data[bang_command] = {
            'url': row['u'].replace('{{{s}}}', '{}'),
            'suggestion': bang_command + ' (' + row['s'] + ')'
        }

    json.dump(bangs_data, open(file_bng, 'w'))


def resolve_bang(query: str, bangs_dict: dict) -> str:

    query = query.lower()
    split_query = query.split(' ')
    for opera in bangs_dict.keys():
        if opera not in split_query \
                and opera[1:] + opera[0] not in split_query:
            continue
        return bangs_dict[opera]['url'].replace(
            '{}',
            query.replace(opera if opera in split_query
                          else opera[1:] + opera[0], '').strip(), 1)
    return ''
