#!/lastdeath/env/bin/python
# Script para fazer o backup do banco de dados
# funciona mesmo com clientes acessando
#
# Author: Franklin

from os import getenv
from dotenv import load_dotenv
import sqlite3

load_dotenv()

db_source_filename = getenv('DATABASE_PATH')
def progress(status, remaining, total):
    print(f'Copied {total-remaining} of {total} pages...')

src = sqlite3.connect(db_source_filename)
dst = sqlite3.connect('/tmp/backup.db')
with dst:
    src.backup(dst, pages=1, progress=progress)

dst.close()
src.close()
