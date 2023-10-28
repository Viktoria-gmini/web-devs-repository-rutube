import json
from typing import Annotated

from fastapi import FastAPI
from fastapi import Request, Form, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette import status
from starlette.responses import JSONResponse

from rabbit_wrapper import NNInterface, NNException

app = FastAPI()
templates = Jinja2Templates(directory="templates")

nn_interface = NNInterface.make_rabbitmq()


# Function to process the input data and return an array of strings
def process_input(article: str, text: str):
    # You can perform your processing here
    # For now, we'll simply split the text into an array of strings
    text_array = text.split()
    return text_array


@app.get('/', response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post('/', response_class=HTMLResponse)
def process_form(request: Request, article: str = Form(...), text: str = Form(...)):
    # Process the input data
    result = process_input(article, text)
    return templates.TemplateResponse("index.html", {"request": request, "result": result})

@app.post('/api/process_data')
def process_data(data = Form(...)):
    data_json = dict()
    try:
        data_json = dict(json.loads(data))
    except Exception as _:
        return JSONResponse({"error": "Invalid JSON"}, status_code=status.HTTP_400_BAD_REQUEST)
    try:
        result = nn_interface.post(data_json)
    except NNException as e:
        return JSONResponse({"error": repr(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return JSONResponse(result)


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
