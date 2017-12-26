import requests
from bs4 import BeautifulSoup

class HTB:

    def __init__(self, email, password):
        self.session = requests.Session()
        self.__login(email, password)
        self.update_machines()

    def __login(self, email, password):
        '''Initializes a Hack the Box session'''
        login_page = self.session.get('https://www.hackthebox.eu/login').text
        login_parse = BeautifulSoup(login_page, 'html.parser')
        csrf_token = login_parse.find('meta',  {'name': 'csrf-token'})['content']
        post_data = {'_token': csrf_token, 'email': email, 'password': password}
        logged_in_page = self.session.post('https://www.hackthebox.eu/login', data=post_data).text
        if 'These credentials do not match our records.' in logged_in_page:
            raise Exception('Login Failed')

    def __update_machines(self, url):
        '''Update attr to a dict of machines'''
        page = self.session.get(url).text
        parse = BeautifulSoup(page, 'html.parser')
        table = parse.find('table')
        # Ignore the first entry, it's the header
        entries = table.findAll('tr')[1:]
        machines = {}
        for entry in entries:
            name, machine = HTB.__parse_machine_row(entry)
            machines[name] = machine
        return machines

    def update_machines(self):
        '''Update all machine lists'''
        self.update_active_machines()
        self.update_retired_machines()

    def update_active_machines(self):
        '''Update active_machines with a dict of the currently active machines'''
        self.active_machines = self.__update_machines('https://www.hackthebox.eu/home/machines/list')

    def update_retired_machines(self):
        '''Update retired_machines with a dict of currently retired machines'''
        self.retired_machines = self.__update_machines('https://www.hackthebox.eu/home/machines/retired')

    @staticmethod
    def __parse_machine_row(soup_tr):
        machine = {}
        soup_tds = soup_tr.findAll('td')
        name = soup_tds[0].find('a').getText()
        machine['id'] = soup_tds[0].find('a')['href'].split('/')[-1]
        machine['author'] = soup_tds[1].find('a').getText()
        machine['os'] = soup_tds[2].getText().strip()
        machine['ip'] = soup_tds[3].getText().strip()
        return name, machine
