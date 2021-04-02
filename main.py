import os
import json
import asyncio
from pytchat import LiveChatAsync
from tqdm import tqdm


folder = "./data"
ytid = None


async def download_chat(id):
    print(f"Download chat via pytchat")
    global ytid, pbar
    ytid = id
    pbar = tqdm(desc="Total chat download")
    chat = LiveChatAsync(id,
                         callback=save_chat)
    while chat.is_alive():
        await asyncio.sleep(3)
    pbar.close()

    # merge
    data = map(lambda i: json.loads(i), open(f"{folder}/{id}.chat.tmp"))
    with open(f"{folder}/{id}.chat.json", "w") as fout:
        json.dump({
            'id': id,
            'chats': list(data)},
            fout)
    print(f"Download {id} chat {folder}/{id}.chat.json")


async def save_chat(chatdata):
    with open(f"{folder}/{ytid}.chat.tmp", "a") as f:
        count = 0
        for c in chatdata.items:
            count += 1
            f.write(c.json() + "\n")
        pbar.update(count)


async def download_video(id):
    print(f"Download video via youtube-dl")
    proc = await asyncio.create_subprocess_exec(
            "youtube-dl", id, "-o", f"{folder}/{id}.mp4")
    print(f"Download {id} video into {id}.mp4")


async def download(id):
    await asyncio.gather(download_chat(id),
                         download_video(id))


if __name__ == "__main__":
    os.makedirs(folder, exist_ok=True)
    id = "c3hdmr5mlzc"  # test
    asyncio.run(download(id))
    # asyncio.run(download_chat(id))
    # asyncio.run(download_video(id))
