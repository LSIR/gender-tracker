The application was setup by following this tutorial:
https://medium.com/@rodrigosmaniotto/integrating-django-and-vuejs-with-vue-cli-3-and-webpack-loader-145c3b98501a

npm and conda need to be installed.

PostgreSQL was setup by foolowing parts of this tutorial:
https://medium.com/agatha-codes/painless-postgresql-django-d4f03364989

PostgreSQL needs to be installed

To setup your conda environment run:

```conda env create -f environment.yml -n gender-tracker```

Activate it:

```conda activate gender-tracker```

Create a PostgreSQL database

Create a .env file in the activelearning folder

```touch .env```

Add 3 lines to the .env file, containing the name of your database, your username and your password

    DB_NAME=name_of_your_db
    DB_USER=your_username
    DB_password=your_password


Create the database tables:

```python manage.py migrate```

Create your user:

```python manage.py createsuperuser```

(In another shell) build the frontend:

```cd frontend && npm install && npm run serve```

Start the application server

```python manage.py runserver``` 

To build and push the backend production container:

```make build && make push```

For the frontend:

```
cd frontend
make build && make push
```

To deploy the containers to production:

First add the following in your `.ssh/config`

```
Host gendertracker
    HostName 185.181.160.137
    User ubuntu
```

Then go the folder `ansible` at the root of this repository, and run

```
pipenv shell
make
```

