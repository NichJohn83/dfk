import collections
import json
from datetime import datetime
import math

FAIL_ON_NOT_FOUND = False

ALPHABET = '123456789abcdefghijkmnopqrstuvwx'

rarity = {
    0: "common",
    1: "uncommon",
    2: "rare",
    3: "legendary",
    4: "mythic",
}

_class = {
    0: "warrior",
    1: "knight",
    2: "thief",
    3: "archer",
    4: "priest",
    5: "wizard",
    6: "monk",
    7: "pirate",
    16: "paladin",
    17: "darkknight",
    18: "summoner",
    19: "ninja",
    24: "dragoon",
    25: "sage",
    28: "dreadknight"
}

visual_traits = {
    0: 'gender',
    1: 'headAppendage',
    2: 'backAppendage',
    3: 'background',
    4: 'hairStyle',
    5: 'hairColor',
    6: 'visualUnknown1',
    7: 'eyeColor',
    8: 'skinColor',
    9: 'appendageColor',
    10: 'backAppendageColor',
    11: 'visualUnknown2'
}

stat_traits = {
    0: 'class',
    1: 'subClass',
    2: 'profession',
    3: 'passive1',
    4: 'passive2',
    5: 'active1',
    6: 'active2',
    7: 'statBoost1',
    8: 'statBoost2',
    9: 'statsUnknown1',
    10: 'element',
    11: 'statsUnknown2'
}

professions = {
    0: 'mining',
    2: 'gardening',
    4: 'fishing',
    6: 'foraging',
}

stats = {
    0: 'strength',
    2: 'agility',
    4: 'intelligence',
    6: 'wisdom',
    8: 'luck',
    10: 'vitality',
    12: 'endurance',
    14: 'dexterity'
}

elements = {
    0: 'fire',
    2: 'water',
    4: 'earth',
    6: 'wind',
    8: 'lightning',
    10: 'ice',
    12: 'light',
    14: 'dark',
}


def parse_rarity(id):
    value = rarity.get(id, None)
    if FAIL_ON_NOT_FOUND and value is None:
        raise Exception("Rarity not found")
    return value


def parse_class(id):
    value = _class.get(id, None)
    if FAIL_ON_NOT_FOUND and value is None:
        raise Exception("Class not found")
    return value


def parse_profession(id):
    value = professions.get(id, None)
    if FAIL_ON_NOT_FOUND and value is None:
        raise Exception("Profession not found")
    return value


def parse_stat(id):
    value = stats.get(id, None)
    if FAIL_ON_NOT_FOUND and value is None:
        raise Exception("Stat not found")
    return value


def parse_element(id):
    value = elements.get(id, None)
    if FAIL_ON_NOT_FOUND and value is None:
        raise Exception("Element not found")
    return value


def genes2traits(genes):
    traits = []

    stat_raw_kai = "".join(__genesToKai(genes).split(' '))
    for ki in range(0, len(stat_raw_kai)):
        kai = stat_raw_kai[ki]
        value_num = __kai2dec(kai)
        traits.append(value_num)

    assert len(traits) == 48
    arranged_traits = [[], [], [], []]
    for i in range(0, 12):
        index = i << 2
        for j in range(0, len(arranged_traits)):
            arranged_traits[j].append(traits[index + j])

    arranged_traits.reverse()
    return arranged_traits


def parse_stat_genes(genes):
    traits = genes2traits(genes)
    stats = parse_stat_trait(traits[0])
    r1 = parse_stat_trait(traits[1])
    r2 = parse_stat_trait(traits[2])
    r3 = parse_stat_trait(traits[3])

    stats['r1'] = r1
    stats['r2'] = r2
    stats['r3'] = r3
    stats['raw'] = genes

    return stats


def parse_stat_trait(trait):

    if len(trait) != 12:
        raise Exception("Traits must be an array of 12")

    stats = {}
    for i in range(0, 12):
        stat_trait = stat_traits.get(i, None)
        stats[stat_trait] = trait[i]

    stats['class'] = parse_class(stats['class'])
    stats['subClass'] = parse_class(stats['subClass'])

    stats['profession'] = parse_profession(stats['profession'])

    stats['passive1'] = parse_class(stats['passive1'])
    stats['passive2'] = parse_class(stats['passive2'])
    stats['active1'] = parse_class(stats['active1'])
    stats['active2'] = parse_class(stats['active2'])

    stats['statBoost1'] = parse_stat(stats['statBoost1'])
    stats['statBoost2'] = parse_stat(stats['statBoost2'])
    stats['statsUnknown1'] = stats.get(stats['statsUnknown1'], None)  # parse_stat(stat_genes['statsUnknown1'])
    stats['statsUnknown2'] = stats.get(stats['statsUnknown2'], None)  # parse_stat(stat_genes['statsUnknown2'])

    stats['element'] = parse_element(stats['element'])

    return stats


def parse_visual_genes(genes):
    visual_genes = {}
    visual_genes['raw'] = genes

    visual_raw_kai = "".join(__genesToKai(visual_genes['raw']).split(' '))

    for ki in range(0, len(visual_raw_kai)):
        stat_trait = visual_traits.get(int(ki / 4), None)
        kai = visual_raw_kai[ki]
        value_num = __kai2dec(kai)
        visual_genes[stat_trait] = value_num

    visual_genes['gender'] = 'male' if visual_genes['gender'] == 1 else 'female'
    return visual_genes


def hero2str(hero):

    if isinstance(hero['info']['class'], int):
        c = parse_class(hero['info']['class'])
        sc = parse_class(hero['info']['subClass'])
        r = parse_rarity(hero['info']['rarity'])
        l = hero['state']['level']
    else:
        c = hero['info']['class']
        sc = hero['info']['subClass']
        r = hero['info']['rarity']
        l = hero['state']['level']

    return str(hero['id']) + " " + r.title() + " " + c.title() + "/" + sc.title() + " lvl " + str(l)


def __genesToKai(genes):
    BASE = len(ALPHABET)

    buf = ''
    while genes >= BASE:
        mod = int(genes % BASE)
        buf = ALPHABET[int(mod)] + buf
        genes = (genes - mod) // BASE

    # Add the last 4 (finally).
    buf = ALPHABET[int(genes)] + buf

    # Pad with leading 1s.
    buf = buf.rjust(48, '1')
    buf = buf[0:48]

    return ' '.join(buf[i:i + 4] for i in range(0, len(buf), 4))


def __kai2dec(kai):
    return ALPHABET.index(kai)


def parse_names(names_raw_string):
    names_raw_string = names_raw_string\
        .replace("\\xf3", "ó") \
        .replace("\\xf2", "ò") \
        .replace("\\xe9", "é") \
        .replace("\\xe1", "á") \
        .replace("\\xc9", "É") \
        .replace("\\xed", "í") \
        .replace("\\xfa", "ú") \
        .replace("\\xec", "ì")

    if "\\x" in names_raw_string:
        raise Exception("Unhandled unicode found")

    return json.loads(names_raw_string)


def get_current_stamina(hero):
    
        cur_time = int(round(datetime.now().timestamp()))
        stamina_full = hero.get('state').get('staminaFullAt')
        max_stamina = hero.get('stats').get('stamina')
        
        # print(f"cur_time: {cur_time}")
        # print(f"stamina full at: {stamina_full}")
        
        seconds_until_full = stamina_full-cur_time
        minutes_until_full = math.ceil(seconds_until_full/60)
        
        # print(f"minutes until full: {minutes_until_full}")
        
        stamina_left_to_recover = math.ceil(minutes_until_full/20)
        # print(f"stamina_left_to_recover: {stamina_left_to_recover}")
        
        cur_stamina = max_stamina - stamina_left_to_recover
        
        return cur_stamina
    
def get_highest_stat(hero):
    
    stats = hero.get('stats')
            
    green_boost = hero.get('info').get('statGenes').get('statBoost1')
    blue_boost = hero.get('info').get('statGenes').get('statBoost2')
    
    for stat in stats:
        if stat == green_boost:
            stats[stat] += 1
        if stat == blue_boost:
            stats[stat] += 3
                
    return max(filter(lambda x: x not in ('hp', 'mp', 'stamina'), stats), key=stats.get)


def group_by_highest_stat(heroes):
    
    groups = collections.defaultdict(list)
    
    for hero in heroes:
        highest_stat = get_highest_stat(hero)
        groups[highest_stat].append(hero)
        
    return groups

def is_ready_to_quest(hero):
    
    ready = False
    cur_stamina = get_current_stamina(hero)

    if cur_stamina >= 25:
        ready = True    
    
    return ready

def group_by_profession(heroes):
    
    groups = collections.defaultdict(list)
    
    for hero in heroes:
        profession = hero.get('info').get('statGenes').get('profession')
        groups[profession].append(hero)
        
    return groups
    
    

