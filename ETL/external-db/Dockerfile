FROM postgres:14

ENV POSTGRES_USER=dbuser
ENV POSTGRES_PASSWORD=dbpassword
ENV POSTGRES_DB=storage_database

EXPOSE 5432

COPY ddls/storage_database.sql /docker-entrypoint-initdb.d/
