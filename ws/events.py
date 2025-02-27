from redis import Redis
from uuid import uuid4
import json
from fastapi import WebSocket
import random
import asyncio
import requests
import os

import ws.schemas as schema
import ws.cruds as crud

room_users: dict[str, list[WebSocket]] = {}
game_loops: dict[str, asyncio.Task] = {}

api_url = "https://api.openai.com/v1/chat/completions"

def _create_user(redis: Redis,data: dict,room_id: str) -> str:
    value = crud.get_redis(redis=redis,key=room_id)
    value = json.loads(value)
    
    id = str(uuid4())
    value["users"].append({
        "id": id
    })
    crud.post_redis(redis=redis,key=room_id,value=json.dumps(value))
    return id
    
def _create_room(redis: Redis,data: dict) -> str | None:
    json_data = _get_room_model()
    room_id = str(uuid4())
    json_data["room"]["room_id"] = room_id
    
    value = json.dumps(json_data)
    crud.post_redis(redis=redis,key=room_id,value=value)
    return room_id

def _ask_question(question: str,word: str) -> str|None:
    print(question,word)
    request_body = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "userが" + word + "について質問するので「はい」か「いいえ」か「分からない」のどれかで回答してください。「はい」か「いいえ」で答えられない質問や質問になっていないものなどは全て「分からない」で回答してください。回答は一般的な常識で行ってください。「はい」「いいえ」「分からない」以外で回答をすると無実の人間が被害に遭うので「はい」「いいえ」「分からない」以外は絶対に発言しないでください"},
            {"role": "user", "content": question}
        ]
    }
    
    json_data = json.dumps(request_body)

    headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {os.getenv('SECRET_KEY')}"
}
    
    response = requests.post(api_url, headers=headers, data=json_data)

    if response.status_code == 200:
        response_data = response.json()
        chat_completion = response_data
        print(chat_completion)
        
        return chat_completion["choices"][0]["message"]["content"]
    else:
        try:
            error_message = response.json()["error"]
        except (KeyError, json.JSONDecodeError):
            error_message = "Unknown error occurred."
        
        print(f"Error {response.status_code}: {error_message}")
        return None
    
def _get_word(redis: Redis,room_id: str) -> str:
    value = crud.get_redis(redis=redis,key=room_id)
    value = json.loads(value)
    num = int(value["room"]["wolf"])
    return value["users"][0]["word"] #懸念点 
    
def _change_room_owner_id(redis: Redis,room_id: str,id: str) -> None:
    value = crud.get_redis(redis=redis,key=room_id)
    value = json.loads(value)
    value["room"]["room_owner_id"] = id
    crud.post_redis(redis=redis,key=room_id,value=json.dumps(value))
    return None

def _change_room_mode(redis: Redis,room_id: str,mode: str,json_data: dict) -> None:
    value = crud.get_redis(redis=redis,key=room_id)
    value = json.loads(value)
    value["status"]["mode"] = mode
    
    crud.post_redis(redis=redis,key=room_id,value=json.dumps(value))
    return None

async def _give_word(redis: Redis,room_id: str,json_data: dict) -> None:
    global room_users
    num = 0
    for user in room_users[room_id]:
        message = _create_response(redis=redis, event_type=schema.EventTypeEnum.start_game, json_data=json_data, room_id=room_id, id="", num=num)
        num += 1
        await user.send_text(message)

def _get_room_model() -> dict:
    json ={
        "room": {
            "room_id": "",
            "room_owner_id": "",
        },
        "status": {
            "mode": "wait",
        },
        "users": []
    }
    return json

async def _broadcast(room_id: str,message: str) -> None:
    global room_users
    for user in room_users[room_id]:
        await user.send_text(message)
        
def _change_create_room_response(redis:Redis,json_data: dict,room_id: str) -> dict:
    value = crud.get_redis(redis=redis,key=room_id)
    value = json.loads(value)
    json_data["room"] = {
        "room_id": room_id,
        "room_owner_id": value["users"][0]["id"]
    }
    
    return json_data
        
def _change_enter_room_response(redis:Redis,json_data: dict,room_id: str,id: str) -> dict:
    value = crud.get_redis(redis=redis,key=room_id)
    value = json.loads(value)
    json_data["user"]["id"] = id
    json_data["users"] = value["users"]
    
    return json_data

def _change_start_game_response(redis:Redis,json_data: dict,room_id: str,id: str,num: int) -> dict:
    value = crud.get_redis(redis=redis,key=room_id)
    value = json.loads(value)
    json_data["user"]["word"] = value["users"][num]["word"]
    
    return json_data

def _change_enter_room_broadcast(redis:Redis,json_data: dict,room_id: str) -> dict:
    value = crud.get_redis(redis=redis,key=room_id)
    value = json.loads(value)
    json_data["users"] = value["users"]
    
    return json_data

def _change_start_game_broadcast(redis:Redis,json_data: dict,room_id: str) -> dict:
    return json_data

def _create_response(redis:Redis,event_type: schema.EventTypeEnum,json_data: dict,room_id: str,id: str,num: int|None) -> str:
    match event_type:
        case schema.EventTypeEnum.create_room:
            json_data = _change_create_room_response(redis=redis,json_data=json_data,room_id=room_id)
        case schema.EventTypeEnum.enter_room:
            json_data = _change_enter_room_response(redis=redis,json_data=json_data,room_id=room_id,id=id)
        case schema.EventTypeEnum.start_game:
            json_data = _change_start_game_response(redis=redis,json_data=json_data,room_id=room_id,id=id,num=num)
    return json.dumps(json_data)

def _create_broadcast(redis:Redis,event_type: schema.EventTypeEnum,json_data: dict,room_id: str) -> str:
    match event_type:
        case schema.EventTypeEnum.join_room:
            json_data = _change_enter_room_broadcast(redis=redis,json_data=json_data,room_id=room_id)
        case schema.EventTypeEnum.start_game:
            json_data = _change_start_game_broadcast(redis=redis,json_data=json_data,room_id=room_id)
    return json.dumps(json_data)

async def _game_loop(redis:Redis,room_id: str,json_data: dict):
    while True:
        key = crud.get_redis(redis=redis,key=room_id)
        key = json.loads(key)
        event_type = key["status"]["mode"]
        match event_type:
            case schema.ModeTypeEnum.question:
                print("質問タイム")
                if int(key["time_now"]) > int(key["options"]["discuss_time"]):
                    print(key["time_now"])
                    key["status"]["mode"] = schema.ModeTypeEnum.voting
                    key["time_now"] = 0
                    crud.post_redis(redis=redis,key=room_id,value=json.dumps(key))
                    
                    json_data["event_type"] = "end_Q_and_A"
                    await _broadcast(room_id=room_id,message=json.dumps(json_data))
                else:
                    key["time_now"] = int(key["time_now"]) + 1
                    print(key["time_now"])
                    crud.post_redis(redis=redis,key=room_id,value=json.dumps(key))
                    await asyncio.sleep(1)
                    
                    json_data["event_type"] = "send_time"
                    json_data["time_now"] = int(key["time_now"]) + 1
                    await _broadcast(room_id=room_id,message=json.dumps(json_data))
            case schema.ModeTypeEnum.voting:
                if key["time_now"] > key["options"]["vote_time"]:
                    key["status"]["mode"] = schema.ModeTypeEnum.wait
                    key["time_now"] = 0
                    crud.post_redis(redis=redis,key=room_id,value=json.dumps(key))
                    
                    json_data["event_type"] = "game_result"
                    await _broadcast(room_id=room_id,message=json.dumps(json_data))
                else:
                    key["time_now"] = int(key["time_now"]) + 1
                    print(key["time_now"])
                    crud.post_redis(redis=redis,key=room_id,value=json.dumps(key))
                    await asyncio.sleep(1)
                    
                    json_data["event_type"] = "send_time"
                    json_data["time_now"] = int(key["time_now"]) + 1
                    await _broadcast(room_id=room_id,message=json.dumps(json_data))
        print(f"Room {room_id} - Game loop")
        await asyncio.sleep(1)  # ここにゲームの状態を更新する処理を追加