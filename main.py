
import uvicorn as uvicorn
from fastapi import FastAPI
from starlette.responses import RedirectResponse

from overlay import overlay_router

tags_metadata = [
    {
        'name': 'overlay',
        'description': 'Do cool stuff'
    }
]

app = FastAPI(
    title='Overdub',
    description='Overdub Audio with text',
    openapi_tags=tags_metadata
)
app.include_router(overlay_router, prefix='/api', tags=['overlay'])


@app.get('/')
def home_page():
    return RedirectResponse(url='/docs')


if __name__ == '__main__':
    uvicorn.run('main:app', host='localhost', port=32322)
