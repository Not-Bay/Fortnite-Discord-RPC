from functools import partial
import fortnitepy
from fortnitepy import auth
import pypresence
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

        self.ACCOUNT_PUBLIC_SERVICE = "https://account-public-service-prod03.ol.epicgames.com"
        self.OAUTH_TOKEN = f"{self.ACCOUNT_PUBLIC_SERVICE}/account/api/oauth/token"
        self.DEVICE_AUTH_GENERATE = f"{self.ACCOUNT_PUBLIC_SERVICE}/account/api/public/account/" + "{account_id}/deviceAuth"
        self.DEVICE_AUTH_DELETE = f"{self.ACCOUNT_PUBLIC_SERVICE}/api/public/account/" + "{account_id}/deviceAuth/{device_id}"
        self.KILL_AUTH_SESSION = f"{self.ACCOUNT_PUBLIC_SERVICE}/api/oauth/sessions/kill/" + "{access_token}"

    def HTTPRequest(self, url: str, headers = None, data = None, method = None):

        if method == 'GET':
            response = requests.get(url, headers=headers, data=data)
            log(f'[GET] {crayons.magenta(url)} > {response.text}', 'debug')
        elif method == 'POST':
            response = requests.post(url, headers=headers, data=data)
            log(f'[POST] {crayons.magenta(url)} > {response.text}', 'debug')
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers, data=data)
            log(f'[DELETE] {crayons.magenta(url)} > {response.text}', 'debug')

        return response

    def get(self, url, headers=None, data=None):
        return self.HTTPRequest(url, headers, data, 'GET')

    def post(self, url, headers=None, data=None):
        return self.HTTPRequest(url, headers, data, 'POST')

    def delete(self, url, headers=None, data=None):
        return self.HTTPRequest(url, headers, data, 'DELETE')

    def authorization_code_authenticate(self, authorization_code: str):

        headers = {
            "Authorization": f"basic {self.IOS_TOKEN}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            "grant_type": "authorization_code",
            "code": authorization_code
        }
        response = self.post(self.OAUTH_TOKEN, headers, data)

        return response.json()

    def device_auth_authenticate(self, device_auths):

        headers = {
            "Authorization": f"basic {self.IOS_TOKEN}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            "grant_type": "device_auth",
            "device_id": device_auths['device_id'],
            "account_id": device_auths['account_id'],
            "secret": device_auths['secret']
        }

        response = self.post(self.OAUTH_TOKEN, headers=headers, data=data)

        return response.json()

    def generate_device_auths(self, auth_session: dict):

        headers = {
            "Authorization": f"bearer {auth_session['access_token']}"
        }
        response = self.post(self.DEVICE_AUTH_GENERATE.format(account_id=auth_session['account_id']), headers)

        return response.json()

    def kill_auth_session(self, credentials: dict):

        headers = {
            "Authorization": f"bearer {credentials['access_token']}"
        }
        response = self.delete(self.KILL_AUTH_SESSION.format(access_token=credentials['access_token']), headers)

        return response

    def delete_device_auths(self, device_auths: dict, auth_session: dict):

        headers = {
            "Authorization": f"bearer {auth_session['access_token']}"
        }
        response = self.delete(self.DEVICE_AUTH_DELETE.format(account_id=device_auths['account_id'], device_id=device_auths['device_id']), headers)

        return response

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
                platform_str = get_platform_str(presence.platform)
                await RPC.update(
                    details = presence.status,
                    state = platform_str if platform_str != False else None,
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


def get_platform_str(platform: fortnitepy.Platform):

    if platform == fortnitepy.Platform.ANDROID:
        return 'Android'

    elif platform == fortnitepy.Platform.IOS:
        return 'IOS'

    elif platform == fortnitepy.Platform.MAC:
        return 'Mac'

    elif platform == fortnitepy.Platform.PLAYSTATION_4:
        return 'PlayStation 4'

    elif platform == fortnitepy.Platform.PLAYSTATION_5:
        return 'PlayStation 5'

    elif platform == fortnitepy.Platform.SWITCH:
        return 'Nintendo Switch'

    elif platform == fortnitepy.Platform.WINDOWS:
        return 'Windows'

    elif platform == fortnitepy.Platform.XBOX_ONE:
        return 'Xbox One'

    elif platform == fortnitepy.Platform.XBOX_X:
        return 'Xbox Series X'

    else:
        return False


def check_update():

    if '--no-update-check' in sys.argv:
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

    if '--delete-device-auth' in sys.argv:
        log('Deleting saved device auth...', 'info')

        device_auths = json.load(open('device_auths.json', 'r', encoding='utf-8'))

        AUTH = Auth()
        auth_session = AUTH.device_auth_authenticate(device_auths)
        delete = AUTH.delete_device_auths(device_auths, auth_session)
        if 'errorMessage' not in delete.text:
            AUTH.kill_auth_session(auth_session)
            with open('device_auths.json', 'w', encoding='utf-8') as f:
                json.dump({"device_id": "", "account_id": "", "secret": ""}, f, indent=4)

            log('Deleted saved device auth successfully!', 'info')
            exit()
        else:
            error = delete.json()['errorMessage']
            AUTH.kill_auth_session(auth_session)
            log(f'An error ocurred deleting device auth: {error}')
            exit()

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

            log('The device_auths.json file contains nothing', 'debug')
            authorizationcode = Auth()
            log('Authentication required', 'warn')
            while True:
                log('Login to https://www.epicgames.com/id/login?redirectUrl=https%3A%2F%2Fwww.epicgames.com%2Fid%2Fapi%2Fredirect%3FclientId%3D3446cd72694c4a4485d81b77adbb2141%26responseType%3Dcode and paste the response: ', 'info')
                data = input('\n')

                try:
                    authorization_code_data = json.loads(data)
                except Exception as e:
                    log(f'An error ocurred processing the data: {e}. Refresh the page and try again', 'error')
                    continue

                try:
                    redirectUrl = authorization_code_data['redirectUrl']
                    code = redirectUrl.replace('com.epicgames.fortnite://fnauth/?code=', '')
                    auth_session = authorizationcode.authorization_code_authenticate(code)

                    try:
                        error = auth_session['errorMessage']
                        log(f'Failed authentication: {error}', 'error')
                        continue
                    except:
                        log('Authorization code worked. Creating device auth', 'debug')
                        device_auths = authorizationcode.generate_device_auths(auth_session)
                        
                        try:
                            error = device_auths['errorMessage']
                            log(f'Failed device auth creation: {error}')
                            authorizationcode.kill_auth_session(auth_session)
                        except:
                            data = {
                                "device_id": device_auths['deviceId'],
                                "account_id": device_auths['accountId'],
                                "secret": device_auths['secret']
                            }
                            with open('device_auths.json', 'w', encoding='utf-8') as f:
                                json.dump(data, f, indent=4)
                            log('Authentication completed', 'debug')
                            authorizationcode.kill_auth_session(auth_session)
                            del sys.argv[0]
                            args_str = ''
                            for arg in sys.argv:
                                args_str += f' {arg}'
            
                            log('Restarting...', 'info')
                            os.system(f'{"python3" if sys.platform != "win32" else "py"} main.py --isRestart {args_str}')
                            sys.exit()

                except Exception as e:
                    log(f'An error ocurred during authentication: {e}', 'error')
                    continue

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