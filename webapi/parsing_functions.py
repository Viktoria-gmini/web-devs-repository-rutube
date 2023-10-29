
def text_to_array(text):
    words = text.split()
    replaced_words = []
    for word in words:
        replaced_words.append(word)
    return replaced_words


def get_entity_group(data):
    entity_dict = {}
    for item in data:
        entity_dict[item['word']] = item['entity_group']
    return entity_dict
