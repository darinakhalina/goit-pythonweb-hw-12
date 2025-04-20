# goit-pythonweb-hw-012

## Demo video link
[Demo video](https://youtu.be/4DiCchOWrRI)

## Запуск
```bash
docker-compose up --build
```

## Демо Diagram
![Diagram](/img/diagram.png)

## Тести
```bash
pytest tests 
```

```bash
pytest --cov=src tests/ 

pytest --cov=src tests/ --cov-report=html
```

![Tests](/img/tests.png)

## Docs
```bash
сd docs

make html
```