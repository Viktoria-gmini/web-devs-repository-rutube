import hashlib

import pandas as pd

# Теперь из наших данных нам нужно извлечь для каждого слова (токена) его тег (label) из разметки, чтобы потом
# предать в модель классификации токенов
from razdel import tokenize


def extract_labels(item):
    # воспользуемся удобным токенайзером из библиотеки razdel,
    # она помимо разбиения на слова, сохраняет важные для нас числа - начало и конец слова в токенах

    raw_toks = list(tokenize(item['video_info']))
    words = [tok.text for tok in raw_toks]
    # присвоим для начала каждому слову тег 'О' - тег, означающий отсутствие NER-а
    word_labels = ['O'] * len(raw_toks)
    char2word = [None] * len(item['video_info'])
    # так как NER можем состаять из нескольких слов, то нам нужно сохранить эту инфорцию
    for i, word in enumerate(raw_toks):
        char2word[word.start:word.stop] = [i] * len(word.text)

    labels = item['entities']
    if isinstance(labels, dict):
        labels = [labels]
    if labels is not None:
        for e in labels:
            if e['label'] != 'не найдено':
                e_words = sorted({idx for idx in char2word[e['offset']:e['offset'] + e['length']] if idx is not None})
                if e_words:
                    word_labels[e_words[0]] = 'B-' + e['label']
                    for idx in e_words[1:]:
                        word_labels[idx] = 'I-' + e['label']
                else:
                    continue
            else:
                continue
        return {'tokens': words, 'tags': word_labels}
    else:
        return {'tokens': words, 'tags': word_labels}


def main():
    data = pd.read_csv('ner_data_train.csv')
    import json
    df = data.copy()
    df['entities'] = df['entities'].apply(lambda l: l.replace('\,', ',') if isinstance(l, str) else l)
    df['entities'] = df['entities'].apply(lambda l: l.replace('\\\\', '\\') if isinstance(l, str) else l)
    df['entities'] = df['entities'].apply(lambda l: '[' + l + ']' if isinstance(l, str) else l)
    df['entities'] = df['entities'].apply(lambda l: json.loads(l) if isinstance(l, str) else l)
    id_length = 8
    for video_num in range(len(df)):
        video_row = df.iloc[video_num]
        extracted_result = extract_labels(video_row)
        tokens = extracted_result['tokens']
        tokens_hash = hashlib.sha256(str(tokens).encode('utf-8'))
        video_uuid = tokens_hash.hexdigest()[:id_length]
        tags = extracted_result['tags']
    pass


if __name__ == '__main__':
    main()
