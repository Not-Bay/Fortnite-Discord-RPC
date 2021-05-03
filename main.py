from functools import partial
import fortnitepy
import pypresence
import webbrowser
import pyautogui
import requests
import datetime
import crayons
import asyncio
import time
import json
import sys 
import os

class Auth:
    def __init__(self):

        self.IOS_TOKEN = "MzQ0NmNkNzI2OTRjNGE0NDg1ZDgxYjc3YWRiYjIxNDE6OTIwOWQ0YTVlMjVhNDU3ZmI5YjA3NDg5ZDMxM2I0MWE="
        self.SWITCH_TOKEN = "NTIyOWRjZDNhYzM4NDUyMDhiNDk2NjQ5MDkyZjI1MWI6ZTNiZDJkM2UtYmY4Yy00ODU3LTllN2QtZjNkOTQ3ZDIyMGM3"
        self.DAUNTLESS_TOKEN = "YjA3MGYyMDcyOWY4NDY5M2I1ZDYyMWM5MDRmYzViYzI6SEdAWEUmVEdDeEVKc2dUIyZfcDJdPWFSbyN+Pj0+K2M2UGhSKXpYUA=="

        self.ACCOUNT_PUBLIC_SERVICE = "https://account-public-service-prod03.ol.epicgames.com"
        self.OAUTH_TOKEN = f"{self.ACCOUNT_PUBLIC_SERVICE}/account/api/oauth/token"
        self.EXCHANGE = f"{self.ACCOUNT_PUBLIC_SERVICE}/account/api/oauth/exchange"
        self.DEVICE_CODE = f"{self.ACCOUNT_PUBLIC_SERVICE}/account/api/oauth/deviceAuthorization"
        self.DEVICE_AUTH_GENERATE = f"{self.ACCOUNT_PUBLIC_SERVICE}/account/api/public/account/" + "{account_id}/deviceAuth"

    def HTTPRequest(self, url: str, headers = None, data = None, method = None):

        if method == 'GET':
            response = requests.get(url, headers=headers, data=data)
        elif method == 'POST':
            response = requests.post(url, headers=headers, data=data)
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers, data=data)

        return response

    def get(self, url, headers=None, data=None):
        return self.HTTPRequest(url, headers, data, 'GET')

    def post(self, url, headers=None, data=None):
        return self.HTTPRequest(url, headers, data, 'POST')

    def delete(self, url, headers=None, data=None):
        return self.HTTPRequest(url, headers, data, 'DELETE')

    
    async def fetch_client_credentials(self):

        headers = {
            "Authorization": f"basic {self.DAUNTLESS_TOKEN}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            "grant_type": "client_credentials",
            "token_type": "eg1"
        }
        response = self.post(self.OAUTH_TOKEN, headers=headers, data=data)

        return response.json()

    async def get_device_code_session(self, credentials: dict):

        headers = {
            "Authorization": f"bearer {credentials['access_token']}",
        }
        data = {
            "prompt": "login"
        }
        response = self.post(self.DEVICE_CODE, headers=headers, data=data)

        return response.json()

    async def device_code_auth(self, device_code: dict):

        headers = {
            "Authorization": f"basic {self.SWITCH_TOKEN}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            "grant_type": "device_code",
            "device_code": device_code['device_code']
        }
        response = self.post(self.OAUTH_TOKEN, headers=headers, data=data)

        return response.json()

    async def get_exchange_code(self, credentials: dict):

        headers = {
            "Authorization": f"bearer {credentials['access_token']}"
        }
        response = self.get(self.EXCHANGE, headers)

        return response.json()

    async def exchange_code_auth(self, exchange_code: dict):

        headers = {
            "Authorization": f"basic {self.IOS_TOKEN}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            "grant_type": "exchange_code",
            "exchange_code": exchange_code['code']
        }
        response = self.post(self.OAUTH_TOKEN, headers, data)

        return response.json()

    async def generate_device_auths(self, auth_session: dict):

        headers = {
            "Authorization": f"bearer {auth_session['access_token']}"
        }
        response = self.post(self.DEVICE_AUTH_GENERATE.format(account_id=auth_session['account_id']), headers)

        return response.json()

    async def get_account_by_user_id(self, user_id: str, credentials: dict):

        headers = {
            "Authorization": f"bearer {credentials['access_token']}"
        }
        response = self.get(self.ACCOUNT_BY_USER_ID.format(user_id=user_id), headers)

        return response.json()


    async def pre_authenticate(self):

        client_credentials = await self.fetch_client_credentials()
        if 'errorCode' in client_credentials:
            return False, client_credentials
        else:
            device_code_session = await self.get_device_code_session(client_credentials)
            if 'errorCode' in device_code_session:
                return False, device_code_session
            else:
                return True, device_code_session

    async def authenticate(self, devicecodesession: dict):

        while True:
            device_code_result = await self.device_code_auth(devicecodesession)

            if 'errorCode' in device_code_result:
                if device_code_result['errorCode'] == 'errors.com.epicgames.account.oauth.authorization_pending':
                    await asyncio.sleep(devicecodesession['interval'])
                    continue
                elif device_code_result['errorCode'] == 'errors.com.epicgames.not_found':
                    log(f'Canceled due to device code expiration: {crayons.magenta(device_code_result)}', 'error')
                    return False, device_code_result
            else:
                break

        exchange_code = await self.get_exchange_code(device_code_result)
        if 'errorCode' in exchange_code:
            return False, exchange_code
        else:
            final_auth_session = await self.exchange_code_auth(exchange_code)
            if 'errorCode' in final_auth_session:
                return False, final_auth_session
            else:
                device_auths = await self.generate_device_auths(final_auth_session)
                if 'errorCode' in device_auths:
                    return False, device_auths
                else:
                    return True, {"device_id": device_auths['deviceId'], "account_id": device_auths['accountId'], "secret": device_auths['secret']}

class data():
    def __init__(self):
        self.user = None
        self.online = False
        self.before_online = False
        self.after_playing = None
        self.before_playing = None
        self.playing_timestamp = None

userdata = data()

client_id = '770037031773798410' # dont change this unless you know what are u doing
RPC = pypresence.AioPresence(client_id=client_id, loop=asyncio.get_event_loop())

def log(content, mode):

    now = datetime.datetime.now().strftime('[%H:%M:%S]')

    if mode == 'rpc':
        print(f'{now} {crayons.green("[RPC]")} {content}')

    elif mode == 'warn':
        print(f'{now} {crayons.yellow("[WARN]")} {content}')

    elif mode == 'error':
        print(f'{now} {crayons.red("[ERROR]")} {content}')
    
    elif mode == 'info':
        print(f'{now} {crayons.white("[INFO]")} {content}')

    elif mode == 'debug':
        if settings['debug'] == True:
            print(f'{now} {crayons.blue("[DEBUG]")} {content}')


with open('device_auths.json', 'r', encoding='utf-8') as d:
    auths = json.load(d)

with open('settings.json', 'r', encoding='utf-8') as s:
    settings = json.load(s)


client = fortnitepy.Client(
    auth=fortnitepy.DeviceAuth(
        device_id=auths['device_id'], 
        account_id=auths['account_id'], 
        secret=auths['secret']
    )
)

@client.event
async def event_ready():
    log('Fortnitepy client ready', 'debug')

    try:
        await RPC.connect()
        log('Connected to discord', 'rpc')
    except Exception as e:
        client.loop.create_task(try_to_connect_rpc())

    await client.party.edit_and_keep(partial(client.party.set_privacy, privacy=fortnitepy.PartyPrivacy.PRIVATE))
    await client.set_presence(status='Fortnite Discord RPC', away=fortnitepy.AwayStatus.AWAY)

    flag = False
    for friend in client.friends:
        if friend.display_name == settings['Owner']:
            userdata.user = friend
            await update_rpc(friend.last_presence)
            flag = True
            break
    
    if flag == False:
        log(f'The owner are not a friend. Add: "{client.user.display_name}"', 'warn')
        flag2 = False
        for pendingfriend in client.pending_friends:
            if pendingfriend.display_name == settings['Owner']:
                await pendingfriend.accept()
                await update_rpc(pendingfriend.last_presence)
                log('Pending friend request from the owner accepted', 'info')
                break

    client.loop.create_task(check_user_online())
    

@client.event
async def event_friend_add(friend):
    
    if friend.display_name == settings['Owner']:
        userdata.user == friend
        log('Owner are now friend of the bot', 'info')


@client.event
async def event_friend_request(request):

    if request.display_name == settings['Owner']:
        await request.accept()
        log('Friend request from the owner accepted', 'info')

@client.event
async def event_friend_presence(before, after):

    global userdata

    if after.friend.display_name == settings['Owner']:

        userdata.before_playing = False if before == None else before.playing
        userdata.after_playing = False if after == None else after.playing
        userdata.playing_timestamp = int(time.time()) if userdata.after_playing == True and userdata.before_playing == False else userdata.playing_timestamp if userdata.before_playing == True and userdata.after_playing == True else None

        try:
            await update_rpc(after)
        except Exception as e:
            log(f'{e}', 'error')
            if settings['debug']:
                raise e


async def update_rpc(presence):

    if presence == None:
        try:
            await RPC.clear()
        except Exception as e:
            log(f'Failed to clear RPC: {e}', 'error')

            if isinstance(e, pypresence.InvalidID):
                asyncio.create_task(try_to_connect_rpc())

            elif isinstance(e, pypresence.InvalidPipe):
                asyncio.create_task(try_to_connect_rpc())
            
            else:
                if settings['debug']:
                    raise e
            

    else:
        if presence.status != None:
            try:
                await RPC.update(
                    details = presence.status,
                    state = 'Windows' if presence.platform == fortnitepy.Platform.WINDOWS else 'Mac' if presence.platform == fortnitepy.Platform.MAC else 'PlayStation 4' if presence.platform == fortnitepy.Platform.PLAYSTATION else 'Xbox' if presence.platform == fortnitepy.Platform.XBOX else 'Nintendo Switch' if presence.platform == fortnitepy.Platform.SWITCH else 'iOS' if presence.platform == fortnitepy.Platform.IOS else 'Android' if presence.platform == fortnitepy.Platform.ANDROID else 'PlayStation 5' if presence.platform == fortnitepy.Platform.PLAYSTATION_5 else 'Xbox Series X' if presence.platform == fortnitepy.platform.XBOX_X else None,
                    start = userdata.playing_timestamp,
                    large_image = 'fortnite_icon',
                    large_text = 'Fortnite Discord RPC',
                    party_id = presence.party.id if presence.party.private == False else None,
                    join = presence.session_id if presence.party.private == False else None
                )
            except Exception as e:
                log(f'Failed to update RPC: {e}', 'error')

                if isinstance(e, pypresence.InvalidID):
                    asyncio.create_task(try_to_connect_rpc())

                elif isinstance(e, pypresence.InvalidPipe):
                    asyncio.create_task(try_to_connect_rpc())

                else:
                    if settings['debug']:
                        raise e

                

async def check_user_online():

    log('Check user online task started', 'debug')

    while True:

        global userdata

        if userdata.user == None:
            flag = False
            for friend in client.friends:
                if friend.display_name == settings['Owner']:
                    flag = True
                    log('User online task finished', 'debug')
                    break
            if flag == False:
                await asyncio.sleep(3)
        
        else:

            user = client.get_friend(userdata.user.id)

            if user.is_online():
                userdata.online = True
                userdata.before_online = True
            else:
                userdata.online = False
                await update_rpc(None)
                userdata.before_online = False

            await asyncio.sleep(5)

async def try_to_connect_rpc():

    log('Reconnect RPC loop task started', 'debug')

    while True:

        try:
            await RPC.connect()
            log('Connected to discord', 'rpc')
            break
        except:
            await asyncio.sleep(5)

    log('Reconnect RPC loop task finished', 'debug')


def check_update():

    if '--noupdatecheck' in sys.argv:
        return

    files_to_check = ['main.py', 'requirements.txt', 'install.bat', 'start.bat', 'README.md', 'LICENSE']
    files_with_changes = []

    url = 'https://raw.githubusercontent.com/BayGamerYT/Fortnite-Discord-RPC/main/'

    for file in files_to_check:
        not_found = False
        try:
            local = open(file, 'r', encoding='utf-8')
        except FileNotFoundError:
            not_found = True

        request = requests.get(f'{url}{file}')

        if request.status_code == 200:

            if not_found == True:
                with open(file, 'w', encoding='utf-8') as f:
                    f.write(request.text)
                continue

            if local.read() != request.text:
                files_with_changes.append(file)
        
        local.close()
        
    if files_with_changes != []:

        log('An update is available', 'warn')

        files_with_changes_str = ''
        for i in files_with_changes:
            files_with_changes_str += i + ' '

        ask = pyautogui.confirm(
            title = 'Fortnite Discord RPC',
            text = f'An update is available. Files with changes: {files_with_changes_str}',
            buttons = ['Update', 'Later']
        )

        if ask == 'Update':

            for file in files_to_check:

                local = open(file, 'w', encoding='utf-8')
                request = requests.get(f'{url}{file}')

                if request.status_code == 200:

                    local.write(request.text)

                local.close()

            log('Restarting...', 'info')

            del sys.argv[0]
            args_str = ''
            for arg in sys.argv:
                args_str += f' {arg}'

            if 'requirements.txt' in files_with_changes:
                os.system(f'{"python3" if sys.platform != "win32" else "py -3"} -m pip install -r requirements.txt\n{"python3" if sys.platform != "win32" else "py"} main.py --isRestart {args_str}')
                time.sleep(3)
            else:
                os.system(f'{"python3" if sys.platform != "win32" else "py"} main.py --isRestart {args_str}')
            sys.exit()


if __name__ == "__main__":
    if '--isRestart' in sys.argv:
        print('\n')
        log('Restart completed', 'info')
    else:
        print(crayons.white('Fortnite Discord RPC', bold=True))
        print(crayons.white('Made by BayGamerYT\n'))
    try:
        if '--isRestart' not in sys.argv:
            check_update()

        if settings['Owner'] == "":
            log('Owner field in settings are default, asking user for his epic games id', 'debug')

            user_display_name = pyautogui.prompt(
                title = 'Fortnite Discord RPC',
                text = f'Enter your epic games display name'
            )

            if user_display_name != None:

                settings['Owner'] = user_display_name
                with open('settings.json', 'w', encoding='utf-8') as f:
                    json.dump(settings, f, indent=4, ensure_ascii=False)

        if auths == {"device_id": "", "account_id": "", "secret": ""}:

            log('The device_auths.json file contains nothing. Starting initial authentication', 'debug')
            device_code = Auth()
            device_code_session = asyncio.run(device_code.pre_authenticate())

            if device_code_session[0] == True:
                log('Authentication required', 'warn')
                log(f'Log in to {device_code_session[1]["verification_uri_complete"]} with the account to be used as a monitor.', 'info')
                try:
                    webbrowser.open(url=device_code_session[1]["verification_uri_complete"])
                    log('Web browser opened in login page', 'info')
                except:
                    pass

                final_auth = asyncio.run(device_code.authenticate(device_code_session[1]))
                
                if final_auth[0] == True:
                    newauths = final_auth[1]
                    with open('device_auths.json', 'w', encoding='utf-8') as f:
                        json.dump(newauths, f, indent=4)

                    del sys.argv[0]
                    args_str = ''
                    for arg in sys.argv:
                        args_str += f' {arg}'
    
                    log('Restarting...', 'info')
                    os.system(f'{"python3" if sys.platform != "win32" else "py"} main.py --isRestart {args_str}')
                    sys.exit()

                else:
                    log(f'An error occurred during authentication: {crayons.red(final_auth[1])}', 'error')
                    sys.exit()
            else:
                log(f'An error occurred during authentication, it was not possible to obtain the device code session: {crayons.red(device_code_session[1])}', 'error')
                sys.exit()

        loop = asyncio.get_event_loop()

        log(f'Monitoring account: "{settings["Owner"]}"', 'info')

        log('Starting fortnitepy client', 'debug')
        start_task = loop.run_until_complete(client.start())

        if isinstance(start_task.exception(), fortnitepy.errors.AuthException):

            log(f'An authentication error occurred while trying to start the client.: {crayons.red(start_task.exception())}', 'error')

            with open('device_auths.json', 'w', encoding='utf-8') as f:
                json.dump({"device_id": "", "account_id": "", "secret": ""}, f, indent=4)

            log('Old device auths deleted, restarting...', 'info')

            
    except KeyboardInterrupt:
        log('Keyboard interruption', 'info')
        log('Disconnected', 'rpc')
        print(crayons.red('Closing...'))
        sys.exit()