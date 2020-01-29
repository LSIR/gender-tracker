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

## Data

Each article needs to be stored in a seperate xml file, and have the following
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

A single article can be added to the database from by running:

```python manage.py addarticle path/to/the/article.xml```

In order to add all articles in a directory to the database, run:

```python manage.py addarticle path/to/the/article/directory```

Once a article has been fully labeled, it can be exported with annotations in the following format.

```xml
<?xml version="1.0"?>
<text>
	<title>Title of the article.</title>
	<p>This is a short article, written by <author a="1">Albert Einstein</author>.
        <author a="1">Einstein</author> once said "<RS a="1">everything is
        relative</RS>".</p>
	<p>His friend, <author a="2">Isaac Newton</author>, did not believe him.
        He told him that "<RS a="2">if everything is relative, why does it
        hurt so much when apples fall?</RS>". He answered that <RS a="1">it
        doesn't hurt much compared to coconuts falling on your head.</RS></p>
</text>
```

## Use of the Active Learning Platform

The active learning platform is used to generate labeled sentences for quote extraction and attribution. The user is
presented sentences, that he has to either label as containing reported speech or containing no reported speech.

If the sentence contains reported speech, the user needs to select the first and last word, as well as the name of the
person who is quoted. As the author of the quote might be in a different sentence than the reported speech, the user
can load the text above and below the reported speech.

## Implementation

### Databases

Articles are represented by a database containing the following fields:

* _id_: A unique identifier for each article.
* _name_: The article name.
* _text_: The xml file in the form of a string.
* _people_: A list of names found in the article.
* _tokens_: The content in the article, as a list of tokens. The tokens are obtained using spaCy's french model.
* _sentences_: A list, sorted in ascending order, of the indices of tokens that are the last in a sentence.
* _paragraphs_: A list, sorted in ascending order, of the indices of sentences that are the last in a paragraph.
* _label_counts_: A list containing the number of user labels for each sentence.
* _label_overlap_: A list containing the percentage of user labels that "agree" (have the same labels) for a sentence.
* _confidence_: A list containing how confident the model is on whether or not each sentence contains reported speech.

User labels are represented in the database with the following fields:
   
* _article_: The article to which this label is attached.
* _sentence_index_: The sentence in the article to which this label is attached.
* _session_id_: The id of the user that created the labels for the sentence.
* _labels_: The label for each word in the sentence.
* _author_index_: The index of the name of the person quoted, if the sentence contains reported speech.
* _admin_label: If the user who created the label is one of the administrators.

### Backend

The backend keeps track of all articles and user labels. An article is considered fully labeled if all of its sentences
are fully labeled. A sentence is fully labeled if:

- There are at least COUNT_THRESHOLD user labels and the consensus between labels is at least CONSENSUS_THRESHOLD.
- Or there is an admin label for the sentence.

We set COUNT_THRESHOLD = 4 and CONSENSUS_THRESHOLD = 75%.

There are two separate ways that user labels are created. The first is the most obvious one, where sentences are
labelled one by one. In order to make labelling faster, users can also be asked to confirm that there is no reported 
speech in a whole paragraph. This happens when the model is confident enough that no reported speech is present in the
whole paragraph. If the user confirms that no reported speech is present, a user label is added to the database for each
sentence in the paragraph. If the user reports that a quote is in the paragraph, the confidence for each sentence in the
paragraph is set to 0, and each sentence is annotated one by one. 

In order to improve the model with as little data as possible, we want to obtain labels for sentences where the model is
most uncertain. In order to have a consistent database, with articles being either fully labeled, currently being
labelled or not labelled at all, we choose the next sentence to be annotated as the first unlabelled sentence in the
article containing the sentence for which the model is the most uncertain.

The backend has four methods in it's API.

* _Load Content_: This method is used to load the next sentence (or paragraph) that needs to be labelled. It returns a
Json file as content, which contains the following keys:
    * 'article_id': the unique ID of the article being labeled.
    * 'sentence_id': a list containing the indices in the article of the sentences to label.
    * 'data': a list containing the sentence, separated into tokens (~words).
    * 'task': either 'sentence' or paragraph, depending on whether or not a full paragraph is being annotated at once.
    This task also reports errors.
* _Load Above_: This method is used to load the text above a given sentence. This is useful when reported speech is in the
sentence, but the person who said this reported speech doesn't have their name in that sentence. By loading the text
above, the user can check (and select) if their name is there. This must be called with a GET request, with parameters 
'article_id' (the id of the article already loaded in the frontend) and 'first_sentence' (the index of the first 
sentence already loaded in the frontend). It returns a data in a Json format, containing the keys:
    * 'Success': If this value is true, then the data also has the keys:
        * 'data': A list of all tokens in the newly loaded text.
        * 'first_sentence': The index of the first sentence that is loaded.
        * 'last_sentence': The index of the last sentence that is loaded.
    * 'reason': If success is false, this indicates why.
* _Load Below_: This method is used to load the text below a given sentence. As for Load Above, this is useful when
reported speech is in the sentence, but the person who said this reported speech doesn't have their name in it. This
must be called with a GET request, with parameters  'article_id' (the id of the article already loaded in the frontend)
and 'last_sentence' (the index of the last sentence already loaded in the frontend). It returns a data in a Json format,
containing the keys:
    * 'Success': If this value is true, then the data also has the keys:
        * 'data': A list of all tokens in the newly loaded text.
        * 'first_sentence': The index of the first sentence that is loaded.
        * 'last_sentence': The index of the last sentence that is loaded.
    * 'reason': If success is false, this indicates why.
* _Load Below_: This method is used to load the text below a given sentence. As for Load Above, this is useful when
reported speech is in the sentence, but the person who said this reported speech doesn't have their name in it. This
must be called with a GET request, with parameters  'article_id' (the id of the article already loaded in the frontend)
and 'last_sentence' (the index of the last sentence already loaded in the frontend). It returns a data in a Json format,
containing the keys:
    * 'Success': If this value is true, then the data also has the keys:
        * 'data': A list of all tokens in the newly loaded text.
        * 'first_sentence': The index of the first sentence that is loaded.
        * 'last_sentence': The index of the last sentence that is loaded.
    * 'reason': If success is false, this indicates why.
* _Submit Tags_: This is a POST request. It should be called when the user has finished labeling the sentence. It should
have as a request body a Json file with the following information:
    * 'article_id': The id of the article that was labelled
    * 'sentence_id': The list of sentence indices that were labelled (only the original sentence indices, not the
    indices of text that was loaded above or below).
    * 'first_sentence': The smallest sentence index that was shown to the user (the smallest index of sentences loaded,
    including sentences loaded with the Load Above call).
    * 'last_sentence': The largest sentence index that was shown to the user (the largest index of sentences loaded,
    including sentences loaded with the Load Below call).
    * 'labels': The labels created by the user. This is a list of values, where each entry is 0 if the corresponding
    token is inside reported speech, and 0 if it isn't. Only one piece of reported speech can be included, which is a
    single continuous block of tokens.
    * 'authors': The list of indices of the name of the person that said the quote in the loaded text. This means that
    if the first token in the loaded text is the name, then [0] is returned.
    * 'task': The task the user was doing ('sentence' or 'paragraph').
    
### Frontend



## Code

### Backend

The backend uses the Django framework. The `activelearning` package contains all code relating to Django settings
and administration. The `backend` package contains the model for the labelled data.

#### frontend_parsing package

Contains all methods that are used to transform information stored in the PostgreSQL data into a format that can be
shown to the user, as well as methods that transform the labels the user created into a format that can be added to the
database.

#### xml_parsing package

Contains all methods that can be used to transform news articles in an xml format into a representation that can be
stored in the PostgreSQL database. This package also contains methods to extract annotated articles to xml files, with the format:

### Frontend

The frontend is implemented with the VueJS framework.
