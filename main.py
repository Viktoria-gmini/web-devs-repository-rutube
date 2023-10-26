from fastapi import FastAPI
from fastapi import Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(directory="templates")

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

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)