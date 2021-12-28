from enum import Enum


class Endpoint(Enum):
    autocomplete = 'autocomplete'
    home = 'home'
    neighbourseye = 'neighbourseye'
    config = 'config'
    healthz = 'healthz'
    session = 'session'
    search = 'search'
    opensearch = 'opensearch.xml'
    findingpage = 'findingpage.html'
    url = 'url'
    imgres = 'imgres'
    element = 'element'


    def __str__(self):
        return self.value

    def in_path(self, path: str) -> bool:
        return path.startswith(self.value) or \
               path.startswith(f'/{self.value}')
