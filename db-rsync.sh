echo "Backup db"
/lastdeath/backupdb.py

echo "rsync database"
rsync /tmp/backup.db ovh:/home/debian/lastdeath/deaths-database.sqlite
