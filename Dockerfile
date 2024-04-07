# usar imagem mais recente do Debian
FROM debian:latest
WORKDIR /lasdeath

# Instalando os pacotes necessários, incluindo cron, openssh-client, rsync, sqlite3, e as ferramentas Python
RUN apt-get update && \
    apt-get install -y cron openssh-client python3-pip python3.11-venv python3 rsync sqlite3 && \
    python3 -m pip install --upgrade pip && \
    rm -rf /var/lib/apt/lists/*

# cria o ambiente virtual python
RUN python3 -m venv env

# ativa o ambiente virtual env
ENV PATH="/lastdeath/env/bin:$PATH"

# copia o arquivo de modulos necessários para o workdir
COPY requirements.txt .

# instala as dependências necessárias
RUN pip install -r requirements.txt

# copia os arquivos locais para o workdir
COPY . .

# copia o entrypoint para o diretório ideal.
# o entry point é apenas para garantir que o crontab inicialize sempre
# e após isso execute o bot
COPY ENTRYPOINT.SH /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# configura os volumes
#  - ssh: chave ssh para sincronizar o banco de dados e arquivos dos bosses
#  - database: vincula o database presente do host para dentro do container
VOLUME ["/DATA/configs/lastdeathbot/ssh:/root/.ssh", "/DATA/configs/lastdeathbot/deaths-database.sqlite:/lastdeath/deaths-database.sqlite"]

# explicita qual arquivo inicializar após o container subir
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]