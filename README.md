This is a django-based web-application run in a docker environment. The application uses postgreSQL as a database system.

To run application:
 - navigate to the folder containing the dockerfile and run 'docker-compose build'
 - run 'docker-compose up' to start the containers
 - when running, use 'docker-compose exec web python manage.py makemigrations' to register changes in models.py
 - afterwards, use 'docker-compose exec web python manage.py migrate' to migrate these changes to the database
 - if none exist, use 'docker-compose exec web manage.py createsuperuser' to register an admin that can use the localhost:8000/admin site
 - you can then use the admin site to add other users -- note that a username must be a positive integer, as it doubles as the tenancy_id in the Tenancy table

For benchmarking, a file named 'tests.py' is included in the InvoiceEngineApp. This file contains the following functions:
- generate_benchmark_data(max_components) to fill the database with 100000 contracts.
- clear_database() to remove everything(!) from the database in a quick manner
- clear_invoices() to remove all invoices from the database so that run_invoice_engine can be used again without having to generate new benchmarking data
- run_invoice_engine() to measure the speed of the invoicing process

Run these functions in the web container from the manage.py shell: 

'docker-compose exec python manage.py shell'

In the shell, run the following commands:
- import InvoiceEngineApp.tests as tests
- tests.function_name(arg)
- exit() when you're done

Do note that if you make changes to tests.py, you have to restart the manage.py shell.