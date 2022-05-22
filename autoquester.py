import logging
import json
import os
import time
import sys
from tokenize import group
import hero.utils.utils as hero_utils
import quests.quest_v2 as quest_v2
import quests.quest_v1 as quest_v1
import hero.hero as heroes
from quests.training import dancing, arm_wrestling, alchemist_assistance, card_game, darts, helping_the_farm, puzzle_solving, game_of_ball
from quests.professions import foraging, minning, gardening, fishing
from web3 import Web3
from datetime import datetime, date
from quests.utils import utils as quest_utils
# import math
import base64


TRAINING_QUESTING_ADDRESSES = {
    'strength': arm_wrestling.QUEST_CONTRACT_ADDRESS, 
    'intelligence': alchemist_assistance.QUEST_CONTRACT_ADDRESS,
    'wisdom': puzzle_solving.QUEST_CONTRACT_ADDRESS,
    'luck': card_game.QUEST_CONTRACT_ADDRESS,
    'agility': game_of_ball.QUEST_CONTRACT_ADDRESS,
    'vitality': helping_the_farm.QUEST_CONTRACT_ADDRESS,
    'endurance': dancing.QUEST_CONTRACT_ADDRESS,
    'dexterity': darts.QUEST_CONTRACT_ADDRESS
}

PROFESSION_QUESTING_ADDRESSES = {
    'foraging': foraging.QUEST_CONTRACT_ADDRESS_V2,
    'gardening': gardening.QUEST_CONTRACT_ADDRESS,
    'mining': minning.GOLD_QUEST_CONTRACT_ADDRESS,
    'fishing': fishing.QUEST_CONTRACT_ADDRESS_V2
}


today = date.today()
private_key = base64.b64decode(os.getenv('PRIVATE_KEY_ENCODED')).decode('utf-8')

start_log_path = os.getenv('QUEST_START_LOG_PATH')
completed_log_path = os.getenv('QUEST_COMPLETED_LOG_PATH')
error_log_path = os.getenv('QUEST_ERROR_LOG_PATH')

training_heroes = [int(hero_id) for hero_id in json.loads(os.getenv('TRAINING_HEROES'))]
profession_heroes = [int(hero_id) for hero_id in json.loads(os.getenv('PROFESSION_HEROES'))]
still_questing = []

log_format = '%(asctime)s|%(name)s|%(levelname)s: %(message)s'

logger = logging.getLogger("DFK-hero")
logger.setLevel(logging.DEBUG)
logging.basicConfig(level=logging.INFO, format=log_format, stream=sys.stdout)

rpc_server = 'https://api.harmony.one'
logger.info("Using RPC server " + rpc_server)

gas_price_gwei = 40
tx_timeout = 30
w3 = Web3(Web3.HTTPProvider(rpc_server))
account_address = w3.eth.account.privateKeyToAccount(private_key).address
questV2 = quest_v2.Quest(rpc_server, logger)
questV1 = quest_v1.Quest(rpc_server, logger)

####################################################################################################################################

def complete_quests():
    
    print(f"Checking if there are completed Training Quests")

    for hero in training_heroes: #indiscriminately going to check if each hero if questing and claim as appropriate
        try:    
            quest_info = quest_utils.human_readable_quest(questV2.get_hero_quest(hero))
            
            if quest_info:
                if quest_info['completeAtTime'] and time.time() > quest_info['completeAtTime']:
                    print(f"Found quest for hero {hero}")
                    tx_receipt = questV2.complete_quest(hero, private_key, w3.eth.getTransactionCount(account_address), gas_price_gwei, tx_timeout)
                    quest_result = questV2.parse_complete_quest_receipt(tx_receipt)
                    
                    with open(f"{completed_log_path}/{today}.txt", "a+") as f:
                        f.write(f"{datetime.now()} -- CLAIMED HERO {hero} -- REWARDS - {str(quest_result)}\n")
                    logger.info("Rewards: " + str(quest_result))
                elif quest_info['completeAtTime']:
                    print(f"Found quest for hero {hero}, but they are still questing -- {quest_info['completeAtTime'] - time.time()} seconds left")
                    still_questing.append(hero)
                else:
                    print(f"Quest not completed yet: {quest_info['completeAtTime'] - time.time()} seconds left")
            else:
                print(f"No quest info found for {hero}")
                
        except Exception as e:
            with open(f"{error_log_path}/{today}.txt", "a+") as f:
                f.write(f"{datetime.now()} -- ERROR CLAIMING -- {hero} -- WITH EXCEPTION {e}")
    
    print(f"Checking is there are completed Profession Quests")
    
    readable_heroes = []
    
    for id in profession_heroes:
        # logger.info("Processing hero #"+str(id))
            # owner = heroes.get_owner(id, rpc_server)
        hero = heroes.get_hero(id, rpc_server)
        readable_hero = heroes.human_readable_hero(hero)
        # print(readable_hero)
        # print('\n')
        readable_heroes.append(readable_hero)
        
    profession_groups = hero_utils.group_by_profession(readable_heroes)
    
    for profession in profession_groups:
        for hero in profession_groups[profession]:
            hero = hero.get('id')
            # quest_info = None
            if profession == 'mining':
                try:
                    quest_info = quest_utils.human_readable_quest(questV1.get_hero_quest(hero))
                except Exception as e:
                    with open(f"{error_log_path}/{today}.txt", "a+") as f:
                        f.write(f"{datetime.now()} -- ERROR CLAIMING -- {hero} -- WITH EXCEPTION {e}")
            else:
                try:    
                    quest_info = quest_utils.human_readable_quest(questV2.get_hero_quest(hero))
                except Exception as e:
                    with open(f"{error_log_path}/{today}.txt", "a+") as f:
                        f.write(f"{datetime.now()} -- ERROR CLAIMING -- {hero} -- WITH EXCEPTION {e}")
            
            if quest_info:
                if quest_info['completeAtTime'] and time.time() > quest_info['completeAtTime']:
                    print(f"Found quest for hero {hero}")
                    if profession == 'mining':
                        tx_receipt = questV1.complete_quest(hero, private_key, w3.eth.getTransactionCount(account_address), gas_price_gwei, tx_timeout)
                        quest_result = questV1.parse_complete_quest_receipt(tx_receipt)
                        
                        with open(f"{completed_log_path}/{today}.txt", "a+") as f:
                            f.write(f"{datetime.now()} -- CLAIMED HERO {hero} -- REWARDS - {str(quest_result)}\n")
                        logger.info("Rewards: " + str(quest_result))
                    else:
                        tx_receipt = questV2.complete_quest(hero, private_key, w3.eth.getTransactionCount(account_address), gas_price_gwei, tx_timeout)
                        quest_result = questV2.parse_complete_quest_receipt(tx_receipt)
                        
                        with open(f"{completed_log_path}/{today}.txt", "a+") as f:
                            f.write(f"{datetime.now()} -- CLAIMED HERO {hero} -- REWARDS - {str(quest_result)}\n")
                        logger.info("Rewards: " + str(quest_result))
                elif quest_info['completeAtTime']:
                    print(f"Found quest for hero {hero}, but they are still questing -- {quest_info['completeAtTime'] - time.time()} seconds left")
                    still_questing.append(hero)
                else:
                    print(f"Quest not completed yet: {quest_info['completeAtTime'] - time.time()} seconds left")
            else:
                print(f"No quest info found for {hero}")


####################################################################################################################################

def start_training_quests():
    readable_heroes = []
    
    for id in list(set(training_heroes) - set(still_questing)):
        logger.info("Processing hero #"+str(id))
        # owner = heroes.get_owner(id, rpc_server)
        hero = heroes.get_hero(id, rpc_server)
        readable_hero = heroes.human_readable_hero(hero)
        readable_heroes.append(readable_hero)

    stat_groups = hero_utils.group_by_highest_stat(readable_heroes) #maps stat to list of ids
    attempts = 5
    level = 1
    
    for stat in stat_groups:
        ready_to_quest = []
        group = []
        for hero in stat_groups[stat]:
            if hero_utils.is_ready_to_quest(hero): #determines if the hero has at least 25 stamina and appends it to list
                if len(group) < 6:
                    group.append(hero.get('id'))
                else:
                    ready_to_quest.append(group)
                    group = []
                    group.append(hero.get('id'))   
        
        ready_to_quest.append(group)              
                
        if ready_to_quest: #if we have heroes with at least 25 stamina for a given training quest
            
            for group in ready_to_quest:
                if group:
                    try:
                        print(f"Questing {group} for {stat}")
                        quest_contract = TRAINING_QUESTING_ADDRESSES[stat]
                        questV2.start_quest(quest_contract, group, attempts, level, private_key, w3.eth.getTransactionCount(account_address), gas_price_gwei, tx_timeout)
                        with open(f"{start_log_path}/{today}.txt", 'a+') as f:
                            f.write(f"{datetime.now()} -- SENT HEROES {group} ON {stat} QUEST\n")
                        with open(f"questing_groups.txt", "a+") as f:
                            f.write(f"{group}\n")
                    except Exception as e:
                        print(e)
                        with open(f"{error_log_path}/{today}.txt", "a+") as f:
                            f.write(f"{datetime.now()} -- ERROR STARTING QUEST -- {group} -- WITH EXCEPTION {e}\n")
                        
                        

def mining_quests():
    
    
    hero_list = [152391]
    readable_heroes = []
    
    for id in hero_list:
        logger.info("Processing hero #"+str(id))
            # owner = heroes.get_owner(id, rpc_server)
        hero = heroes.get_hero(id, rpc_server)
        readable_hero = heroes.human_readable_hero(hero)
        print(readable_hero)
        print('\n')
        readable_heroes.append(readable_hero)
    
    level = 0
    # attempts = 1
    profession_groups = hero_utils.group_by_profession(readable_heroes)

    for profession in profession_groups:
        for hero in profession_groups[profession]:
            group = [hero.get('id')]
            try:
                print(f"Questing {group} for {profession}")
                attempts = hero_utils.get_current_stamina(hero)
                quest_contract = PROFESSION_QUESTING_ADDRESSES[profession]
                questV1.start_quest(quest_contract, group, 1, private_key, w3.eth.getTransactionCount(account_address), gas_price_gwei, tx_timeout)
                # with open(f"{start_log_path}/{today}.txt", 'a+') as f:
                #     f.write(f"{datetime.now()} -- SENT HEROES {group} ON {profession} QUEST\n")
                # with open(f"questing_groups.txt", "a+") as f:
                #     f.write(f"{group}\n")
            except Exception as e:
                print(e)
                # with open(f"{error_log_path}/{today}.txt", "a+") as f:
                #     f.write(f"{datetime.now()} -- ERROR STARTING QUEST -- {group} -- WITH EXCEPTION {e}\n")
    return

def start_profession_quests():
    
    attempts = 5
    level = 0
    
    readable_heroes = []
    
    for id in list(set(profession_heroes) - set(still_questing)):
        logger.info("Processing hero #"+str(id))
            # owner = heroes.get_owner(id, rpc_server)
        hero = heroes.get_hero(id, rpc_server)
        readable_hero = heroes.human_readable_hero(hero)
        # print(readable_hero)
        # print('\n')
        readable_heroes.append(readable_hero)
        
        
    profession_groups = hero_utils.group_by_profession(readable_heroes)
        
    for profession in profession_groups:
        
        ##### Gold Mining Quests
        if profession == 'mining':
            group = []
            for hero in profession_groups[profession]:
                if hero_utils.get_current_stamina(hero) >= 20:
                    group.append(hero.get('id'))
            try:
                if group:
                    print(f"Questing {group} for {profession}")
                    quest_contract = PROFESSION_QUESTING_ADDRESSES[profession]
                    questV1.start_quest(quest_contract, group, 1, private_key, w3.eth.getTransactionCount(account_address), gas_price_gwei, tx_timeout) #1 is the for the 'attempts' variable. Unsure why 1 quests that hero for their current total stamina
                    with open(f"{start_log_path}/{today}.txt", 'a+') as f:
                        f.write(f"{datetime.now()} -- SENT HEROES {group} ON {profession} QUEST\n")
                    with open(f"questing_groups.txt", "a+") as f:
                        f.write(f"{group}\n")
            except Exception as e:
                print(e)
                with open(f"{error_log_path}/{today}.txt", "a+") as f:
                    f.write(f"{datetime.now()} -- ERROR STARTING QUEST -- {group} -- WITH EXCEPTION {e}\n")

        ##### Fishing and Foraging Quests 
        else:
            ready_to_quest = []
            group = []
            for hero in profession_groups[profession]:
                if hero_utils.is_ready_to_quest(hero): #determines if the hero has at least 25 stamina and appends it to list
                    if len(group) < 6:
                        group.append(hero.get('id'))
                    else:
                        ready_to_quest.append(group)
                        group = []
                        group.append(hero.get('id'))   
                        
            
            ready_to_quest.append(group)
            
            
            if ready_to_quest:
                for group in ready_to_quest:
                    if group:
                        try:
                            print(f"Questing {group} for {profession}")
                            quest_contract = PROFESSION_QUESTING_ADDRESSES[profession]
                            questV2.start_quest(quest_contract, group, attempts, level, private_key, w3.eth.getTransactionCount(account_address), gas_price_gwei, tx_timeout)
                            with open(f"{start_log_path}/{today}.txt", 'a+') as f:
                                f.write(f"{datetime.now()} -- SENT HEROES {group} ON {profession} QUEST\n")
                            with open(f"questing_groups.txt", "a+") as f:
                                f.write(f"{group}\n")
                        except Exception as e:
                            print(e)
                            with open(f"{error_log_path}/{today}.txt", "a+") as f:
                                f.write(f"{datetime.now()} -- ERROR STARTING QUEST -- {group} -- WITH EXCEPTION {e}\n")
        
            
        

        

if __name__ == "__main__":
        
    ####################################################################################################################################
    
    # mining_quests()
    complete_quests()
    start_training_quests()
    start_profession_quests()
    still_questing = []
    
    ####################################################################################################################################

    
