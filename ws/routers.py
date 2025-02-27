from fastapi import APIRouter, Depends,WebSocket
from redis import Redis
import asyncio
import json
from uuid import uuid4

import ws.schemas as schema
import ws.cruds as crud
import ws.events as event
from ws.redis import get_redis
from ws.events import room_users,game_loops

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket,redis: Redis = Depends(get_redis)):
    await websocket.accept()
    global room_users
    try:
        while True:
            data = await websocket.receive_text()  # クライアントからのメッセージを非同期に受信
            json_data = json.loads(data)
            event_type = json_data["event_type"]
            match event_type:
                case schema.EventTypeEnum.create_room:
                    room_id = event._create_room(redis=redis,data=json_data)
                    id = event._create_user(redis=redis,data=json_data,room_id=room_id)
                    event._change_room_owner_id(redis=redis,room_id=room_id,id=id)
                    room_users[room_id] = []
                    room_users[room_id].append(websocket)
                    message = event._create_response(redis=redis,event_type=event_type,json_data=json_data,room_id=room_id,id=id,num=None)
                    await websocket.send_text(message)
                case schema.EventTypeEnum.join_room:
                    room_id = json_data["room"]["room_id"]
                    id = event._create_user(redis=redis,data=json_data,room_id=room_id)
                    room_users[room_id].append(websocket)
                    message = event._create_broadcast(redis=redis,event_type=event_type,json_data=json_data,room_id=room_id)
                    await event._broadcast(room_id=room_id,message=message)
                case schema.EventTypeEnum.start_game:
                    room_id = json_data["room"]["room_id"]
                    print(room_id)
                    event._change_room_mode(redis=redis,room_id=room_id,mode=schema.ModeTypeEnum.playing,json_data=json_data)
                    print("change room mode")
                    message = event._create_broadcast(redis=redis,event_type=event_type,json_data=json_data,room_id=json_data["room"]["room_id"])
                    print("create broadcast")
                    await event._broadcast(room_id=room_id,message=message)
                    
                    global game_loops
                    print(game_loops)
                    game_loops[room_id] = asyncio.create_task(event._game_loop(redis=redis,room_id=room_id,json_data=json_data))
                # case schema.EventTypeEnum.ask_question:
                #     question = json_data["chat_text"]
                #     json_data["event_type"] = schema.EventTypeEnum.ask_question
                #     await event._broadcast(room_id=room_id,message=json.dumps(json_data))
                #     word = event._get_word(redis=redis,room_id=room_id)
                #     response = event._ask_question(question=question,word=word)
                #     json_data["event_type"] = schema.EventTypeEnum.give_answer
                #     json_data["chat_text"] = response
                #     await event._broadcast(room_id=room_id,message=json.dumps(json_data))
                    
            
    except Exception as e:
        print(f"WebSocketエラー: {e}")
    finally:
        pass
        # ユーザーが退出した場合、ルームから削除する
        # ルームが空になった場合、ルームを破壊する

@router.post("/redis/get", response_model=schema.RoomModel|None)
async def get_redis_list(request: schema.RedisGetRequest,redis: Redis = Depends(get_redis)):
    value=crud.get_redis(redis=redis,key=request.key)
    if value:
        return schema.RoomModel.model_validate(json.loads(value))
    else:
        return None

@router.post("/redis/post", response_model=schema.RedisInsertResponse)
async def get_redis_list(request: schema.RedisInsertRequest,redis: Redis = Depends(get_redis)):
    crud.post_redis(redis=redis,key=request.key,value=request.value)
    return schema.RedisInsertResponse(key=request.key, value=request.value)

@router.post("/redis/list", response_model=schema.RedisGetListResponse)
async def get_redis_list(redis: Redis = Depends(get_redis)):
    items = crud.get_redis_list(redis=redis)
    return schema.RedisGetListResponse(items=items)