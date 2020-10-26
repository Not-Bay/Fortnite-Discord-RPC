from fortnitepy.ext import commands as fncommands
from pypresence import AioPresence
import time
import crayons
import fortnitepy
import asyncio
import json
import sys

client_id = '770037031773798410'
RPC = AioPresence(client_id=client_id, loop=asyncio.get_event_loop())

with open('device_auths.json', 'r', encoding='utf-8') as d:
    auths = json.load(d)

with open('settings.json', 'r', encoding='utf-8') as s:
    settings = json.load(s)

client = fncommands.Bot(
    command_prefix='',
    auth=fortnitepy.AdvancedAuth(
        device_id=auths['device_id'],
        account_id=auths['account_id'],
        secret=auths['secret'],
        prompt_authorization_code=True
    )
)

@client.event
async def event_device_auth_generate(details, email):

    print(crayons.yellow('[INFO] Device auths generated'))

    with open('device_auths.json', 'w', encoding='utf-8') as fw:
        auths = json.dump(details, fw, indent=4)

@client.event
async def event_friend_request(request):

    if request.author.display_name == settings['Owner']:
        await request.accept()

@client.event
async def event_ready():

    await RPC.connect()
    print(crayons.green('RPC connected'))

    for friend in client.friends:
        if friend.display_name == settings['Owner']:
            await update_rpc(friend.last_presence)
            break

class data():
    def __init__(self):
        self.before_playing = False
        self.after_playing = False
        self.timestamp = None

before_playing = False
after_playing = False
playing_timestamp = None

@client.event
async def event_friend_presence(before, after):

    if after.friend.display_name == settings['Owner']:
        if after.friend.is_online == False:
            await RPC.clear()

        else:
            global before_playing
            global after_playing
            global playing_timestamp


            before_playing = False if before == None else before.playing
            after_playing = False if after == None else after.playing
            playing_timestamp = int(time.time()) if after_playing == True and before_playing == False else playing_timestamp if before_playing == True and after_playing == True else None


            try:
                await update_rpc(after)
            except:
                pass

async def update_rpc(presence):

    if presence == None:
        await RPC.clear()
        return

    platform = presence.platform
    await RPC.update(
        details = presence.status,
        state = 'Windows' if platform == fortnitepy.Platform.WINDOWS else 'Mac' if platform == fortnitepy.Platform.MAC else 'PlayStation 4' if platform == fortnitepy.Platform.PLAYSTATION else 'Xbox' if platform == fortnitepy.Platform.XBOX else 'Nintendo Switch' if platform == fortnitepy.Platform.SWITCH else 'IOS' if platform == fortnitepy.Platform.IOS else 'Android' if platform == fortnitepy.Platform.ANDROID else '',
        start = playing_timestamp,
        large_image = 'fortnite_icon',
        large_text = 'Fortnite Discord RPC',
        party_id = presence.party.id if presence.party != None else None,
        join = presence.session_id if presence.joinable == True else None
        )


if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()

        loop.create_task(client.start())
        loop.run_forever()
    except KeyboardInterrupt:
        print(crayons.red('Closing...'))
        sys.exit()