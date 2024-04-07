#!/lastdeath/env/bin/python
# Script para parsear a experience de todos membros da guild Bolados
#
# Version 1.1 - obtem todos membros e parseia as experiences do dia anterior
# Version 1.2 - adicionado headers nas requisições, o website está bloqueando com o header padrão da lib requests
# 
# Author: Franklin

import re
import logging
import time
from os import getenv
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from models import Experience, db, insert_achievements, update_outfit_url

load_dotenv()

db_filename = getenv('DATABASE_PATH')
db.bind('sqlite', filename=db_filename)
db.generate_mapping()

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)

HEADERS = {
  'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0'
}
URL_PLAYER = "https://san.taleon.online/characterprofile.php?name="
URL = "https://san.taleon.online/guilds.php?name=Os%20Bolados"
page_guild = requests.get(URL, headers=HEADERS)

soup = BeautifulSoup(page_guild.content, "lxml")
table_guild = soup.find(class_="table table-striped")

# obtem o nome do jogador sem apelido de guild
REGX_NAME = re.compile(r"^[\w ]+")
members_guild = []
for member in table_guild.find_all("tr")[1:]:
    rank, name, *status_and_level = member.children
    name = name.text.strip()
    name = REGX_NAME.search(name).group().strip()
    members_guild.append(name)

# atrasa a busca pois o site do taleon só permite 15 requisições
# por minuto. Limitei para 9, pois deixa espaço para outros scripts
# também fazerem buscas no site
SLEEP_TIME = 60 / 9

for member in members_guild:
    level = 0

    try:
        r = requests.get(URL_PLAYER + member, headers=HEADERS)
        soup = BeautifulSoup(r.content, "lxml")
        soup = soup.find(class_="tab_table table table-striped table-condensed")
        
        # get level
        soup_level = BeautifulSoup(r.content, "lxml")
        soup_level = soup_level.find(class_="table table-striped table-condensed")
        level = soup_level.find(string="Level: ")
        level = level.find_next('td').text
        level = int(level)

        # obtem os achievements do jogador
        soup_achiev = BeautifulSoup(r.content, "lxml")
        achievements = []
        for tag in soup_achiev.find("tbody", class_="ach").tr.next_siblings:
            text = tag.get_text()
            text = re.sub('\n|[[\d+\]]', '', text)
            
            if not text:
                continue
            achievements.append(text)

        # obtem a url do achiev
        soup_outfit = BeautifulSoup(r.content, "lxml")
        url_outfit = soup_outfit.find('img', class_='outfitImgTable').attrs.get('src')
        url_outfit = url_outfit.replace('outfit.php', 'animoutfit.php')
        
    except Exception as e:
        logger.debug(f"Error get member {member} {e}")
        time.sleep(SLEEP_TIME)
        continue
    
    # faz um parse somente do dia anterior
    for e in soup.find_all('tr')[2:3]: 
        date, experience = e.children
        delta = timedelta(days=1)
        date = datetime.now() - delta
        
        if experience.text.startswith("No experience"):
            experience = 0
        else:
            experience = int(experience.text.replace(',', ''))

        
        # salva no banco de dados
        #Experience.insert(date, experience, member, level)
    # atualiza o outift
    update_outfit_url(member, url_outfit)
    # Atualiza os achievements do jogador
    insert_achievements(member, achievements)
    #print('Atualizando achievement do membro', member, 'Achievements:', achievements)
    time.sleep(SLEEP_TIME)

