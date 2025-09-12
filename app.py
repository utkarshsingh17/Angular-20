# As an Intern
jdbc_url = "jdbc:mysql://localhost:3306/targetdb?useSSL=false&serverTimezone=UTC"
props = {"user": "root", "password": "vikumar8", "driver": "com.mysql.cj.jdbc.Driver"}

tables = [
    "playerinfo_dim", "venuedetails_dim", "teamdetails_fact",
    "matches_info_fact", "matches_info_dim",
    "odiformatstats_fact", "t20formatstats_fact", "testformatstats_fact",
    "playerstatspervenue_fact"
]

for t in tables:
    df = spark.read.jdbc(jdbc_url, t, properties=props)
    df.createOrReplaceTempView(t)   # now spark.sql can use the table name directly
