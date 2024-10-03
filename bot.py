#!/lastdeath/env/bin/python
# Script para enviar mortes de jogadores

import logging
from datetime import datetime, timedelta
from calendar import monthrange
from os import getenv, environ
import time
from io import BytesIO
from dotenv import load_dotenv
from tabulate import tabulate
from models import db, get_last_dead, rank_exp_guild, rank_exp_month, confirm_sent, get_last_bans, ban_confirm_sent
from models import max_level_died, top_10_dead_players, top_10_dead_players_guild, monster_most_kill

from discord.ext import tasks, commands
import discord

load_dotenv()

db_filename = getenv('DATABASE_PATH')
db.bind('sqlite', filename=db_filename)
db.generate_mapping()

environ['TZ'] = 'America/Sao_Paulo'
time.tzset()

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)

GUILDSCHANNELS = getenv('GUILDSCHANNELS').split(';')
TOKEN = getenv('DISCORDTOKEN')
INTERVAL_SEARCH_DEAD = 30  # SECONDS
INTERVAL_LAST_DEATH = 240
INTERVAL_SEARCH_BANS = 300
INTERVAL_BANS = 600
MIN_LEVEL = 850
MIN_LEVEL_BANS = 1


def convert_date(value):
    # convert strint to interval date
    # return (d1, d2)
    d1 = datetime.now().date()
    try:
        d1 = datetime.strptime(value,'%m/%Y')
    except ValueError:
        ...
        
    d1 = d1.replace(day=1)
    _, d2 = monthrange(d1.year, d1.month)
    d2 = d1.replace(day=d2)
    return (d1, d2)


class DeathCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.index = 0
        self.printer.start()
        self.searchs_bans.start()

    def cog_unload(self):
        self.printer.cancel()
        self.searchs_bans.cancel()

    @tasks.loop(seconds=INTERVAL_SEARCH_DEAD)
    async def printer(self):
        # a cada 30 segundos faz a busca e envia se for necessário
        delta = timedelta(seconds=INTERVAL_LAST_DEATH)
        result = get_last_dead(delta, MIN_LEVEL)
        msg = ""
        
        for _, level, name, monsters in result:
            monsters = ' e '.join(monsters.split(','))
            msg += f'[{level}] {name} morreu para {monsters}.\n'

        if msg:
            msg = f'```{msg}```'
            try:
                for channel in GUILDSCHANNELS:
                    channel = int(channel)
                    channel = self.bot.get_channel(channel)
                    await channel.send(content=msg)
            except Exception:
                pass
            finally:
                deathsid = (id for id, *_ in result)
                confirm_sent(deathsid)

    @tasks.loop(seconds=INTERVAL_SEARCH_BANS)
    async def searchs_bans(self):
        # busca os últimos bans
        delta = timedelta(seconds=INTERVAL_BANS)
        result = get_last_bans(delta, MIN_LEVEL_BANS)
        msg = ""
        logger.debug("last bans: %s" %result)
        for _, name, level, _ in result:
            msg += f'🚫 [{level}] {name} foi banido!\n'

        if msg:
            msg = f'```{msg}```'
            try:
                for channel in GUILDSCHANNELS:
                    channel = int(channel)
                    channel = self.bot.get_channel(channel)
                    await channel.send(content=msg)
            except Exception:
                pass
            finally:
                bansid = (id for id, *_ in result)
                ban_confirm_sent(bansid)


    @commands.command(name='weekexp')
    async def week_exp_guild(self, ctx):
        """exp de 7 dias atrás até ontem
        """
        delta = timedelta(days=7)
        result = rank_exp_guild(delta)

        t = tabulate(result,
                     headers=['Player', 'EXP', 'Lv. In', 'Lv. Out', 'Diff'],
                     tablefmt='rounded_grid')
        
        t = f'*Ref: exp de 7 dias atrás até ontem. Exp de hoje contabiliza às 00:10.\n' + t        
        f = BytesIO(t.encode())
        f = discord.File(f, filename='weekexp.txt')
        await ctx.send(file=f)
            
    @commands.command(name='monthexp')
    async def month_exp_guild(self, ctx):
        """exp de 30 dias atrás até ontem
        """
        delta = timedelta(days=30)
        result = rank_exp_guild(delta)
        t = tabulate(result,
                     headers=['Player', 'EXP', 'Lv. In', 'Lv. Out', 'Diff'],
                     tablefmt='rounded_grid')

        t = f'*Ref: exp de 30 dias atrás até ontem. Exp de hoje contabiliza às 00:10.\n' + t
        f = BytesIO(t.encode())
        f = discord.File(f, filename='monthexp.txt')
        await ctx.send(file=f)

    @commands.command(name='killstats')
    async def kill_stats(self, ctx):
        """algumas estatísticas de mortes referente a 30 dias
        """
        delta = timedelta(days=30)
        d1 = datetime.now().date() - delta
        d2 = datetime.now().date()

        max_level = max_level_died(delta)
        max_level = tabulate(max_level, headers=['Lv', 'Date', 'Player'])

        top_10_dead = top_10_dead_players(delta)
        top_10_dead = tabulate(top_10_dead, headers=['Deaths', 'Player'])

        top_10_dead_guild = top_10_dead_players_guild(delta)
        top_10_dead_guild = tabulate(top_10_dead_guild, headers=['Deaths', 'Player'])

        monster_kill = monster_most_kill(delta)
        monster_kill = tabulate(monster_kill, headers=['Kill Players', 'Monster'])

        fmt = f'*Ref: {d1} ~ {d2}'
        fmt += f'\n\n**:skull: Max level died**\n{max_level}'
        fmt += f'\n\n**:skull: Top 10 last deaths**\n{top_10_dead}'
        fmt += f'\n\n**:skull: Top 10 last deaths Guild**\n{top_10_dead_guild}'
        fmt += f'\n\n**:troll: Top 10 monster kill**\n{monster_kill}'
        
        await ctx.send(content = fmt)

    @commands.command(name='exp')
    async def month_exp(self, ctx, d: convert_date):
        """09/2023 - exp de um mês especifico
        """
        rank = rank_exp_month(*d)
        rank = tabulate(rank, headers=['Name', 'Exp', 'Lv. In', 'Lv. Out', 'Diff'])
        d1,_ = d
        rank = f'*Ref. {d1.month}/{d1.year}\n' + rank
        
        f = BytesIO(rank.encode())
        f = discord.File(f, filename='monthexp.txt')
        await ctx.send(file=f)


class Bot(commands.Bot):
    def __init__(self, intents):
        act = discord.Game('Jogos Mortais')
        super().__init__(command_prefix='/',
                         description='Bot Taleon san death search',
                         intents=intents,
                         activity=act)

    async def on_ready(self):
        await self.add_cog(DeathCog(self), override=True)


intents = discord.Intents.all()
intents.message_content = True
bot = Bot(intents)

bot.run(TOKEN)
