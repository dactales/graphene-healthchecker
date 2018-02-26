# BitShares Backend Healthchecking

* **bitshares-backend-health.py**: This is the main script that performs
  the health checks on requests received through HTTP

* **bitshares-backend-health.service**: This is a systemd service that
  keeps the health checker running

## Running Health Check

```
Usage: bitshares-backend-health.py [OPTIONS] URL

Options:
  --listen INTEGER
  --help            Show this message and exit.
```

**Example**:

```
bitshares-backend-health.py --listen 8080 wss://node.bitshares.eu
```

## Health Check

1. Check if a connection can be established to the backend node. 
   (Raise HTTP/502 if not.)
2. Check that the returned answer from the backend has status code 200.
   (Raise HTTP/502 if not.)
3. Check if the answer has a "result" key in its json representation.
   (Raise HTTP/502 if not.)
4. Obtain the time of the most recent block as well as the next
   maintenance time
5. Check that current head time is less than 60 seconds old and next
   maintenance interval is more than 10 seconds in the future.
   (Raise HTTP/502 if not.)
