from django.http import JsonResponse
import xml.etree.ElementTree as ET

def hello(request):
    return JsonResponse({'hello': 'world'})

def loadSentence(request):
    xml_article = load_article()
    response = parse_xml(xml_article)
    return JsonResponse(response)

# As I'm not sure where to put helper functions yet (my guess is that I'll write a helper.py file),
# I'll write them in here for now

def load_article():
    """
    :return: an article whose quotes we want to label.
    Right now: loads the only xml-formatted article I have, and returns it as an ElementTree.
    Future: Probably load a random article (or a carefully selected one), parse it and return
    it as an ElementTree. How we choose each article to parse is the important part.
    """
    article_path = '../data/article01.xml'
    return ET.parse(article_path)

def parse_xml(xml_file):
    """
    :param xml_file: the ElementTree we want to parse into a JSON object
    :return: the ElementTree as a JSON object. 
    """
    root = xml_file.getroot()
    full_text = get_element_text(root)
    returned_text = full_text[:45] +  ' ...'
    split_words = returned_text.split(' ')
    return {'sentence': split_words}

def get_element_text(element):
    """
    Takes as input an ElementTree Element, and returns all text contained between its
    two XML labels as a string.
    :param element: the element whose contained text we want
    :return: all text contained between "element"s two tags.
    """
    # Text as list of strings
    ls = list(element.itertext())
    # Concatenate
    text = ''.join(ls)
    # Clean text
    text = ''.join(ls).replace('\n', '')
    text = ' '.join(text.split())
    return text