## Fortnite Discord RPC

An unofficial rich presence that let you to have Fortnite RPC regardless of the platform on which you play. Made with pypresence and fortnitepy. 
Its needed a PC (obviously with discord installed) and an unused epic account (used to log in and monitore your status)


### Setup

**Install Python 3.7/3.8:**
https://www.python.org/downloads

**Install required packages:**
* Windows:
Run `install.bat`

* Other:
Run the command `pip -3 install -r requirements.txt`

**Make an epic account to monitore your status**
For this step you can use an unused epic account
You can create an account in [this link](https://www.epicgames.com/id/logout?redirectUrl=https%3A//www.epicgames.com/id/login)

**Setup configuration**
You only need to put your id in the `Owner` field
Example:
```json
{
    "Owner": "Tfue",
    "debug": false
}
```
The `debug` field are for development purposes, doesn't and affect nothing

**Run the program**
* Windows:
Run `start.bat`

* Other:
Run the command `python3 main.py`

**Make the verification**
Its required an verification to generate credentials for the epic account (the account that monitore your status) so for that enter to [this link](https://www.epicgames.com/id/logout?redirectUrl=https%3A//www.epicgames.com/id/login%3FredirectUrl%3Dhttps%253A%252F%252Fwww.epicgames.com%252Fid%252Fapi%252Fredirect%253FclientId%253D3446cd72694c4a4485d81b77adbb2141%2526responseType%253Dcode) and login with that account. Warning: **Don't** use your main account

**Add the epic monitor account as friend**
You may get a message indicating that you are not a friend of the bot. This means you will have to add it by epic games. If you are already a friend of the bot simply ignore this step

**Ready!**
Now you will have your RPC ready, as long as you do not close your desktop discord and you have the program open! Enjoy


---

If you need help add me as friend on discord: `BayGamerYT#0001`

#### Use code BayGamerJJ in the item shop to support me <3 #EpicPartner