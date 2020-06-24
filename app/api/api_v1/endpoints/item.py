from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/items/{id}")
async def read_item(id: str):
    if id == 'ok':
        return {
            'id':234,
            'label':'Special'
        }
    raise HTTPException(status_code=404, detail="Item not found")