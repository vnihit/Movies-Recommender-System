Developed by - Nihit Vyas, Steven Phaedonos

## Running the project
1. Ensure that the [first-time setup](#first-time-setup) steps have been performed
2. Run the project by executing `docker-compose up`
3. Access the application via http://localhost:3000

## First-time setup
1. In a terminal (root directory of the project as working directory) run the following:
    - `docker-compose build`
    - `docker-compose up`
2. In another terminal, run the following:
    - `docker-compose images` (record the name of the container for the backend - e.g. "comp9321_ass3_backend_1")
    - `docker exec -it BACKEND_CONTAINER_NAME sh` 
    - `python manage.py migrate`
    - `python manage.py makemigrations movies`
    - `python manage.py migrate movies`
    - `python manage.py collectstatic`
3. Download [the movies dataset](https://www.kaggle.com/rounakbanik/the-movies-dataset)
4. Place the downloaded .csv files in the `backend/seed/` directory (folder may need to be created)
5. Navigate to http://localhost:8000/movies/bulk_create/
6. Setup is done once this completes (track the progress in the terminal which is running docker-compose)
