{
  "name": "pg-weather-connector",
  "config": {
    "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
    "tasks.max": "1",
    "database.hostname": "postgres",
    "database.port": "5432",
    "database.user": "postgres",
    "database.password": "postgres",
    "database.dbname": "weather_db",
    "database.server.name": "pgserver1",
    "schema.include.list": "public",
    "table.include.list": "public.weather_readings",
    "slot.name": "weather_slot",
    "publication.name": "weather_pub",
    "plugin.name": "pgoutput"
  }
}
