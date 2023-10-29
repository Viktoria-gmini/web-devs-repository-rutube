import json

from fastapi import FastAPI
from fastapi import Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette import status
from starlette.responses import JSONResponse
from webapi.parsing_functions import text_to_array, get_entity_group
from webapi.nn_interface import NNException
from webapi.rabbit_client import make_rabbitmq

app = FastAPI()
templates = Jinja2Templates(directory="templates")

nn_interface = make_rabbitmq()
my_dict = {}


# Function to process the input data and return an array of strings

@app.get('/', response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post('/', response_class=HTMLResponse)
def process_form(request: Request, article: str = Form(...), text: str = Form(...)):
    # Process the input data
    s = article + " " + text
    words = text_to_array(s)
    response = process_data()
    data = response.body
    result = json.loads(data)
    entities = result["tokens"]
    entities2 = []
    classes = result["tags"]
    classes2 = []
    pos = 0
    res_text, res_tags = [], []
    while pos < len(entities):
        res_tags.append(classes[pos])
        res_text.append([entities[pos]])
        pos += 1
        while pos < len(entities) and classes[pos][0] == "I":
            res_text[-1].append(entities[pos])
            pos += 1
    poses = []
    res_substr = []
    pos = 0
    for i in range(len(res_text)):
        if res_tags[i] == "O":
            continue
        start = s.find(res_text[i][0], pos)
        end = start + len(res_text[i][0])
        fd2 = pos
        if len(res_text) > 1:
            end = s.find(res_text[i][-1], pos)
            pos = end + len(res_text[i][-1])
            end = pos
        res_substr.append((start, end, res_tags[i][2:], res_text[i]))
        #[[3.5."персона",""матвей"],[7.10]
    return templates.TemplateResponse("index.html", {"request": request, "tags": res_tags,"r":res_substr,
                                      "string":s})


@app.post('/api/process_data')
def process_data(data: str = Form(...)):
    data_json = dict()
    try:
        data_json['text'] = str(data_json)
    except Exception as _:
        return JSONResponse(content={"error": "Invalid JSON"}, status_code=status.HTTP_400_BAD_REQUEST)
    try:
        result = nn_interface.post(data_json)
    except NNException as e:
        return JSONResponse(content={"error": repr(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return JSONResponse(result)


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002)
