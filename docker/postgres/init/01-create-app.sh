#!/bin/sh
set -eu

psql --username "$POSTGRES_USER" --dbname postgres \
  --set=app_user="$LEARNAI_DB_USER" \
  --set=app_password="$LEARNAI_DB_PASSWORD" \
  --set=app_db="$LEARNAI_DB_NAME" <<'SQL'
CREATE ROLE :"app_user" LOGIN PASSWORD :'app_password' NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT;
CREATE DATABASE :"app_db" OWNER :"app_user";
SQL

psql --username "$POSTGRES_USER" --dbname "$LEARNAI_DB_NAME" <<'SQL'
CREATE EXTENSION IF NOT EXISTS vector;
SQL
