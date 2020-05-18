from django.contrib.postgres.fields import JSONField
from django.db import models
from django.db.models.fields import TextField, IntegerField, BooleanField, CharField


class Article(models.Model):
    """
    Represents an article table
    """
    name = CharField(max_length=200)
    # String representation of the article's XML file.
    text = TextField()
    # List of unique people cited in the article
    people = JSONField()
    # Article text surrounded by a list of tokens
    tokens = JSONField()
    # List of all sentence indices that are the ends of paragraphs
    paragraphs = JSONField()
    # List of all token indices that are the ends of sentences
    sentences = JSONField()
    # List of boolean values {0, 1} representing if a sentence is fully labeled or
    labeled = JSONField()
    # List of boolean values {0, 1} representing if a token is in between quotes or not
    in_quotes = JSONField()
    # List of values, where value j is in (0, 1) representing the confidence of the current ML models predictions in
    # deciding if sentence j is a quote or not. 1 means absolute confidence, while 0 means completely unsure.
    confidence = JSONField()
    # If this article can only be seen by admins
    admin_article = BooleanField()
    # The newspaper in which the article was published
    source = CharField(max_length=200)
    # Date of instance creation
    created_at = models.DateTimeField(auto_now_add=True)
    

    def __str__(self):
        return f'Article id: {self.id}'


class UserLabel(models.Model):
    """
    Lists of labels given by users to sentences in the paragraph.
    """
    # Each user labelling is for a sentence in a particular article
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    # Stores a unique identifier for the user session that created this label
    session_id = CharField(max_length=50)
    # List of the labels given to each word by the user
    labels = JSONField()
    # The index of the sentence that has these labels
    sentence_index = IntegerField()
    # A list of the token indices that are the author of this citation
    author_index = JSONField()
    # If this label was added by an admin user
    admin_label = BooleanField()
    # Date of instance creation
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Label id: {self.id}, Session id: {self.session_id}, {self.article}, Sentence Number: ' \
               f'{self.sentence_index}'
