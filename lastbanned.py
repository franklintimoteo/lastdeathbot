#!/lastdeath/env/bin/python
#
# Author: Franklin

import re
import logging
import time
from datetime import datetime
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
from os import getenv, environ
from models import db, insert_banned

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

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)

URL = "https://san.taleon.online/banned.php"
page_bans = requests.get(URL, headers=HEADERS)

REGX_LEVEL = re.compile("[0-9.]+")
"🚫"

soup = BeautifulSoup(page_bans.content, "html.parser")
table_bans = soup.find(id="achivTable")

for ban in table_bans.find_all("tr")[1:]:
    name, level, timeban, *_ = ban.find_all("td")
    name = name.text
    level = int(level.text.replace(".", ""))
    timeban = datetime.strptime(timeban.text, "%d/%m/%Y %H:%M:%S")
    logger.debug("🚫 Name: %s | Level: %s | Timeban: %s" %(name, level, timeban))
    insert_banned(name, level, timeban)
