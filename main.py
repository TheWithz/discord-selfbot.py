import asyncio
import json
import os

import aiofiles
import discord

from vocabulary.vocabulary import Vocabulary as vb


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
            # TODO add a translate command using vb.translate('word','en','fra')
            elif content.startswith('>define'):
                # TODO populate embed with correct data
                # TODO create sub commands
                # TODO hopefully fix duplicates
                # and ignore everything after the first white space
                args = content[7:].strip().split()
                # if nothing was entered after the command, do nothing
                if len(args) == 0:
                    await self.delete_message(message)
                    return
                # get the first word typed after the command
                word = args[0]
                meanings = vb.meaning(word, format='list')
                # if the word cannot be found to have any meaning then
                # make an embed showing that. 
                if not meanings:
                    em = discord.Embed(title='Definition of ' + word, description='No definition could be found', colour=0xFF0000)
                    await self.send_message(message.channel, embed=em)
                    await self.delete_message(message)
                    return
                synonyms = vb.synonym(word, format='list')
                antonyms = vb.antonym(word, format='list')
                # part of speech. Not piece of shit :P
                pos = vb.part_of_speech(word, format='list')
                examples = vb.usage_example(word, format='list')
                pronunciations = vb.pronunciation(word, format='list')
                em = discord.Embed(title='Definition of ' + word, colour=0x00FF00)
                for x in range(1, len(meanings) - 1):
                    if x % 25 == 0:
                        await self.send_message(message.channel, embed=em)
                        em = discord.Embed(title='Definition of ' + word, colour=0x00FF00)
                    em.add_field(name='Meaning ' + str(x), value=remove_html(meanings[x]), inline=False)
                await self.send_message(message.channel, embed=em)


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
    with open('config.json') as f:
        config = json.load(f)

    os.makedirs('tmp', exist_ok=True)

    client = Bot()

    client.run(config['token'], bot=False)


if __name__ == '__main__':
    main()
