from enum import Enum
from pydantic import BaseModel,Field

class EventTypeEnum(str, Enum):
    create_room = "create_room"
    join_room = "join_room"
    start_game = "start_game"
    send_shot = "send_shot"
    ready_shot = "ready_shot"
    reach_goal = "reach_goal"
    notify_game_end = "notify_game_end"
    wait_for_next_shot = "wait_for_next_shot"

class VoteItem(BaseModel):
    id: str | None
    display_name: str | None

class UserItem(BaseModel):
    id: str | None
    display_name: str | None
    icon: str | None
    is_wolf: bool | None
    score: int | None
    word: str | None
    is_participant: bool | None
    vote: VoteItem | None
    
class RoomItem(BaseModel):
    room_id: str | None
    room_owner_id: str | None
    vote_ended: bool | None

class OptionItem(BaseModel):
    turn_num: int | None
    discuss_time: int | None
    vote_time: int | None
    participants_num: int | None
    
class WinEnum(str, Enum):
    wolf = "wolf"
    citizen = "citizen"
    draw = "draw"
    
class UsersItem(BaseModel):
    display_name: str | None
    is_wolf: bool | None
    score: int | None
    word: str | None
    vote: list[VoteItem] | None

class ShotItem(BaseModel):
    x: float
    y: float

class Request(BaseModel):
    event_type: EventTypeEnum
    user: UserItem | None
    room: RoomItem | None
    chat_text: str | None
    options: OptionItem | None
    time_now: str | None
    win: WinEnum | None
    users: list[UsersItem] | None
    shot: ShotItem | None
    
class Response(BaseModel):
    event_type: EventTypeEnum
    user: UserItem | None
    room: RoomItem | None
    chat_text: str | None
    options: OptionItem | None
    time_now: str | None
    win: WinEnum | None
    users: list[UsersItem] | None
    shot: ShotItem | None
    
class RedisGetRequest(BaseModel):
    key: str

class RedisInsertRequest(BaseModel):
    key: str
    value: str
    
class RedisGetResponse(BaseModel):
    value: str | None
    
class RedisInsertResponse(BaseModel):
    key: str | None

class RedisGetListResponse(BaseModel):
    items: list[tuple[str, str]] | None

class ModeTypeEnum(str, Enum):
    wait = "wait"
    playing = "playing"
    firing = "firing"
    game_end = "game_end"

class status(BaseModel):
    mode: ModeTypeEnum
    turn_now: str | None

class RoomModel(BaseModel):
    room: RoomItem | None
    options: OptionItem | None
    status: status | None
    time_now: str | None
    win: WinEnum | None
    users: list[UserItem|None] | None