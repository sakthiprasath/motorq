

1. create a virtual env ```python3.9 -m venv motorq_venv```
2. install the requirements using
``` pip install -r requirements.txt```
3. 
4. If we want to run as docker container, follow the below commands

```
docker build -t motorq_task .

docker run -d \
  --name postgres_db \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=test_db \
  -v postgres_data:/var/lib/postgresql/data \
  -p 5432:5432 \
  postgres:13

docker run -e DB_NAME=test_db -e DB_USER=postgres -e DB_PASSWORD=postgres -e DB_HOST=localhost -e DB_PORT=5432 motorq_task

```
