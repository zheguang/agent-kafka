#!/usr/bin/env python
import json

from datetime import datetime
from kafka import KafkaProducer

def generate_lineitems():
    producer = KafkaProducer(
        value_serializer=lambda m: json.dumps(m).encode("utf-8"), 
        bootstrap_servers=["localhost:9092"]
    )

    producer.send("lineitem", value={ 
            "timestamp": datetime.now().isoformat(), 
            "order_id": "o1",
            "part_id": "p1",
        } 
    )

    producer.send("lineitem", value={ 
            "timestamp": datetime.now().isoformat(), 
            "order_id": "o1",
            "part_id": "p2",
        } 
    )

    producer.send("lineitem", value={ 
            "timestamp": datetime.now().isoformat(), 
            "order_id": "o2",
            "part_id": "p1",
        } 
    )


if __name__ == "__main__":
    generate_lineitems()
