from datetime import datetime, timedelta, date
from calendar import monthrange
from pony.orm import *


db = Database()
@db.on_connect(provider='sqlite')
def sqlite_case_sensitivity(db, connection):
    cursor = connection.cursor()
    cursor.execute("PRAGMA foreign_keys = OFF")
    
# select level, Player.name, time, Death_monster.monster from Death inner join Player on Death.player = player.id inner join Death_monster on Death.id = Death_monster.death where time > '2023-09-21' order by Player;

# select level, Player.name, time, group_concat(Monster.name) from Death inner join Player on Death.player = player.id inner join Death_monster on Death.id = Death_monster.death inner join Monster on Death_Monster.monster = Monster.id where time >= '2023-09-21' group by Player;

# select level, Player.name, time, group_concat(Monster.name) from Death inner join Player on Death.player = player.id inner join Death_monster on Death.id = Death_monster.death inner join Monster on Death_Monster.monster = Monster.id where time >= '2023-09-21' group by Player,time;

# pegar somente as mortes dos membros da guild
# select time,player.name, group_concat(monster.name) from death inner join Death_Monster on death_monster.death = death.id inner join Monster on Death_monster.monster = monster.id inner join player on death.player = player.id where death.player = (select player from experience where death.player = player) group by time,player;

class Death(db.Entity):
    id = PrimaryKey(int, auto=True)
    player = Required('Player')
    level = Optional(int)
    time = Optional(datetime)
    monsters = Set('Monster')
    sent = Optional(bool)

    @staticmethod
    @db_session
    def insert(player, level, time, monsters):
        """
        player: str
        level: int
        time: datetime
        monsters: [str]
        """
        p = Player.create_get_player(player)
        m = Monster.create_get_monsters(monsters)
        level = int(level)
        died = Death.select(lambda x: x.player == p and x.time == time and x.level == level)

        if not died.exists():
            Death(
                player=p,
                level=level,
                time=time,
                monsters=m
            )


class Monster(db.Entity):
    id = PrimaryKey(int, auto=True)
    name = Optional(str)
    deaths = Set(Death)

    @staticmethod
    @db_session
    def create_get_monsters(monsters=[]):
        """
        monsters: ['Dwarf Guard', 'Dwarf', ...]

        Cria uma lista de monstros e retorna as instâncias deles
        """
        if not isinstance(monsters, list):
            raise TypeError(f'monsters must be list not {type(monsters)}')

        monsters_obj = []
        for m in monsters:
            if not Monster.exists(name=m):
                Monster(name=m)
            monsters_obj.append(Monster.get(name=m))

        return monsters_obj
        

class Player(db.Entity):
    id = PrimaryKey(int, auto=True)
    name = Optional(str)
    deaths = Set(Death)
    experiences = Set('Experience')

    @staticmethod
    @db_session
    def create_get_player(name):
        """
        name: str

        Cria o player se não existir
        e retorna a instẫncia com o jogador criado
        """
        if not Player.exists(name=name):
            Player(name=name)

        return Player.get(name=name)


class Experience(db.Entity):
    id = PrimaryKey(int, auto=True)
    date = Optional(datetime)
    amount = Optional(int)
    player = Required(Player)
    level = Optional(int)  # level atual no dia que foi registrado a exp

    @staticmethod
    @db_session
    def insert(date, amount, player, level):
        """
        date: datetime
        amount: int
        player: str
        level: int

        Registra a experience junto com o level atual do jogador
        """
        player = Player.create_get_player(player)
     
        inserted = Experience.select(lambda e: e.player == player
                                     # compara somente dia, mes e ano
                                     and e.date.date() == date.date() 
                                     and e.amount == amount
                                     and e.level == level)

        if not inserted.exists():
            Experience(
                date=date,
                amount=amount,
                player=player,
                level=level
            )


# graphs
@db_session
def max_level_died(delta):
    """max level dead player in last week
    """
    delta = datetime.date(datetime.now()) - delta
    result = db.select("select max(level),time,name from death inner join player where player.id = death.player and death.time >= $delta;")

    return result


@db_session
def top_10_dead_players(delta):
    """top 10 player who died the most in the last delta
    """
    delta = datetime.date(datetime.now()) - delta
    result = db.select("select count(player),name from death inner join player on death.player = player.id and death.time >= $delta group by player order by count(player) desc limit 10")

    return result


@db_session
def top_10_dead_players_guild(delta):
    """
    top 10 players who died the most in the last delta from guild
    """
    delta = datetime.date(datetime.now()) - delta
    result = db.select("select count(player),name from death inner join player on death.player = player.id where death.player= (select player from experience where death.player = player) and death.time >= $delta group by player order by count(player) desc limit 10")

    return result

@db_session
def monster_most_kill(delta):
    """top 10 monster that killed the most player in the last week
    """
    delta = datetime.date(datetime.now()) - delta
    result = db.select("select count(monster),name from death_monster inner join monster on monster.id = death_monster.monster inner join death on death_monster.death = death.id where time >= $delta group by monster order by count(monster) desc limit 10;")

    return result

@db_session
def rank_exp_guild(delta):
    """rank experience guild members
    """
    delta = datetime.date(datetime.now()) - delta
    result = db.select("select name, sum(amount), min(level), max(level),max(level)-min(level) from Experience inner join player on experience.player = player.id where date >= $delta group by player order by sum(amount) desc;")

    return result


@db_session
def rank_exp_month(d1, d2):
    """rank experience guild member between d1 and d2 month
    """
    result = db.select("select name, sum(amount), min(level), max(level), max(level)-min(level) from Experience inner join player on experience.player = player.id where date >= $d1 and date <= $d2 group by player order by sum(amount) desc;")

    return result


@db_session
def get_last_dead(delta, level):
    """Obtem as últimas mortes levando em conta os segundos
    """
    delta = datetime.now() - delta
    result = db.select("select death.id, level, Player.name, group_concat(Monster.name) from Death inner join Player on Death.player = player.id inner join Death_monster on Death.id = Death_monster.death inner join Monster on Death_Monster.monster = Monster.id where time >= $delta and level >= $level and sent is null group by Player,time;")

    return result


@db_session
def confirm_sent(deathsid):
    """
    deathsid: [int]
    Set true boolean sent in Death
    """
    deathsid = tuple(deathsid)
    if len(deathsid) == 1:
        # caso so tenha um valor, o execute buga por conta do virgula
        # na tupla (123,)
        deathsid = f'({deathsid[0]})'

    result = db.execute(f"update Death set sent=True where id in {deathsid}")

    return result

@db_session
def insert_achievements(player_name, achievements):
    """
    Insere os achievements no player caso hajam achievements
    """
    if not achievements:
        return
    
    player = Player.create_get_player(player_name)

    player_achievs = []
    for achiev in achievements:
        achi_id = db.select("select id from achievement where name = $achiev COLLATE NOCASE")
        if not achi_id:
            print("Achievment", achiev, "não existe na tabela de referência. Favor atualizar tabela Achievement.")
            continue
        player_achievs.append((player.id, achi_id[0]))

    for player_id, achiev in player_achievs:
        db.execute("INSERT OR IGNORE INTO Achievement_Player(Player, Achievement) VALUES ($player_id, $achiev);")


@db_session
def update_outfit_url(player, url):
    player = Player.create_get_player(player).id
    db.execute("UPDATE PLAYER SET outfit = $url WHERE id = $player;")


@db_session
def insert_banned(player, level, timeban):
    player = Player.create_get_player(player).id
    db.execute("INSERT OR IGNORE INTO Players_Banned(Player, Level, Timeban) VALUES ($player, $level, $timeban);")


@db_session
def ban_confirm_sent(bans_ids):
    "bans_id: [int]"
    bans_ids = tuple(bans_ids)
    if len(bans_ids) == 1:
        bans_ids = f'({bans_ids[0]})'

    result = db.execute(f"update Players_Banned set sent=True where id in {bans_ids}")

    return result
