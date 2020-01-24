# Gender Tracker: Active Learning

## Installation

The application was setup by following this tutorial:
https://medium.com/@rodrigosmaniotto/integrating-django-and-vuejs-with-vue-cli-3-and-webpack-loader-145c3b98501a

npm and conda need to be installed.

PostgreSQL was setup by following parts of this tutorial:
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
pipenv install  # this line and the next need only to be run once on your computer
ansible-galaxy install -r requirements.yml
pipenv shell
make
```

## Code organisation

### Backend

The backend uses the Django framework. The `activelearning` package contains all code relating to Django settings
and administration. The `backend` package contains the model for the labelled data.

#### frontend_parsing package

Contains all methods that are used to transform information stored in the PostgreSQL data into a format that can be
shown to the user, as well as methods that transform the labels the user created into a format that can be added to the
database.

#### xml_parsing package

Contains all methods that can be used to transform news articles in an xml format into a representation that can be
stored in the PostgreSQL database. Each article needs to be stored in a seperate xml file, and have the following
format:

```xml
<?xml version="1.0"?>
<text>
	<title>Title of the article.</title>
	<p>Content of the first paragraph.</p>
	<p>Content of the second paragraph.</p>
	<p>...</p>
	<p>Content of the last paragraph.</p>
</text>
```

This package also contains methods to extract annotated articles to xml files, with the format:

```xml
<?xml version="1.0"?>
<text>
	<title>Title of the article.</title>
	<p>This is a short article, written by <author a="1">Albert Einstein</author>. <author a="1">Einstein</author>
            once said "<RS a="1">everything is relative</RS>".</p>
	<p>His friend, <author a="2">Isaac Newton</author>, did not believe him. He told him that "<RS a="2">if everything
            is relative, why does it hurt so much when apples fall?</RS>". He answered that <RS a="1">it doesn't hurt much compared
            to coconuts falling on your head.</RS></p>
</text>
```
