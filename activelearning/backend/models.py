from django.contrib.postgres.fields import JSONField
from django.db.models.fields import TextField, IntegerField
from django.db import models


class Article(models.Model):
    """
    Represents an article table
    """
    name = "Article"
    # String representation of the article's XML file.
    text = TextField()
    # List of unique people cited in the article
    authors = JSONField()
    # Article text surrounded by a list of tokens
    tokens = JSONField()
    # List of all token indices that are the start of paragraphs
    paragraphs = JSONField()
    # List of all token indices that are the start of sentences
    sentences = JSONField()
    # List of the number of user labels for each token 
    label_counts = JSONField()
    # List of boolean values {0, 1} representing if a token is in between quotes or not
    in_quotes = JSONField()
    # List of values, where value j is in (0, 1) representing the confidence of the current
    # ML models predictions in deciding if sentence j is a quote or not. 1 means absolute
    # confidence (the sentence has been labeled), while 0 means completely unsure.
    confidence = JSONField()
    
    def __str__(self):
        return self.name


class UserLabel(models.Model):
    """
    Lists of labels given by users to sentences in the paragraph.
    """
    name = "User Labels"
    # Each user labelling is for a sentence in a particular article
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    # Stores a unique identifier for the user session that created this label
    session_id = IntegerField() 
    # List of the labels given to each word by the user
    labels = JSONField()
    # The first token in the sentences index in the article
    sentence_index = IntegerField()
    # A list of the token indices that are the author of this citation
    author_index = JSONField()

    def __str__(self):
        return self.name

