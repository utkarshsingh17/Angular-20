podman run -d --name connect `
  --network debezium-net `
  -e "BOOTSTRAP_SERVERS=host.containers.internal:9092" `
  -e "GROUP_ID=1" `
  -e "CONFIG_STORAGE_TOPIC=my_connect_configs" `
  -e "OFFSET_STORAGE_TOPIC=my_connect_offsets" `
  -e "STATUS_STORAGE_TOPIC=my_connect_statuses" `
  -e "KEY_CONVERTER=org.apache.kafka.connect.json.JsonConverter" `
  -e "VALUE_CONVERTER=org.apache.kafka.connect.json.JsonConverter" `
  -e "VALUE_CONVERTER_SCHEMAS_ENABLE=false" `
  -e "KEY_CONVERTER_SCHEMAS_ENABLE=false" `
  -p 8083:8083 `
  quay.io/debezium/connect:2.7
