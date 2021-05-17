from pathlib import Path
import os

from requests import Session
from requests.auth import HTTPBasicAuth
import re
import urllib3
from zeep import Client, Settings
from zeep.transports import Transport
from zeep.cache import SqliteCache
from zeep.exceptions import Fault
from ciscoaxl import axl
from getpass import getpass

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class axl(object):

    def __init__(self, username, password, cucm, cucm_version):

        cwd = os.path.dirname(os.path.abspath(__file__))
        if os.name == "posix":
            wsdl = Path(f"{cwd}/schema/{cucm_version}/AXLAPI.wsdl").as_uri()
        else:
            wsdl = str(Path(f"{cwd}/schema/{cucm_version}/AXLAPI.wsdl").absolute())
        session = Session()
        session.verify = False
        session.auth = HTTPBasicAuth(username, password)
        settings = Settings(
            strict=False, xml_huge_tree=True, xsd_ignore_sequence_order=True
        )
        transport = Transport(session=session, timeout=10, cache=SqliteCache())
        axl_client = Client(wsdl, settings=settings, transport=transport)

        self.wsdl = wsdl
        self.username = username
        self.password = password
        self.wsdl = wsdl
        self.cucm = cucm
        self.cucm_version = cucm_version
        self.UUID_PATTERN = re.compile(
            r"^[\da-f]{8}-([\da-f]{4}-){3}[\da-f]{12}$", re.IGNORECASE
        )
        self.client = axl_client.create_service(
            "{http://www.cisco.com/AXLAPIService/}AXLAPIBinding",
            f"https://{cucm}:8443/axl/",
        )
    def get_route_pattern(self, patterns=[]):
        try:
            uuids = []
            for pattern in patterns:
                uuid = self.client.listRoutePattern(
                    {"pattern": pattern}, returnedTags={"pattern": "", "uuid": "", "routePartitionName": ""}
                )
                uuids.append(uuid)
        except Fault as e:
            return e
        rps = []
        for uuid in uuids:
            if "return" in uuid and uuid["return"] is not None:
                for rp in uuid["return"]["routePattern"]:
                    rps.append(rp)
        if len(rps) == 0:
            return 'No matches'
        else:
            return rps

    def get_route_lists(self):
        response = self.client.listRouteList(
            {"name": '%'}, returnedTags={"name": ""})
        for entry in response['return']['routeList']:    
            print(entry['name'])
    
    def update_route_pattern(self, **args):
        try:
            return self.client.updateRoutePattern(**args)
        except Fault as e:
            return e


if __name__ == '__main__':
    # change to user, password, cucm, and ver of choosing.
    print('\n')
    print('WELCOME TO THE ROUTE LIST FLIPPER APPLICATION' , '\n')
    userid= input('Enter your CUCM username: ')
    pwd = getpass()
    cucm = input('Enter Pub IP address: ')
    version = input('Enter CUCM version (11.5 or 12.5): ')
    print('Please wait...')
    while True:
        client = axl(userid, pwd, cucm, version)
        # add as many RPs to the list below as needed.  example: patterns = ['800%', '877%', '888%', '855%']
        patterns = ['800%', '833%' , '844%' , '855%' , '866%' , '877%' , '888%', '81339%']
        # get a list of UUIDs for patterns
        rps = client.get_route_pattern(patterns=patterns)
        for rp in rps:
            print(f"{rp.pattern} - {rp.routePartitionName._value_1} - {rp.uuid}")
        # once UUID is identified, you can use func to change RL as desired, UUIDs don't change so this can be hard coded
        # if same RP will be flipped/changed to different RLs.
        uuid = input('Please Enter the uuid of the RP you would like to update: ')
        print('\nPlease select from the available Route Lists: ')
        rls = client.get_route_lists()
        rl = input('What Route List would you like to update the pattern with?: ')
        result = client.update_route_pattern(uuid=uuid, destination={'routeListName': rl})
        print(result)
        print("Your Route Pattern's RL has been updated")
        print('\n')
        Continue = str(input('Would you like to update another Route Pattern? Please enter yes or no: '))
        stop = 'no' or 'No'
        if Continue==stop:
            print('\n')
            print('Thank you for using the Route List Flipper tool')
            print('\n')  
            exit()
