from fastapi import FastAPI
from fastapi.testclient import TestClient

from dtos.admission import BedCreateDTO, BedDTO, BedUpdateDTO, RoomCreateDTO, RoomDTO, RoomUpdateDTO
from routers.admission.bed_router import bed_router, get_bed_repository
from routers.admission.room_router import room_router, get_room_repository


class FakeBedRepository:
    def __init__(self):
        self._next_id = 1
        self._beds = {}

    def create_bed(self, bed: BedCreateDTO) -> BedDTO:
        data = bed.dict()
        data["id"] = self._next_id
        self._next_id += 1
        dto = BedDTO(**data)
        self._beds[dto.id] = dto
        return dto

    def get_bed(self, bed_id: int):
        return self._beds.get(bed_id)

    def get_beds(self, skip: int = 0, limit: int = 100, ward_id: int = 0):
        beds = list(self._beds.values())
        if ward_id:
            beds = [bed for bed in beds if bed.ward_id == ward_id]
        return {"data": beds[skip:skip + limit], "total": len(beds)}

    def update_bed(self, bed_id: int, bed: BedUpdateDTO):
        current = self._beds.get(bed_id)
        if not current:
            return None
        data = current.dict()
        data.update(bed.dict(exclude_unset=True))
        updated = BedDTO(**data)
        self._beds[bed_id] = updated
        return updated

    def delete_bed(self, bed_id: int):
        return self._beds.pop(bed_id, None) is not None


class FakeRoomRepository:
    def __init__(self):
        self._next_id = 1
        self._rooms = {}

    def create_room(self, room: RoomCreateDTO) -> RoomDTO:
        data = room.dict()
        data["id"] = self._next_id
        self._next_id += 1
        dto = RoomDTO(**data)
        self._rooms[dto.id] = dto
        return dto

    def get_room(self, room_id: int):
        return self._rooms.get(room_id)

    def get_rooms(self, skip: int = 0, limit: int = 100, ward_id: int = 0):
        rooms = list(self._rooms.values())
        if ward_id:
            rooms = [room for room in rooms if room.ward_id == ward_id]
        return {"data": rooms[skip:skip + limit], "total": len(rooms)}

    def update_room(self, room_id: int, room: RoomUpdateDTO):
        current = self._rooms.get(room_id)
        if not current:
            return None
        data = current.dict()
        data.update(room.dict(exclude_unset=True))
        updated = RoomDTO(**data)
        self._rooms[room_id] = updated
        return updated

    def delete_room(self, room_id: int):
        return self._rooms.pop(room_id, None) is not None


def create_client():
    app = FastAPI()
    app.include_router(bed_router)
    app.include_router(room_router)
    bed_repo = FakeBedRepository()
    room_repo = FakeRoomRepository()
    app.dependency_overrides[get_bed_repository] = lambda: bed_repo
    app.dependency_overrides[get_room_repository] = lambda: room_repo
    return TestClient(app)


def test_bed_crud_flow():
    client = create_client()

    create_resp = client.post(
        "/api/admissions/beds",
        json={"ward_id": 1, "bed_number": "B-01", "status": "Free"},
    )
    assert create_resp.status_code == 201
    bed_id = create_resp.json()["id"]

    get_resp = client.get(f"/api/admissions/beds/{bed_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["bed_number"] == "B-01"

    list_resp = client.get("/api/admissions/beds?skip=0&limit=10")
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] == 1

    update_resp = client.put(
        f"/api/admissions/beds/{bed_id}",
        json={"bed_number": "B-02"},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["bed_number"] == "B-02"

    delete_resp = client.delete(f"/api/admissions/beds/{bed_id}")
    assert delete_resp.status_code == 200
    assert delete_resp.json()["deleted"] is True

    missing_resp = client.get(f"/api/admissions/beds/{bed_id}")
    assert missing_resp.status_code == 404


def test_room_crud_flow():
    client = create_client()

    create_resp = client.post(
        "/api/admissions/rooms",
        json={"ward_id": 1, "room_number": "R-01", "capacity": 2, "status": "Free"},
    )
    assert create_resp.status_code == 201
    room_id = create_resp.json()["id"]

    get_resp = client.get(f"/api/admissions/rooms/{room_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["room_number"] == "R-01"

    list_resp = client.get("/api/admissions/rooms?skip=0&limit=10")
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] == 1

    update_resp = client.put(
        f"/api/admissions/rooms/{room_id}",
        json={"room_number": "R-02", "capacity": 3},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["room_number"] == "R-02"

    delete_resp = client.delete(f"/api/admissions/rooms/{room_id}")
    assert delete_resp.status_code == 200
    assert delete_resp.json()["deleted"] is True

    missing_resp = client.get(f"/api/admissions/rooms/{room_id}")
    assert missing_resp.status_code == 404
