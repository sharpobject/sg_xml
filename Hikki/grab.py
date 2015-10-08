# -*- coding: utf-8 -*-

# script to make the swogi spreadsheets into the json file we want.
import json
from collections import Counter
import re
import gspread
from feed.date.rfc3339 import tf_from_timestamp
from xml.dom import minidom
import sys
import codecs
import locale
from oauth2client.client import SignedJwtAssertionCredentials

sys.stdout = codecs.getwriter(locale.getpreferredencoding())(sys.stdout)

# Takes a dict (or Counter) and an int, returns a new dict with all
# the values multiplied by the int
def cmul(di, n):
    ret = type(di)(di)
    for k in ret.keys():
        ret[k] *= n
    return ret
Counter.__mul__ = cmul

tsfile = open("timestamp", "r")
old_ts = float(tsfile.read())
tsfile.close()

new_ts = 0

json_key = json.load(open("password.conf"))
scope = ['https://spreadsheets.google.com/feeds']
credentials = SignedJwtAssertionCredentials(json_key['client_email'], json_key['private_key'], scope)
gc = gspread.authorize(credentials)

scs = gc.openall()
for sc in scs:
    print sc.id

sh = gc.open_by_key("1ECdAfHs8Z-80gmt0Aj7dhHSuAyPndCS1LoEIsAGp3lo")
ws1 = sh.get_worksheet(1)
ws2 = sh.get_worksheet(2)
new_ts = max(tf_from_timestamp(ws1.updated),
             tf_from_timestamp(ws2.updated))
if new_ts > old_ts:
    csheet = ws1.get_all_values()
    ssheet = ws2.get_all_values()

    out = open("hikki_cards.json", "w")
    out.write(json.dumps(csheet, indent=2, separators=(',', ': ')))
    out.close()
    out = open("hikki_skills.json", "w")
    out.write(json.dumps(ssheet, indent=2, separators=(',', ': ')))
    out.close()
    tsfile = open("timestamp", "w")
    tsfile.write(str(new_ts))
    tsfile.close()

    hikki_schema = ["id", "name", "kr_name", "faction", "episode", "type", "rarity",
                    "life", "size", "limit", "attack", "defense", "stamina", "level",
                    "points", "s1", "s2", "s3", "flavor", "kr_flavor", "upgrade_path"]

    id_to_card = {}
    name_to_ids = {}

    for line in csheet[1:]:
        entries = zip(hikki_schema, line)
        if len(entries) < len(hikki_schema):
            print "Failed to parse hikki line:\n%r"%line
            continue
        card = {}
        for k,v in entries:
            card[k]=v
        skills = [x for x in map(int,[card["s1"], card["s2"], card["s3"]]) if x]
        card["skills"] = skills
        del card["s1"]
        del card["s2"]
        del card["s3"]
        if len(card["episode"]) > 0 and card["episode"][0] not in ["E", "U"]:
            card["episode"] = "EP"+card["episode"]
        id_to_card[card["id"]] = card
        for name in [card["name"],card["kr_name"]]:
            if name not in name_to_ids:
                name_to_ids[name] = set()
            name_to_ids[name].add(card["id"])

    skill_text = {}
    for line in ssheet[1:]:
        skill_text[line[0]] = line[3]

    def skill_replace(id):
        return '"'+skill_text[id.group(1)[1:]]+'"'

    for x in xrange(10):
        for k,v in skill_text.iteritems():
            skill_text[k] = re.sub(r"(\$\d\d\d\d)", skill_replace, skill_text[k])

    for k,v in name_to_ids.iteritems():
        name_to_ids[k] = sorted(list(v))

    out = open("swogi.json", "w")
    out.write(json.dumps({"id_to_card": id_to_card, "name_to_ids": name_to_ids,
    "skill_text": skill_text}, indent=2, separators=(',', ': '), sort_keys=True))
    out.close()

id_to_card = {}
name_to_ids = {}
skill_text = {}

# TODO: DECK_SERIF, INT, EMO, IND, CHA, EXT, various dialogues and stuff??
# ORDER_PRIORITY lol!

attrs = [["EPISODE", "episode"],
         ["POINT", "points"],
         ["USE_LIMIT", "limit"],
         ["TEXT", "flavor"],
         ["SIZE", "size"],
         ["LIFE", "life"],
         ["LV", "level"],
         ["ATTACK_POINT", "attack"],
         ["DEFENSE_POINT", "defense"],
         ["HEALTH_POINT", "stamina"],
        ]

bool_attrs = [["STEP", "can_gift"],
              ["RECIPE_NUMBER", "can_craft"]]

factions = ["Flat girls are the best", "Vita", "Academy",
            "Crux", "Darklore", "Neutral", "Imperial"]

rarities = ["","","","","","C","","UC","","R","DR","EV","TR","","","P","IM"]

skill_tags = ["SKILL_NUMBER", "SKILL_NUMBER_1", "SKILL_NUMBER_2", "SKILL_NUMBER_3"]

types = {"CHARACTER_CARD": "Character",
         "SPELL_CARD": "Spell",
         "FOLLOWER_CARD": "Follower"}

# let's paste code from stackoverflow
import unicodedata as ud

latin_letters= {}

def is_latin(uchr):
    try: return latin_letters[uchr]
    except KeyError:
         return latin_letters.setdefault(uchr, 'LATIN' in ud.name(uchr))

def only_roman_chars(unistr):
    return all(is_latin(uchr)
           for uchr in unistr
           if uchr.isalpha())
# that was fun!

cardData = minidom.parse('en_cardData.xml')
cards = cardData.getElementsByTagName("CHARACTER_CARD")+cardData.getElementsByTagName("SPELL_CARD")+cardData.getElementsByTagName("FOLLOWER_CARD")
for element in cards:
    id = element.getElementsByTagName("ID_NUMBER")[0].firstChild.wholeText
    name = element.getElementsByTagName("NAME")[0].firstChild.wholeText
    if (not id) or (not name):
        continue
    try:
        name.encode('ascii')
    except:
        continue
    if name=="0":
        continue
    card = {"id": id, "name": name}
    for tagname,key in attrs:
        elems = element.getElementsByTagName(tagname)
        if len(elems):
            card[key] = elems[0].firstChild.wholeText
    for tagname,key in bool_attrs:
        elems = element.getElementsByTagName(tagname)
        if len(elems) and int(elems[0].firstChild.wholeText):
            card[key] = True
    elems = element.getElementsByTagName("SIDE")
    if len(elems):
        card["faction"] = factions[int(elems[0].firstChild.wholeText)]
    elems = element.getElementsByTagName("RARITY")
    if len(elems):
        card["rarity"] = rarities[int(elems[0].firstChild.wholeText)]
    card["skills"] = []
    for tagname in skill_tags:
        elems = element.getElementsByTagName(tagname)
        if len(elems) and int(elems[0].firstChild.wholeText):
            card["skills"].append(elems[0].firstChild.wholeText)
    card["type"] = types[element.tagName]
    if len(card["episode"]) > 0 and card["episode"][0] not in ["E", "U"]:
        card["episode"] = "EP"+card["episode"]
    id_to_card[id] = card
    if name not in name_to_ids:
        name_to_ids[name] = set()
    name_to_ids[name].add(id)

for k,v in name_to_ids.iteritems():
    name_to_ids[k] = sorted(list(v))

cardData = minidom.parse('en_cardSkill.xml')
skills = cardData.getElementsByTagName("CARD_SKILL")
for element in skills:
    try:
        id = element.getElementsByTagName("ID")[0].firstChild.wholeText
    except:
        continue
    text = element.getElementsByTagName("TEXT")[0].firstChild.wholeText
    if not id:
        continue
    if not only_roman_chars(text):
        continue
    skill_text[id] = text.replace("<span fontWeight='bold'>", "").replace("</span>", "")

out = open("swogi_na.json", "w")
out.write(json.dumps({"id_to_card": id_to_card, "name_to_ids": name_to_ids,
"skill_text": skill_text}, indent=2, separators=(',', ': '), sort_keys=True))
out.close()
