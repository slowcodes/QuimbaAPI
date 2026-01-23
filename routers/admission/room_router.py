from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from db import get_db
from dtos.admission import RoomCreateDTO, RoomDTO, RoomUpdateDTO
from repos.admission.room_repository import RoomRepository

room_router = APIRouter(prefix="/api/admissions", tags=["Admissions"])


def get_room_repository(db: Session = Depends(get_db)) -> RoomRepository:
    return RoomRepository(db)


@room_router.post("/rooms", response_model=RoomDTO, status_code=status.HTTP_201_CREATED)
def create_room(room: RoomCreateDTO, repo: RoomRepository = Depends(get_room_repository)):
    return repo.create_room(room)


@room_router.get("/rooms", status_code=status.HTTP_200_OK)
def list_rooms(skip: int = 0, limit: int = 100, ward_id: int = 0, repo: RoomRepository = Depends(get_room_repository)):
    return repo.get_rooms(skip=skip, limit=limit, ward_id=ward_id)


@room_router.get("/rooms/{room_id}", response_model=RoomDTO, status_code=status.HTTP_200_OK)
def get_room(room_id: int, repo: RoomRepository = Depends(get_room_repository)):
    room = repo.get_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room


@room_router.put("/rooms/{room_id}", response_model=RoomDTO, status_code=status.HTTP_200_OK)
def update_room(room_id: int, room: RoomUpdateDTO, repo: RoomRepository = Depends(get_room_repository)):
    updated = repo.update_room(room_id, room)
    if not updated:
        raise HTTPException(status_code=404, detail="Room not found")
    return updated


@room_router.delete("/rooms/{room_id}", status_code=status.HTTP_200_OK)
def delete_room(room_id: int, repo: RoomRepository = Depends(get_room_repository)):
    deleted = repo.delete_room(room_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Room not found")
    return {"deleted": True}
