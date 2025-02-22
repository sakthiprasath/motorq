

1. create a virtual env ```python3.9 -m venv motorq_venv```
2. install the requirements using
``` pip install -r requirements.txt```
3. If we want to run as docker container, follow the below commands.
4. To pull a psotgres:13 docker image  and run it like the below one
  ```  
    docker run -d \
      --name postgres_db \
      -e POSTGRES_USER=postgres \
      -e POSTGRES_PASSWORD=postgres \
      -e POSTGRES_DB=test_db \
      -v postgres_data:/var/lib/postgresql/data \
      -p 5432:5432 \
      postgres:13
   ```
    
5. ```docker exec -it <postgres_image_tag> bash``` or 
    use ```psql -h localhost -U postgres``` to login to postgres cli and create around test_db.
6. Do ```\c test_db``` to connect to the ```test_db```
7. You can execute the sql statements in db => relations.sql
8. You can start the gunicorn server within the ```python venv``` created in ```step: 1,2```
9. Alternatively use this command to build the docker image ```docker build -t motorq_task .```
10. Use the below command to run the app in a docker container 
    ```
    docker run -e DB_NAME=test_db -e DB_USER=postgres -e DB_PASSWORD=postgres -e DB_HOST=localhost -e DB_PORT=5432 motorq_task
    ```
11. Please refer the ```notes.txt``` for ```kubernetes``` section
