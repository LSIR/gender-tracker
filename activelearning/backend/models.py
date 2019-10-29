from django.contrib.postgres.fields import JSONField
from django.db.models.fields import TextField
from django.db import models


class LabeledSentence(models.Model):
    """
    Annotated articles, where the text is an XML string containg 
    a <text> tag surrounding all text, a <p> tag sourround paragraphs, 
    an <RS> tag surrounding reported speech, and a <Author> tag around
    quote authors. Author and RS tags contain an author attribute, which
    links authors to quotes. Each author cited has exactly one author
    attribute value.
    """
    name = "Sentence"
    text = TextField()

    def __str__(self):
        return self.name


class Article(models.Model):
    """
    Articles, where the text is an XML string containg a <text> tag
    surrounding all text and a <p> tag sourround paragraphs.
    """
    name = "Article"
    text = TextField()

    def __str__(self):
        return self.name


class Labels(models.Model):
    """
    Lists of labels given by users to sentences in the paragraph.
    """
    name = "Labels"
    user_labels = JSONField()
    article = models.ForeignKey(Article, on_delete=models.CASCADE)

    def __str__(self):
        return self.name
