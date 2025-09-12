name=mysql-connector-local
connector.class=io.debezium.connector.mysql.MySqlConnector
tasks.max=1

database.hostname=localhost
database.port=3306
database.user=debezium
database.password=dbz_passwd

database.server.id=184054
database.server.name=mysql_local

database.include.list=your_source_db
table.include.list=your_source_db.playerinfo,your_source_db.venuedetails

include.schema.changes=true

# history storage
database.history=io.debezium.relational.history.FileDatabaseHistory
database.history.file.filename=C:/kafka/dbhistory-mysql.dat

snapshot.mode=initial
snapshot.locking.mode=none
