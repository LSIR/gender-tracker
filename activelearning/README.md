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

#### Articles

Articles are represented by a database containing the following fields:

* _id_:
    * integer
    * A unique identifier for each article.
* _name_: 
    * string (maximum 200 characters)
    * The article name.
* _text_:
    * string
    * The xml file in the form of a string.
* _people_:
    * json file
        * keys: {people: list(string)}
    * A list of names found in the article.
* _tokens_:
    * json file
        * keys: {tokens: list(string)}
    * The content in the article, as a list of tokens. The tokens are obtained using spaCy's french model.
* _sentences_:
    * json file
        * keys: {sentences: list(int)}
    * A list, sorted in ascending order, of the indices of tokens that are the last in a sentence.
* _paragraphs_:
    * json file
        * keys: {paragraphs: list(int)}
    * A list, sorted in ascending order, of the indices of sentences that are the last in a paragraph.
* _in_quotes_:
    * json file
        * keys: {in_quotes: list(int)}
    * An integer for each token in the article, describing if it's in between quotes (1) or not (0).
* _labeled_:
    * json file
        * keys: {labeled: list(int), fully_labeled: int}, optional keys: {test_set: list(int)}
    * The value of labeled is a list of integers for each sentence: 1 if the sentence has enough labels, 0 if it needs
    more.
    * The value of fully_labeled is an integer which is 1 if all sentences in the article are labeled, and 0 otherwise.
    * Fully labeled articles can have an optional key, test_set, which is a list of integers describing if each sentence
    is in the training set (0) or in the test set (1).
* _confidence_:
    * json file
        * keys: {confidence: list(int), min_confidence: int}
    * The confidence key has as a value a list containing how confident the model is on whether or not each sentence 
    contains reported speech.
    * The min_confidence key has as a value an integer containing the lowest confidence for the entire article.
* _admin_article_:
    * boolean
    * If the article text should only be shown to administrators.

#### User labels

User labels are represented in the database with the following fields:
   
* _article_:
    * Article
    * The article to which this label is attached.
* _sentence_index_:
    * string (maximum 50 characters)
    * The sentence in the article to which this label is attached.
* _session_id_:
    * integer
    * The id of the user that created the labels for the sentence.
* _labels_:
    * json file
        * keys: {labels: list(int)}
    * The label for each word in the sentence.
* _author_index_:
    * json file
        * keys: {author_index: list(int)}
    * The index of the name of the person quoted (can be multiple tokens), if the sentence contains reported speech.
* _admin_label_:
    * boolean
    * If the user who created the label is one of the administrators.

If a user wanted to skip as sentence as they weren't sure how to annotate it correctly, the label is added to the 
database with the correct article, sentence_index and session_id, but the labels are set to an empty list.

### Backend

The backend keeps track of all articles and user labels. There are two types of users that can add labels to sentences:
normal users and admin users. Admin users are simply users that are fully trusted, and hence for which a single label is 
enough to have a sentence be fully annotated. Selected users can become admin users by visiting the url: 

```{website_url}/api/admin_tagger?key=SECRET_KEY```

Where the secret key is given by the administrators of the site.

A sentence in an article is fully labeled if:
- There are enough user labels (at least COUNT_THRESHOLD) and the consensus between labels (the proportion of labels 
that agree on the contents of the sentence.) is large enough (at least CONSENSUS_THRESHOLD).
- Or there is an admin label for the sentence.
An article is considered fully labeled if all of its sentences are fully labeled.

We set COUNT_THRESHOLD = 4 and CONSENSUS_THRESHOLD = 75%.

There are two separate ways that user labels are created. The first is the most obvious one, where sentences are
labelled one by one. In order to make labelling faster, users can also be asked to confirm that there is no reported 
speech in a whole paragraph. This happens when the model is confident enough that no reported speech is present in any 
sentence in a paragraph. If the user confirms that no reported speech is present, a user label is added to the database
for each sentence in the paragraph. If the user reports that a quote is in the paragraph, the confidence for each
sentence in the paragraph is set to 0, and each sentence is annotated one by one. 

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
* _Load Above_: This method is used to load the text above a given sentence. This is useful when reported speech is in
the sentence, but the person who said this reported speech doesn't have their name in that sentence. By loading the text
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
    single continuous block of tokens. If the user didn't know how to annotate the sentence, an empty list should be
    returned.
    * 'authors': The list of indices of the name of the person that said the quote in the loaded text. This means that
    if the first token in the loaded text is the name, then [0] is returned. If the user didn't know how to annotate the
    sentence, an empty list should be returned.
    * 'task': The task the user was doing ('sentence' or 'paragraph').
    
### Frontend

The frontend loads content using the methods from the API and displays them to the user. 

#### Single sentence annotation:

It stores a list of tokens, loaded from the backend with the loadContent method, where the task returned was 'sentence'.
A list of the same length as the list of tokens is stored, which indicates if each token is inside reported speech (1)
or not (0). It's initially filled with 0s, which means no quote is in the displayed sentence.

To select reported speech, the user first clicks on the first token of the quote, and then the last. This sets all
indices in the boolean list between the two tokens to 1. Only one passage of reported speech per sentence can be 
selected.

To select which person said a quote, the user can click on any token shown once they are done selecting the first and
last token of the quote. The indices of these tokens in the token list are stored.

As some quotes last more than a single sentence, and sometimes the author of a quote is outside of the sentence where 
they are quoted, the user can load more text with the loadAbove and loadBelow methods. They can also tag text in the 
extra text loaded, but if they select a quote it must have at least one token in the original sentence.

The article id, the ids of the sentences that needed to be annotated, the list of labels the user created, the list of
author indices, as well as information on the extra sentences the user might have loaded are returned to the backend.

#### Paragraph annotation:

It stores a list of tokens, loaded from the backend with the loadContent method, where the task returned was 'paragraph'
. There are only two buttons: one to confirm that no reported speech is present (a list of 0s is returned), and one to
indicate that there was in fact reported speech (a list of 1s is returned).

### Machine Learning

There are two separate models needed to determine how many men and women are quoted in an article. The first model is
used to detect whether a sentence contains reported speech or not, and the second is used to determine which Named 
Entity is the author of the reported speech.

Different models for classification are tested, including Logistic Regression and SVMs.

Each sentence is assigned to the training set with probability 90% and the test set with probability 10%. This assigment 
is done for all sentences in a given article once it's fully labeled.

#### Quote detection

This model takes as input a sentence, and outputs a prediction as to whether or not the sentence contains a quote. The
first step of this process is performing feature extraction. The following features are extracted from the sentence:

* The length of the sentence.
* Whether it contains quotation marks.
* Whether it contains a named entity that is a person.
* Whether it contains a verb in the verb-cue list.
* Presence of a parataxis.
* Presence of multiple verbs.

These feature vectors are then passed through different models to be evaluated. As there are many more sentences that 
don't contain quotes than ones that do, the set of sentences containing quotes is subsampled so that there are about the
same number of sentences of both classes.

#### Speaker Extraction

This model takes as input a sentence and a list of named entities. It assigns a score between 0 and 1 to each named,
where a score closer to 1 means it's more likely to be the author of the reported speech, using a classification model.
The named entity with the highest score is predicted to be the author of the quote.

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
stored in the PostgreSQL database. This package also contains methods to extract annotated articles to xml files.

### ml package

Contains all files used to perform feature extraction and train models for quote detection and attribution.

### Frontend

The frontend is implemented with the VueJS framework.
