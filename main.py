from fortnitepy.ext import commands as fncommands
from pypresence import AioPresence
import time
import crayons
import fortnitepy
import asyncio
import json

class Data():
    def __init__(self):
        self.user = None

with open('device_auths.json', 'r', encoding='utf-8') as d:
    auths = json.load(d)

with open('settings.json', 'r', encoding='utf-8') as s:
    settings = json.load(s)

ask_for_code = True if auths['device_id'] == '' or auths['account_id'] == '' or auths['secret'] == '' else False

fnclient = fncommands.Bot(
    command_prefix='',
    auth=fortnitepy.AdvancedAuth(
        device_id=auths['device_id'],
        account_id=auths['account_id'],
        secret=auths['secret'],
        prompt_authorization_code=ask_for_code
    )
)

@fnclient.event
async def event_device_auth_generate(details, email):

    print(crayons.yellow('[INFO] Device auths generated'))

    with open('device_auths.json', 'w', encoding='utf-8') as fw:
        auths = json.dump(details, fw, indent=4)

@fnclient.event
async def event_friend_request(request):

    if request.author.display_name == settings['Owner']:
        await request.accept()

@fnclient.event
async def event_ready():

    flag = False

    for friend in fnclient.friends:
        if friend.display_name == settings['Owner']:
            Data.user=friend
            flag = True
            break

    if flag == False:
        print(crayons.blue(f'The owner must be friend of the bot to start RPC\nAdd: "{fnclient.user.display_name}" to start'))

    fnclient.loop.create_task(check_friend())
    fnclient.loop.create_task(rpc_loop())


client_id = '770037031773798410'
RPC = AioPresence(client_id=client_id, loop=asyncio.get_event_loop())

async def check_friend():

    while True:

        friend = fnclient.get_friend(user_id=Data.user.id)

        if friend.is_online() == False:
            Data.user = None
        
        elif friend.last_presence.available == False:
            Data.user = None
        
        else:
            Data.user = friend

        await asyncio.sleep(5)

async def rpc_loop():

    print(crayons.green('RPC Started'))
    await RPC.connect()
    
    while True:

        if Data.user != None:

            platform = Data.user.last_presence.platform
            partysize = Data.user.last_presence.party_size

            await RPC.update(
                state = 'Windows' if platform == fortnitepy.Platform.WINDOWS else 'Mac' if platform == fortnitepy.Platform.MAC else 'PlayStation 4' if platform == fortnitepy.Platform.PLAYSTATION else 'Xbox' if platform == fortnitepy.Platform.XBOX else 'Nintendo Switch' if platform == fortnitepy.Platform.SWITCH else 'IOS' if platform == fortnitepy.Platform.IOS else 'Android' if platform == fortnitepy.Platform.ANDROID else '',
                details = Data.user.last_presence.status,
                large_image = 'fortnite_icon',
                large_text = 'Fortnite Discord RPC',
                join = Data.user.last_presence.game_session_join_key,
                party_id=Data.user.last_presence.party.id
            )
        
        else:
            await RPC.clear()
            await asyncio.sleep(5)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()

    loop.create_task(fnclient.start())
    loop.run_forever()