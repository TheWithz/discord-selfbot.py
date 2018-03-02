import asyncio
import json
import os

import aiofiles
import discord

from oxforddict import OxfordDictionary as ox

with open('config.json') as f:
    config = json.load(f)

dictionary = ox(app_key=config['app_keys'], app_id=config['app_id'])
print(dictionary.thesaurus('cat', synonyms=True))
# print(dictionary.entries('cat')['results'][0]['lexicalEntries'][0]['entries'][0]['senses'][0]['subsenses'][1]['definitions'][0])
