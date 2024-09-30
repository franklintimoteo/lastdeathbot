echo "Backup db"
/lastdeath/backupdb.py

echo "rsync database"
rsync -e "ssh -o StrictHostKeyChecking=no" -arvc /tmp/backup.db ovh:/home/debian/lastdeath/deaths-database.sqlite
