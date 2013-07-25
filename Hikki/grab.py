# -*- coding: utf-8 -*-

# script to make the swogi spreadsheets into the json file we want.
import json
from collections import Counter
import re
import gspread
from feed.date.rfc3339 import tf_from_timestamp
import sys

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

(username, password) = open("password.conf").read().split(" ")
gc = gspread.login(username, password)
sh = gc.open_by_key("0ArCz3yAJlMXkdEhzbjBySGl6Qkg4dWJLVHNKV0pmcHc")
new_ts = max(tf_from_timestamp(sh.get_worksheet(1).updated),
             tf_from_timestamp(sh.get_worksheet(1).updated))
if new_ts <= old_ts:
    sys.exit(0)
csheet = sh.get_worksheet(1).get_all_values()
ssheet = sh.get_worksheet(2).get_all_values()


out = open("hikki_cards.json", "w")
out.write(json.dumps(csheet, indent=2, separators=(',', ': ')))
out.close()
out = open("hikki_skills.json", "w")
out.write(json.dumps(ssheet, indent=2, separators=(',', ': ')))
out.close()

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
    card = {"recipe": None, "base_recipe": None}
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

for k,v in skill_text.iteritems():
    skill_text[k] = re.sub(r"(\$\d\d\d\d)", skill_replace, skill_text[k])

for k,v in name_to_ids.iteritems():
    name_to_ids[k] = sorted(list(v))

out = open("swogi.json", "w")
out.write(json.dumps({"id_to_card": id_to_card, "name_to_ids": name_to_ids,
    "skill_text": skill_text}, indent=2, separators=(',', ': '), sort_keys=True))
out.close()
