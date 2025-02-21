#!/usr/bin/env bash

# References:
# - http://docs.gunicorn.org/en/stable/settings.html#worker-class
# - http://docs.gunicorn.org/en/stable/settings.html#access-log-format

gunicorn server:app \
 --bind 0.0.0.0:5000 \
 --backlog 100 \
 --workers 2 \
 --threads 10 \
 --worker-class gevent \
 --access-logfile '-' \
 --access-logformat "{\"remote_ip\": \"%(h)s\", \"user_name\": \"%(u)s\", \"requested_time\": \"%(t)s\", \"request_method\": \"%(m)s\", \"request_path\": \"%(U)s\", \"request_querystring\": \"%(q)s\", \"response_code\": \"%(s)s\", \"referer\": \"%(f)s\", \"service_host\": \"%({host}i)s\", \"user_agent\": \"%(a)s\", \"request_timetaken\": \"%(D)s\", \"response_length\": \"%(b)s\", \"message\": \"%(h)s %(l)s %(u)s %(t)s '%(r)s' %(s)s %(b)s '%(f)s' '%(a)s' %({host}i)s %(D)s\"}"
