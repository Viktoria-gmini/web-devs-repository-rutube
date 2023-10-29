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
    str = article + " " + text
    words = text_to_array(article + " " + text)
    response = process_data(article,text)
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
    i=0
    while(i!=len(str)):
        for j in range(len(res_text)):
            if (res_tags[j]=='0'):
                for k in range(len(res_text[j])):
                    poses.append(0)
            elif(res_tags[j].startswith('B')):
                for k in range(len(res_text[j])):
                    poses.append(1)
        #     indexes.append(count+1)
        # elif (item.startswith('I')):
        #     indexes.append(count)
        # else:
        #     entities
        #     indexes.append(-1)
    state = 0
    for i in range(len(entities)):
        if indexes[i]-state==1:
            entities2.append(entities[i])
            classes2.insert(state,classes2[state].replace("B-",""))
            state+=1
        elif indexes[i]==state:
            new_string = entities2[state]+" "+entities[i]
            entities2.insert(state,new_string)
            entities2.insert(state,new_string)


    return templates.TemplateResponse("index.html", {"request": request, "words": words, "tokens": entities2,
                                                     "tags":classes2})


@app.post('/api/process_data')
def process_data(article, text):
    data = {article: text}
    data_json = json.dumps(data)
    try:
        data_json = dict(json.loads(data_json))
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
