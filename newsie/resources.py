from dagster import resource, Field, String, InitResourceContext, EnvVar
import psycopg


@resource
def postgres_resource(context: InitResourceContext):
    host = EnvVar('PG_DB_HOST').get_value()
    username = EnvVar('PG_DB_USERNAME').get_value()
    password = EnvVar('PG_DB_URL').get_value()
    dbname = EnvVar('PG_DB_NAME').get_value()

    # Establish a connection to the database
    connection = psycopg.connect(
        host=host,
        user=username,
        password=password,
        dbname=dbname
    )

    yield connection

    connection.close()
