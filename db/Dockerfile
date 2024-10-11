FROM postgres

COPY .env .

COPY 00_init.sql /docker-entrypoint-initdb.d/
