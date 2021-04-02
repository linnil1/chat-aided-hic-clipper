import os
import json
import asyncio
from datetime import timedelta
from pytchat import LiveChatAsync
from tqdm import tqdm
import scipy.cluster.hierarchy as hcluster
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from moviepy.editor import VideoFileClip


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


def sec_to_str(i):
    return str(timedelta(seconds=int(i)))

def get_keyword_timestamp(chat_file, keyword_func,
                          save_fig=True, show_fig=False,
                          thresh_time=60, thresh_report=3):
    """
    Find keyword in the chatdata

    The timestamps is returned when there is a group(cluster) of reports.

    args:
      chat_file: path to chat json file
      keyword_func: A custome keyword matching function
      thresh_time (int): Threshold time interval to separate the events
      thresh_report (int): Threshold of minimal reports of the events

    returns:
      timestamps: list of int
    """
    # get hic items
    chat_data = json.load(open(chat_file))
    data = chat_data['chats']
    data_hic = filter(keyword_func, data)

    # get eps, you can calculate the elapsed_time manually
    hic_eps = map(lambda i: i['elapsedTime'].split(":"), data_hic)
    hic_eps = map(lambda i: i if len(i) == 3 else ["0"] + i, hic_eps)
    hic_eps = np.array(list(hic_eps), dtype=int)
    hic_eps = hic_eps.dot([3600, 60, 1])

    # cluster
    clusters = hcluster.fclusterdata(hic_eps[:, None],
                                     thresh_time,
                                     criterion="distance")
    data_cluster = []

    # parse and threshold
    for i in set(clusters):
        cluster_hic = hic_eps[clusters == i]
        cluster_num = len(cluster_hic)
        if cluster_num < thresh_report:
            continue

        first_eps = np.sort(cluster_hic)[1]
        data_cluster.append([first_eps, cluster_num])
    data_cluster = sorted(data_cluster)

    if save_fig:
        # Basic
        plt.figure(figsize=(14, 5))
        plt.xlabel("Time")
        plt.ylabel("HIC in chat")
        plt.gca().xaxis.set_major_formatter(
                matplotlib.ticker.FuncFormatter(lambda i, _: sec_to_str(i)))

        # histogram
        plt.hist(hic_eps, bins=(max(hic_eps) - min(hic_eps)) // 60)

        # plot cluster text
        for cluster_eps, cluster_num in data_cluster:
            plt.text(cluster_eps,
                     cluster_num,
                     f"{sec_to_str(cluster_eps)}"
                     f"--{cluster_num}reports")

        plt.xlim(left=0)
        plt.ylim(top=max(map(lambda i: i[1], data_cluster)))
        plt.title(f"HIC event: (Total: {len(data_cluster)})")
        plt.savefig(f"{folder}/{chat_data['id']}.hic.png")
        if show_fig:
            plt.show()
        plt.close()

    return list(map(lambda i: i[0], data_cluster))


def clip_by_timestamp(id, timestamps, seconds_before=5, seconds_after=10):
    video = VideoFileClip(f"{folder}/{id}.mp4")
    for i, t in enumerate(timestamps):
        clip = video.subclip(t - seconds_before, t + seconds_after)
        clip.write_videofile(f"{folder}/{id}.hic{i:02d}.mp4")


if __name__ == "__main__":
    os.makedirs(folder, exist_ok=True)
    id = "c3hdmr5mlzc"  # test
    # asyncio.run(download(id))
    # asyncio.run(download_chat(id))
    # asyncio.run(download_video(id))

    def hic_ame_keyword(i):
        return "hic" == i['message'].lower() or \
               ":_hic1::_hic2::_hic3:" == i['message']

    def hic_ubye_keyword(i):
        # this is enough in chinese chat
        return "hic" in i['message'].lower()

    """
    id = "ejGH1BC1l98"  # ubye
    asyncio.run(download(id))

    timestamps = get_keyword_timestamp(
            f"{folder}/{id}.chat.json",
            hic_ubye_keyword)
    clip_by_timestamp(id, timestamps)
    """

    id = "TgEX7HFqTYc"  # ame

    # asyncio.run(download(id))
    timestamps = get_keyword_timestamp(
            f"{folder}/{id}.chat.json",
            hic_ame_keyword, show_fig=False,
            thresh_report=10)
    print(list(map(sec_to_str, timestamps)))
    # clip_by_timestamp(id, timestamps,
    #                   seconds_before=5, seconds_after=2.5)
