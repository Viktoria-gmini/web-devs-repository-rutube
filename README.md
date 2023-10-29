# Запуск
### Docker
1. Скачать модель:  
2. Положить в папку nnmodel проекта. Папка ДОЛЖНА называться model (переименовать)
```
project_folder\nnmodel
│
├───logger_utils
│
├───model  <----------------------
│       config.json
│       pytorch_model.bin
│       special_tokens_map.json
│       tokenizer.json
│       tokenizer_config.json
│       vocab.txt
│
├───rabbit_utils
│
└───thread_utils
```
3. Запустить докер-компоуз. Из папки проекта  

С видеокартой:
```bash
docker-compose -f ./devops/compose.gpu.yml up -d
```
Без видеокарты:
```bash
docker-compose -f ./devops/compose.cpu.yml up -d
```
### Вручную
Сложно, обращайтесь к разработчику