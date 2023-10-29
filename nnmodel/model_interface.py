from transformers import AutoTokenizer
from razdel import tokenize
import torch
from transformers import AutoModelForTokenClassification


class Model():
    def __init__(self, path: str):
        self.tokenizer = AutoTokenizer.from_pretrained(path, device='cpu')
        self.label_list = ['O',
                           'B-Дата',
                           'B-бренд',
                           'B-вид спорта',
                           'B-видеоигра',
                           'B-команда',
                           'B-лига',
                           'B-локация',
                           'B-модель',
                           'B-название проекта',
                           'B-организация',
                           'B-персона',
                           'B-сезон',
                           'B-серия',
                           'I-Дата',
                           'I-бренд',
                           'I-вид спорта',
                           'I-видеоигра',
                           'I-команда',
                           'I-лига',
                           'I-локация',
                           'I-модель',
                           'I-название проекта',
                           'I-организация',
                           'I-персона',
                           'I-сезон',
                           'I-серия'
                           ]
        self.model = AutoModelForTokenClassification.from_pretrained(path, num_labels=len(self.label_list))
        self.model.config.id2label = dict(enumerate(self.label_list))
        self.model.config.label2id = {v: k for k, v in self.model.config.id2label.items()}

    def predict(self, text: str):
        raw_toks = list(tokenize(text))
        words = [tok.text for tok in raw_toks]
        tokens = self.tokenizer(words, truncation=True, is_split_into_words=True, return_tensors='pt')
        tokens = {k: v.to(self.model.device) for k, v in tokens.items()}

        with torch.no_grad():
            pred = self.model(**tokens)
            # print(pred.logits.shape)
        indices = pred.logits.argmax(dim=-1)[0].cpu().numpy()
        token_text = self.tokenizer.convert_ids_to_tokens(tokens['input_ids'][0])
        pos = 1
        word, label = [], []
        for i in words:
            t = self.tokenizer(i, truncation=True)['input_ids']
            dl = len(self.tokenizer.convert_ids_to_tokens(t)[1:-1])

            if pos >= len(indices):
                label.append(0)
                word.append(("OUT OF RANGE", self.tokenizer.convert_ids_to_tokens(t)))
            else:
                label.append(indices[pos])
                word.append((token_text[pos], self.tokenizer.convert_ids_to_tokens(t)))
            pos += dl
        label = [self.label_list[idx] for idx in label]
        return words, label

from nnmodel.logger_utils import logger

class WordTag:
    def __init__(self, word: str, label: str):
        self.word = word
        self.label = label

    def __str__(self):
        return f"{self.word} -> {self.label}"


class NNModel:
    def __init__(self, path: str):
        logger.info("Loading model")
        self._model = Model(path)
        logger.info("Loaded model")

    def predict(self, text: str) -> list[WordTag]:
        words, tags = self._model.predict(text)
        return [WordTag(word, tag) for word, tag in zip(words, tags)]

    @staticmethod
    def get_model():
        return NNModel('./nnmodel/model')


def main():
    logger.info("hi")
    m = NNModel('./model')
    # a, b = m.predict("Привет! Меня зовут Слава. Я люблю играть в Call Of Duty. Украина!")
    words = m.predict(
        "<НАЗВАНИЕ:> Агент 117: Из Африки с любовью — Русский тизер=трейлер (2021) <ОПИСАНИЕ:>Лучший Telegram канал о кино <LINK> Сотрудничество <LINK> Дата выхода 26 августа 2021 Оригинальное название: OSS 117: Alerte rouge en Afrique noire Страна: Франция Режиссер: Николя Бедос Жанр: боевик, комедия В главных ролях: Жан Дюжарден, Пьер Нинэ, Мелоди Каста, Наташа Линдинжер, Владимир Иорданов, Фату Н’Диайе, Пол Уайт Мир изменился. Он нет. Судьба заносит легендарного Агента 117 в Африку, где горячее пустыни только женщины. Вооруженный неиссякаемой уверенностью в себе и убийственной харизмой, он может справиться со всеми врагами, кроме самого себя. По вопросам авторского права, пожалуйста, свяжитесь с нами по адресу: <AT>")
    is_last_word_was_o = False
    for word in words:
        is_word_o = word.label == 'O'
        if not is_word_o or not is_last_word_was_o:
            print()
        print(word, end=" ")
        is_last_word_was_o = is_word_o
    print()


if __name__ == '__main__':
    main()
