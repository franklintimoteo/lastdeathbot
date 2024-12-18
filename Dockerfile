# usar imagem mais recente do Debian
FROM debian:latest
WORKDIR /lastdeath

# Altera o timezone
ENV TZ="America/Sao_Paulo"

# Instalando os pacotes necessários, incluindo cron, openssh-client, rsync, sqlite3, e as ferramentas Python
RUN apt-get update && \
    apt-get install -y cron openssh-client python3-pip python3.11-venv python3 rsync sqlite3 && \
    rm -rf /var/lib/apt/lists/*

# cria o ambiente virtual python
RUN python3 -m venv /lastdeath/env

# ativa o ambiente virtual env
ENV PATH="/lastdeath/env/bin:$PATH"

# copia o arquivo de modulos necessários para o workdir
COPY requirements.txt .

# instala as dependências necessárias
RUN pip install -r requirements.txt

# copia os arquivos locais para o workdir
COPY . /lastdeath

COPY cron /etc/cron.d/lastdeath-cron
RUN ln -snf /usr/share/zoneinfo/America/Sao_Paulo /etc/localtime

RUN chmod 0644 /etc/cron.d/lastdeath-cron && \
    crontab /etc/cron.d/lastdeath-cron
 
# copia o entrypoint para o diretório ideal.
# o entry point é apenas para garantir que o crontab inicialize sempre
# e após isso execute o bot
COPY ENTRYPOINT.SH /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# garante que exista a pasta de configurações do ssh
RUN mkdir /root/.ssh

# configura os volumes
#  - ssh: chave ssh para sincronizar o banco de dados e arquivos dos bosses
#  - database: vincula o database presente do host para dentro do container
#  - .env: variaveis secretas de ambiente
#  - ssh_config: vincula o arquivo de ssh_config para não vazar os dados da vps que hospeda o site
# VOLUME ["/DATA/configs/lastdeathbot/deaths-database.sqlite:/lastdeath/deaths-database.sqlite",
# 	"/DATA/configs/lastdeathbot/.env:/lastdeath/.env",
# 	"/DATA/configs/lastdeathbot/ssh_config:/root/.ssh/config",
# 	"/DATA/configs/lastdeathbot/ovh_remote:/root/.ssh/ovh_remote",
# 	"/GALLERY:/GALLERY"]

# explicita qual arquivo inicializar após o container subir
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
