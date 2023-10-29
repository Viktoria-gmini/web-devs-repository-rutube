# Запуск
### Docker
Из папки проекта (с видеокартой):
```bash
docker-compose -f ./devops/compose.gpu.yml up -d
```
Без видеокарты (без видеокарты)
```bash
docker-compose -f ./devops/compose.cpu.yml up -d
```
### Вручную
Сложно, обращайтесь к разработчику