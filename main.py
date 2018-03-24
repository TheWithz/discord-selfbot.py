import asyncio
import json
import os

import aiofiles
import discord

from oxforddict import OxfordDictionary as ox

with open('config.json') as f:
    config = json.load(f)

dictionary = ox(app_keys=config['app_keys'], app_id=config['app_id'])

class Bot(discord.Client):
    def __init__(self):
        super(Bot, self).__init__()

    async def on_ready(self):

        print('Logged in as')
        print(self.user.name)
        print(self.user.id)
        print('------')

    async def on_message(self, message):
        if message.author == self.user:
            content = message.content  # type: str

            if content.startswith('>tex'):
                content = content[4:].strip()
                image_file = await compile_tex(content)
                await self.send_file(message.channel, image_file)
            elif content.startswith('>antonyms'):
                await handle_word(self, message, content[1:9])
            elif content.startswith('>synonyms'):
                await handle_word(self, message, content[1:9])
            elif content.startswith('>definition'):
                await handle_word(self, message, content[1:11])


async def handle_word(self, message, command):
    args = message.content[len(command)+1:].strip().split()
    # if nothing was entered after the command, do nothing
    if len(args) == 0:
        await self.delete_message(message)
        return
    # get the first word typed after the command
    word = args[0]
    response = get_dict(command, word)
    # if the word cannot be found make an embed showing that. 
    if not response:
        em = discord.Embed(title=command + ' of ' + word, description='None could be found', colour=0xFF0000)
        await self.send_message(message.channel, embed=em)
        await self.delete_message(message)
        return
    em = discord.Embed(title=command + ' of ' + word, colour=0x00FF00)
    for x in range(0, len(response)):
        if x % 25 == 0 and x != 0:
            await self.send_message(message.channel, embed=em)
            em = discord.Embed(title=command + ' of ' + word, colour=0x00FF00)
        em.add_field(name=str(x + 1), value=remove_html(response[x]), inline=False)
    await self.send_message(message.channel, embed=em)

    
def get_dict(command, word):
    if command == 'antonyms':
        return dictionary.thesaurus(word, antonyms=True)
    elif command == 'synonyms':
        return dictionary.thesaurus(word, synonyms=True)
    elif command == 'definition':
        return dictionary.entries(word)['results'][0]['lexicalEntries'][0]['entries'][0]['senses'][0]['subsenses']
    return False


# remove html tags while preserving quotes.
def remove_html(s):
    tag = False
    quote = False
    out = ""

    for c in s:
        if c == '<' and not quote:
            tag = True
        elif c == '>' and not quote:
            tag = False
        elif (c == '"' or c == "'") and tag:
            quote = not quote
        elif not tag:
            out = out + c

    return out

async def compile_tex(snippet):
    async with aiofiles.open('template.tex') as f:
        template = await f.read()

    source = template.replace('{_user_code_}', snippet)

    async with aiofiles.open('tmp/snippet.tex', mode='w') as f:
        await f.write(source)

    proc_latex = await asyncio.create_subprocess_exec('pdflatex', 
                                                      '-shell-escape',
                                                      'snippet.tex', cwd='tmp/')
    await proc_latex.wait()

    proc_convert = await asyncio.create_subprocess_exec('convert',
                                                        '-density', '300',
                                                        'snippet.pdf',
                                                        '-trim',
                                                        '-border', '16x16',
                                                        '-background', 'white',
                                                        '-alpha', 'remove',
                                                        '-quality', '90',
                                                        'snippet.png', cwd='tmp/')
    await proc_convert.wait()

    return 'tmp/snippet.png'


def main():

    os.makedirs('tmp', exist_ok=True)

    client = Bot()

    client.run(config['token'], bot=False)


if __name__ == '__main__':
    main()
