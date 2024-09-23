#!/lastdeath/env/bin/python
#
# Script que parseia toda deaths.php do taleon e salva no banco de dados
#
# Version 1.1 - adicionado caracters - e ' no regex dos monstros que mataram o personagem
# Version 1.2 - as mortes agora são salvas no banco de dados, outro programa agora será
# responsável por enviar as mortes no discord. Level mínimo retirado.
# Version 1.3 - adicionado headers nas requisições, o website está bloqueando com o header padrão da lib requests
#
# Author: Franklin

import re
import logging
from os import getenv, environ
import requests
from bs4 import BeautifulSoup
import time
from dotenv import load_dotenv
from datetime import datetime
from math import log, floor
from models import db, Death

load_dotenv()

db_filename = getenv('DATABASE_PATH')
db.bind('sqlite', filename=db_filename)
db.generate_mapping()

environ['TZ'] = 'America/Sao_Paulo'
time.tzset()

HEADERS = {
  'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0'
}
GUILDSCHANNELS = getenv('GUILDSCHANNELS').split(';')# valores de guild,channel 12,34;55,78

def human_format(number):
    units = ['', 'K', 'KK', 'KKK', 'T', 'P']
    k = 1000.0
    magnitude = int(floor(log(number, k)))
    return '%.2f%s' % (number / k**magnitude, units[magnitude])
    
def exp_loss(level):
    """ Possivel exp perdida na morte"""
    from math import pow
    level = int(level)
    exploss = ((level + 50) / 100) * 50 * (pow(level,2) - 5 * level + 8)
    exploss = exploss - (exploss * 0.7)
    exploss = human_format(exploss)
    return exploss

    
logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)

URL = "https://san.taleon.online/deaths.php"
page_deaths = requests.get(URL, headers=HEADERS)

soup = BeautifulSoup(page_deaths.content, "html.parser")
table_deaths = soup.find(id="deathsTable")

REGX_LEVEL = re.compile("[0-9.]+")
REGX_DIEDFOR = re.compile(r"by[\w '-]+")
REGX_SPLIT = re.compile(r" and a[n]? ")

# primeira TR é o header não valido para nosso scraping
for deaths in table_deaths.find_all("tr")[1:]:
  name, desc, timedeath = deaths.children
  name = name.text
  desc = desc.text
  # filtra apenas o nome, monstro, e data
  level = REGX_LEVEL.search(desc).group().replace(".","") # obtem o grupo encontrado, nesse caso o level numérico 
  died_for_monsters = REGX_DIEDFOR.search(desc).group().removeprefix("by an ").removeprefix("by a ").removeprefix("by ")
  died_for_monsters = REGX_SPLIT.split(died_for_monsters)
  
  timedeath = datetime.strptime(timedeath.text, "%d %b %Y, %H:%M")
  logger.debug("P> %s Lv> %s Hour> %s Monsters> %s" %(name, level, timedeath, died_for_monsters))
  
  # salva no banco de dados
  logger.debug('time atual: %s | time death: %s' %(time.time(), timedeath))
  Death.insert(name, level, timedeath, died_for_monsters)

