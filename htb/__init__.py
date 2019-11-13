"""
A wrapper around the Hack the Box API
"""
import requests

__version__ = '1.1.0'

class HTBAPIError(Exception):
    """Raised when API fails"""
    def __init__(self, expression, message=""):
        self.expression = expression
        self.message = message

class HTB:
    """
    Hack the Box API Wrapper

    :attr api_key: API Key used for authenticated queries
    :attr user_agent: The User-Agent to be used with all requests
    """

    BASE_URL = 'https://www.hackthebox.eu/api'

    def __init__(self, api_key, user_agent='Python HTB Client/{}'.format(__version__)):
        self.api_key = api_key
        self.headers = {'User-Agent': user_agent}

    @staticmethod
    def _validate_response(response):
        """
        Validate the response from the API

        :params response: the response dict received from an API call
        :returns: the response dict if the call was successfull
        """
        if response['success'] != '1':
            message = "\n".join([ f"{k}: {v}" for k,v in response.items() ])
            raise HTBAPIError("success != 1", message=message)
        return response

    def _get(self, path: str) -> dict:
        """
        Helper function to get an API endpoint and validate the response

        :params self: the HTB object
        :params path: the path to get including leading forward slash
        :returns: the response dict from the endpoint
        """
        return HTB._validate_response(requests.get(self.BASE_URL + path, headers=self.headers).json())

    def _post(self, path: str, data: dict = None) -> dict:
        """
        Helper function to get an API endpoint and validate the response

        :params self: the HTB object
        :params path: the path to get including leading forward slash
        :returns: the response dict from the endpoint
        """
        return HTB._validate_response(requests.post(self.BASE_URL + path, data=data, headers=self.headers).json())

    def _auth(self, path: str) -> str:
        """
        Helper function to generate an authenticated URL

        :params self: HTB object in use
        :params path: string containing path to query
        :returns: path to authenticated query
        """
        return "{}?api_token={}".format(path, self.api_key)

    def global_stats(self) -> dict:
        """
        Returns current stats about Hack the Box

        :params cls: the HTB class
        :returns: global stats dict
        """
        return self._post('/stats/global')

    def overview_stats(self) -> dict:
        """
        Returns overview stats about Hack the Box

        Doesn't include success key

        :params cls: the HTB class
        :returns: overview stats dict
        """
        return requests.get(self.BASE_URL + '/stats/overview', headers=self.headers).json()

    def daily_owns(self, count: int = 30) -> dict:
        """
        Returns the number of owns and total number of users after the last COUNT days

        :params cls: the HTB class
        :params count: the number of days to get data from
        :returns: daily owns dict
        """
        return self._post('/stats/daily/owns/{}'.format(count))

    def list_conversations(self) -> dict:
        """
        Return the conversations dict

        Doesn't include success key

        :params self: HTB object in use
        :returns: conversations dict
        """
        return requests.post(self.BASE_URL + self._auth('/conversations/list/'), headers=self.headers).json()

    def vpn_freeslots(self) -> dict:
        """
        Return information about free slots on the VPN

        :params self: HTB object in use
        :returns: vpn_freeslots dict
        """
        return self._post(self._auth('/vpnserver/freeslots/'))

    def vpn_statusall(self) -> dict:
        """
        Return information about the status of every VPN

        :params self: HTB object in use
        :returns: vpn_statusall dict
        """
        return self._get(self._auth('/vpnserver/status/all/'))

    def connection_status(self) -> dict:
        """
        Return connection status information

        Success key seems to be behaving incorrectly

        :params self: HTB object in use
        :returns: connection_status dict
        """
        return requests.post(self.BASE_URL + self._auth('/users/htb/connection/status/'), headers=self.headers).json()

    def fortress_connection_status(self) -> dict:
        """
        Return fortress connection status information

        Success key seems to be behaving incorrectly

        :params self: HTB object in use
        :returns: fortress_connection_status dict
        """
        return requests.post(self.BASE_URL + self._auth('/users/htb/fortress/connection/status/'), headers=self.headers).json()

    def switch_vpn(self, lab: str) -> dict:
        """
        Switch the VPN your profile is connected to

        Success key doesn't exist

        :params self: HTB object in use
        :params lab: the lab to connect to, either free, usvip or euvip
        :returns: switch_vpn dict
        """

        if lab not in ("usfree", "eufree", "usvip", "euvip", "euvipbeta"):
            raise HTBAPIError("invalid lab")
        else:
            return requests.post(self.BASE_URL + self._auth('/labs/switch/{}/'.format(lab)), headers=self.headers).json()

    def get_owns(self) -> dict:
        """
        Get which machines the user has owned.

        :params self: HTB object in use
        :returns: machines dict
        """
        return requests.get(self.BASE_URL + self._auth('/machines/owns'), headers=self.headers).json()

    def get_machines(self) -> dict:
        """
        Get all machines on the network

        :params self: HTB object in use
        :returns: machines dict
        """
        return requests.get(self.BASE_URL + self._auth('/machines/get/all/'), headers=self.headers).json()

    def get_machine(self, mid: int) -> dict:
        """
        Get a single machine on the network

        :params self: HTB object in use
        :params mid: Machine ID
        :returns: machine dict
        """
        return requests.get(self.BASE_URL + self._auth('/machines/get/{}/'.format(mid)), headers=self.headers).json()
    
    def spawn_machine(self, mid: int, lab="vip") -> (int, str):
        """
        Spawn a machine

        :params self: HTB object in use
        :params mid: Machine ID
        :params lab: vip for vip users, unknown for free.
        :returns: bool if successful, str status message
        """
        try:
            resp = self._post(self._auth('/vm/{}/assign/{}'.format(lab, mid))).json()
            return (resp['success'], resp['status'])
        except HTBAPIError as e:
            print(e.message)
            return False, "An Error Occurred"
    
    def terminate_machine(self, mid: int, lab="vip") -> (int, str):
        """
        Terminate a machine

        :params self: HTB object in use
        :params mid: Machine ID
        :params lab: vip for vip users, unknown for free.
        :returns: bool if successful, str status message
        """
        try:
            resp = self._post(self._auth('/vm/{}/remove/{}'.format(lab, mid))).json()
            return (resp['success'], resp['status'])
        except HTBAPIError as e:
            print(e.message)
            return False, "An Error Occurred"
    
    def own_machine(self, mid: int, hsh: str, diff: int) -> (int, str):
        """
        Own a challenge on a machine

        :params self: HTB object in use
        :params mid: Machine ID
        :params hsh: Flag Hash
        :params diff: difficult (10-100)
        :returns: bool if successful
        """
        try:
            resp = self._post(self._auth('/machines/own'), {"id": mid, "flag": hsh, "difficulty": diff})
            return (resp['success'], resp['status'])
        except HTBAPIError as e:
            print(e.message)
            return False, "An Error Occurred"
    
    def own_machine_user(self, mid: int, hsh: str, diff: int) -> bool:
        """
        Own a user challenge on a machine

        :params self: HTB object in use
        :params mid: Machine ID
        :params hsh: User Hash
        :params diff: difficult (10-100)
        :returns: bool if successful
        """
        try:
            self._post(self._auth('/machines/own/user/{}/'.format(mid)),
                       {"hash": hsh, "diff": diff})
            return True
        except HTBAPIError:
            return False

    def own_machine_root(self, mid: int, hsh: str, diff: int) -> bool:
        """
        Own a root challenge on a machine

        :params self: HTB object in use
        :params mid: Machine ID
        :params hsh: Root Hash
        :params diff: difficult (10-100)
        :returns: bool if successful
        """
        try:
            self._post(self._auth('/machines/own/root/{}/'.format(mid)),
                       {"hash": hsh, "diff": diff})
            return True
        except HTBAPIError:
            return False

    def reset_machine(self, mid: int) -> dict:
        """
        Reset a machine on the network

        :params self: HTB object in use
        :params mid: Machine ID
        :returns: reset_machine dict
        """
        return self._post(self._auth('/vm/reset/{}/'.format(mid)))
