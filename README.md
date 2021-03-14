This is a django-based web-application run in a docker environment. The application uses postgreSQL as a database system.

To run application:
 - navigate to the folder containing the docker file and run 'docker-compose build' then run docker-compose up.

Use "python manage.py makemigration" and "python manage.py migrate" to sync the database.