
## Fortnite Discord RPC

An unofficial rich presence that let you to have Fortnite RPC regardless of the platform on which you play. Made with pypresence and fortnitepy

![preview](https://media.discordapp.net/attachments/838192486547324938/838206225325752340/unknown.png)

![preview playing](https://media.discordapp.net/attachments/838192486547324938/838282084437983232/unknown.png)


### Setup

**Install Python 3.7/3.8:**
https://www.python.org/downloads
Make sure `tcl/tk and IDLE` is enabled before installing

**Install required packages:**
* Windows:
Run `install.bat`

* Other:
Run the command `python3 -m pip install -r requirements.txt`

**Make an epic account to monitore your status**

For this step you can use an unused epic account
You can create an account in [this link](https://www.epicgames.com/id/logout?redirectUrl=https%3A//www.epicgames.com/id/login)

**Run the program**
* Windows:
Run `start.bat`

* Other:
Run the command `python3 main.py`

**Setup**

The first time you start the program you will be prompted to enter your epic games display name and log in to the account to be used to monitor your status.
You only have to wait for a text like this to appear:
```
Login to https://www.epicgames.com/id/login?redirectUrl=https%3A%2F%2Fwww.epicgames.com%2Fid%2Fapi%2Fredirect%3FclientId%3D3446cd72694c4a4485d81b77adbb2141%26responseType%3Dcode and paste the response:
```
Open that link in your browser, login with the bot account **NOT YOUR MAIN**.
You will see a text like this:
![Text example](https://media.discordapp.net/attachments/838192486547324938/856967743471747072/unknown.png)

Copy all and paste it in the console
![Paste example](https://media.discordapp.net/attachments/838192486547324938/856968391041220638/unknown.png)

Hit enter and if you did it correctly and the code didn't expire yet you are ready!

If for some reason you get an error saying that the code is not valid just refresh the page where you got the data and copy all again.


**Add the monitor account as friend**

You may get a message indicating that you are not a friend of the bot. This means you will have to add it by epic games. If you are already a friend of the bot simply ignore this step

**Ready!**

Now you will have your RPC ready, as long as you do not close your discord and you have the program open! Enjoy


**Command line arguments**

Just some command line arguments that can be usefull for you:

```
--delete-device-auth | Deletes created device auth (You will need to do authentication again after this)
--no-update-check | Skips the update check
```


**Note**

There is a possibility that the credentials of the monitor account may be invalid unexpectedly. In that case you will just have to restart and perform the authentication again.

---

If you need help you can send me a private message on twitter `@CodeBayGamerJJ` or add me as a friend on Discord `Bay#7210`

#### Use code BayGamerJJ in the item shop to support me <3 #EpicPartner
