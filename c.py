import cloudscraper, ctypes, time, json, os, requests, random
from argparse import Namespace
from colorama import init, Fore
from threading import Thread
scraper = cloudscraper.create_scraper(browser={'browser': 'firefox','platform': 'windows','mobile': False})
os.system('cls')
init()

rbxflip_tokens = json.load(open('config.json','r'))

main_bearer = rbxflip_tokens['rbxflip_tokens']['main_token']
second_bearer = rbxflip_tokens['rbxflip_tokens']['second_token']
webhook = rbxflip_tokens['webhook']

main_inventory = []
second_inventory = []
main_user = ''
second_user = ''

rpsType = ['Rock', 'Paper', 'Scissors']

def retrieve_inventories():
    first = scraper.get('https://legacy.rbxflip-apis.com/users/authenticated-user/items', headers={'authorization': f'Bearer {main_bearer}'}).json()
    for item in first['data']['items']:
        main_inventory.append(item)
    second = scraper.get('https://legacy.rbxflip-apis.com/users/authenticated-user/items', headers={'authorization': f'Bearer {second_bearer}'}).json()
    for item in second['data']['items']:
        second_inventory.append(item)

def grabPair():
    global main_inventory, second_inventory
    for main in main_inventory:
        mainData = Namespace(**main)
        if mainData.tags == []:
            for alt in second_inventory:
                altData = Namespace(**alt)
                if altData.tags == []:

                    if mainData.value*0.9 < altData.value < mainData.value*1.1:
                        print(f'{Fore.LIGHTBLUE_EX}Found pair to flip:\n\n    First account: {mainData.name} ({mainData.value} value)\n    Second account: {altData.name} ({altData.value} value)\n\n{Fore.WHITE}')

                        data = {
                            'embeds':[{
                                'author': {
                                    'name': f'Found flip pair'
                                    },
                                'color': int('1266ba',16),
                                'fields': [
                                    {'name': f'Main Account','value': f'{mainData.name} ({mainData.value})','inline':True},
                                    {'name': f'Alt Account','value': f'{altData.name} ({altData.value})','inline':True},
                                ]
                            }]
                        }
                        requests.post(webhook, json=data)

                        return mainData, altData
    return False, False

def check_inventories():
    global main_inventory, second_inventory, rpsType
    try:

        if 'Recyclable' in str(main_inventory) and str(second_inventory):

            mainPair, altPair = grabPair()

            if mainPair == False and altPair == False:
                print(f"Unable to find pair, this is probably because you don't have a pair which can be flipped")
                print(f'A pair is found when a limited from your first and second account are within 10% value of eachother')
                return None

            mainOwner = mainPair.serialNumber
            altOwner = altPair.serialNumber

            option = random.choice(rpsType)

            if type(mainOwner) != int: mainOwner = None
            if type(altOwner) != int: altOwner = None

            mPair = {
                "mode": "RPS",
                "option": option,
                "items": [
                    {
                    "userAssetId": mainPair.userAssetId,
                    "assetId": mainPair.assetId,
                    "serialNumber": mainOwner,
                    "ownerId": mainPair.ownerId,
                    "name": mainPair.name,
                    "value": mainPair.value,
                    "tags": mainPair.tags,
                    "selected": True
                    }
                ]
            }

            create = scraper.post('https://legacy.rbxflip-apis.com/games/versus/RPS', headers={'authorization': f'Bearer {main_bearer}'}, json=mPair).json()
            if 'data' in create:
                gameId = create['data']['id']

                print(f'{Fore.LIGHTBLUE_EX}RPS Game was created > {gameId} (option: {option}){Fore.WHITE}')

                data = {
                    'embeds':[{
                        'color': int('7653c6',16),
                        'fields': [
                            {'name': f'RPS Game Created','value': f'Game Id: {gameId}\nOption: {option}','inline':True},
                        ]
                    }]
                }
                requests.post(webhook, json=data)

                aPair = {
                    "mode": "RPS",
                    "id": gameId,
                    "option": option,
                    "items": [
                        {
                        "userAssetId": altPair.userAssetId,
                        "assetId": altPair.assetId,
                        "serialNumber": altOwner,
                        "ownerId": altPair.ownerId,
                        "name": altPair.name,
                        "value": altPair.value,
                        "tags": altPair.tags,
                        "selected": True
                        }
                    ]
                }

                print(f'{Fore.MAGENTA}Attempting to join {gameId}')
                for i in range(3):
                    Thread(target=joinGame, args=[gameId, option, aPair]).start() # 3 requests as it's possible 1 might fail to bypass cloudflare, but for all 3 is incredibly unlikely. feel free to up the threads if you want but i'm not sure of the ratelimit

            else:
                print(f'{Fore.RED}Unable to create RPS Game due to error > {str(create)}{Fore.WHITE}')

        else:
            print(f'One of your accounts does not have a small limited!')
        
    except Exception as err:
        print(f'{Fore.RED}{str(err)}')
        input()

def joinGame(gameId, option, aPair):
    global main_inventory, second_inventory, rpsType
    try:
        join = scraper.put(f'https://legacy.rbxflip-apis.com/games/versus/RPS/{gameId}', headers={'authorization': f'Bearer {second_bearer}'}, json=aPair).json()
        if 'ok' in join:
            print(f'{Fore.GREEN}Second account joined {gameId}{Fore.WHITE}')

            data = {
                'embeds':[{
                    'color': int('28d269',16),
                    'fields': [
                        {'name': f'Alt account joined RPS Game','value': f'Game Id: {gameId}','inline':True},
                    ]
                }]
            }
            requests.post(webhook, json=data)

        elif 'Someone is joining this game' in str(join):
            pass
        else:
            print(f'{Fore.RED}Account did not join RPS Game due to error: {str(join)}{Fore.WHITE}')
    except Exception as err:
        print(f'{Fore.RED}{str(err)}')
        input()

def checkUser():
    global main_user, second_user
    info = scraper.get('https://legacy.rbxflip-apis.com/auth/user', headers={'authorization': f'Bearer {main_bearer}'}).json()
    if 'ok' in info:
        user = info['data']['user']['name']
        print(f'{Fore.GREEN}{user} was set as main account')
        main_user = user
    else:
        print(f'{Fore.RED}Main bearer token was invalid!')
        input('Press Enter to exit')
        quit()
    info = scraper.get('https://legacy.rbxflip-apis.com/auth/user', headers={'authorization': f'Bearer {second_bearer}'}).json()
    if 'ok' in info:
        user = info['data']['user']['name']
        print(f'{Fore.GREEN}{user} was set as second account')
        main_user = user
    else:
        print(f'{Fore.RED}Second bearer token was invalid!')
        input('Press Enter to exit')
        quit()


print(f'{Fore.YELLOW}Keep in mind that this made with little testing')
print(f'{Fore.YELLOW}Make sure your tokens both have been 2fa verified within the past 24 hours, or you could end up creating a flip on main account, but second account needed 2fa to join (and someone could join it before you are able to verify)')
print(f'{Fore.YELLOW}No autoclaim at the moment as I dont have anything to claim so I cant view the request it makes')
print(f'{Fore.YELLOW}I am unsure of possible errors other than cloudflare bypass fails, so you might want to just watch the flip creation+joining process incase anything happens')
print(f'{Fore.YELLOW}\nPress enter to continue')
input()

os.system('cls')

checkUser()
retrieve_inventories()
check_inventories()
