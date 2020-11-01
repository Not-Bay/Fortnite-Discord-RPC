from pypresence import AioPresence
from functools import partial
import requests
import pyautogui
import datetime
import time
import crayons
import fortnitepy
import asyncio
import json
import sys 
import os

class data():
    def __init__(self):
        self.user = None
        self.online = False
        self.before_online = False
        self.after_playing = None
        self.before_playing = None
        self.playing_timestamp = None

userdata = data()

client_id = '770037031773798410'
RPC = AioPresence(client_id=client_id, loop=asyncio.get_event_loop())

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
    auth=fortnitepy.AdvancedAuth(
        device_id=auths['device_id'],
        account_id=auths['account_id'],
        secret=auths['secret'],
        prompt_authorization_code=True
    )
)

@client.event
async def event_device_auth_generate(details, email):

    with open('device_auths.json', 'w', encoding='utf-8') as fw:
        auths = json.dump(details, fw, indent=4)
    log('Device auths generated and saved', 'debug')

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
    client.loop.create_task(check_update())
    

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

exc = ['Client ID is Invalid']

async def update_rpc(presence):

    if presence == None:
        try:
            await RPC.clear()
        except Exception as e:
            log(f'Failed to clear RPC: {e}', 'error')
            if e in exc:
                client.loop.create_task(try_to_connect_rpc())

    else:
        if presence.status != None:
            try:
                await RPC.update(
                    details = presence.status,
                    state = 'Windows' if presence.platform == fortnitepy.Platform.WINDOWS else 'Mac' if presence.platform == fortnitepy.Platform.MAC else 'PlayStation 4' if presence.platform == fortnitepy.Platform.PLAYSTATION else 'Xbox' if presence.platform == fortnitepy.Platform.XBOX else 'Nintendo Switch' if presence.platform == fortnitepy.Platform.SWITCH else 'iOS' if presence.platform == fortnitepy.Platform.IOS else 'Android' if presence.platform == fortnitepy.Platform.ANDROID else None,
                    start = userdata.playing_timestamp,
                    large_image = 'fortnite_icon',
                    large_text = 'Fortnite Discord RPC',
                    party_id = presence.party.id if presence.party != None else None,
                    join = presence.session_id if presence.joinable == True else None
                )
            except Exception as e:
                log(f'Failed to update RPC: {e}', 'error')
                if e in exc:
                    client.loop.create_task(try_to_connect_rpc())

async def check_user_online():

    log('Check user online task started', 'debug')

    while True:

        global userdata

        if userdata.user == None:
            flag = False
            for friend in client.friends:
                if friend.display_name == settings['Owner']:
                    flag = True
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
    log('User online task finished', 'debug')

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


async def check_update():

    log('Checking for updates...', 'info')

    files_to_check = ['main.py', 'requirements.txt', 'install.bat', 'start.bat', 'README.md', 'LICENSE']
    files_with_changes = []

    url = 'https://raw.githubusercontent.com/BayGamerYT/Fortnite-Discord-RPC/main/'

    for file in files_to_check:

        local = open(file, 'r', encoding='utf-8')
        request = requests.get(f'{url}{file}')

        if request.status_code == 200:

            if local.read() != request.text:
                files_with_changes.append(file)
        
        local.close()
        
    if files_with_changes != []:

        log('An update is available', 'warn')

        ask = pyautogui.confirm(
            title = 'Fortnite Discord RPC',
            text = f'An update is available. Files with changes: {"".join(f"{x} "for x in files_with_changes)}',
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
            if sys.platform == 'win32':
                os.system('py -3 -m pip install -r requirements.txt\npy main.py')
                await asyncio.sleep(3)
                sys.exit()
            else:
                os.system('python3 -m pip install -r requirements.txt\n python3 main.py')
                await asyncio.sleep(3)
                sys.exit()
                
    else:
        log('No updates found', 'info')


if __name__ == "__main__":
    print(crayons.white('Fortnite Discord RPC', bold=True))
    print(crayons.white('Made by BayGamerYT\n'))
    try:
        log('Starting fortnitepy client', 'debug')
        loop = asyncio.get_event_loop()
        loop.create_task(client.start())
        loop.run_forever()
    except KeyboardInterrupt:
        log('Keyboard interruption', 'info')
        log('Disconnected', 'rpc')
        print(crayons.red('Closing...'))
        sys.exit()
