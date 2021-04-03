import os
import json
import glob
import asyncio
import argparse
from datetime import timedelta
from pytchat import LiveChatAsync
from tqdm import tqdm
import scipy.cluster.hierarchy as hcluster
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from moviepy.editor import VideoFileClip, concatenate_videoclips


folder = "./data"
ytid = None  # BAD to put in global


async def download_chat(id):
    print(f"Download {id} chat via pytchat")
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
    print(f"Download {id} chat in {folder}/{id}.chat.json")


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


def sec_to_str(sec):
    return str(timedelta(seconds=int(sec)))


def str_to_sec(s):
    a = str(s).split(':')
    while len(a) < 3:
        a = [0] + a
    return int(a[0]) * 3600 + int(a[1]) * 60 + int(a[2])


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
    hic_eps = np.array(list(map(lambda i: str_to_sec(i['elapsedTime']),
                                data_hic)))

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


def clip_by_timestamp(id, timestamps, suffix="hic", index=None,
                      seconds_before=5, seconds_after=10):
    video = VideoFileClip(f"{folder}/{id}.mp4")
    for i, t in enumerate(timestamps):
        if index is not None and i != index:
            continue
        clip = video.subclip(t - seconds_before, t + seconds_after)
        clip.write_videofile(f"{folder}/{id}.{suffix}{i:02d}.mp4")


def clip_merge(id, suffix="hic"):
    input_videos = sorted(glob.glob(f"{folder}/{id}.{suffix}*.mp4"))
    input_videos = list(filter(lambda i: "merged" not in i, input_videos))
    videos = map(VideoFileClip, input_videos)
    merged_video = concatenate_videoclips(list(videos))
    merge_file = f"{folder}/{id}.{suffix}.merged.mp4"
    merged_video.write_videofile(merge_file)
    print(f"merge {input_videos} into {merge_file}")


def setupParser():
    parser = argparse.ArgumentParser(description="Auto HIC clipper",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("id", type=str,
                        help="Youtube video id")
    parser.add_argument("--base", type=str, default="./data",
                        help="Path to data folder")

    # download
    parser.add_argument("--download", action="store_true",
                        help="Download youtube chat and video simultaneously")
    parser.add_argument("--download_chat", action="store_true",
                        help="Donwload chat only")
    parser.add_argument("--download_video", action="store_true",
                        help="Donwload video only")

    # keyword
    parser.add_argument("--keyword_threshold", type=int, default=3)
    parser.add_argument("--keyword_func", type=str, default="hic_ubye_keyword",
                        help="Fill the function name in config.py")
    parser.add_argument("--suffix", type=str, default="hic")
    parser.add_argument("--load_timecode", action="store_true",
                        help="Load the timecode file"
                             "(This file is generated after "
                             "--clip or --clip_dryrun)")

    # clip
    parser.add_argument("--clip", action="store_true",
                        help="Clip the video by timecode")
    parser.add_argument("--clip_dryrun", action="store_true",
                        help="Same as --clip but only plot the timecode")
    parser.add_argument("--clip_timecode", type=str,
                        help="Specific timecode you want to clip")
    parser.add_argument("--reclip_index", type=int,
                        help="Specific hic.index you want to reclip")
    parser.add_argument("--clip_seconds_before", type=float, default=5,
                        help="Seconds before the event for clipping")
    parser.add_argument("--clip_seconds_after", type=float, default=10,
                        help="Seconds after the event for clipping")
    parser.add_argument("--merge", action="store_true",
                        help="Merge the clips")

    return parser


if __name__ == "__main__":
    parser = setupParser()
    args = parser.parse_args()
    id = args.id
    folder = args.base
    os.makedirs(folder, exist_ok=True)

    if args.download:
        asyncio.run(download(id))
    else:
        if args.download_chat:
            asyncio.run(download_chat(id))
        if args.download_video:
            asyncio.run(download_video(id))

    if args.clip or args.clip_dryrun or args.reclip_index:
        file_timecode = f"{folder}/{id}.hic.time.csv"

        if args.load_timecode and os.path.exists(file_timecode):
            timestamps = list(map(lambda i: str_to_sec(i.split(",")[0]),
                                  open(file_timecode)))
        else:
            import config
            keyword_func = getattr(config, args.keyword_func)
            timestamps = get_keyword_timestamp(
                    f"{folder}/{id}.chat.json",
                    keyword_func,
                    thresh_report=args.keyword_threshold,
                    show_fig=args.clip_dryrun)

            # save
            with open(file_timecode, "w") as flog:
                for i, t in enumerate(timestamps):
                    flog.write(f"{str(sec_to_str(t))},hic{i:02d}\n")

        # log
        print("HIC timecode:")
        for i, t in enumerate(timestamps):
            print(f"  hic{i:02d} {str(sec_to_str(t))}")

        # clip
        if not args.clip_dryrun:
            clip_by_timestamp(id, timestamps,
                              suffix=args.suffix,
                              index=args.reclip_index,
                              seconds_before=args.clip_seconds_before,
                              seconds_after=args.clip_seconds_after)

    elif args.clip_timecode:
        t = str_to_sec(args.clip_timecode)
        clip_by_timestamp(id, [t],
                          suffix=args.clip_timecode.replace(":", "_"),
                          seconds_before=args.clip_seconds_before,
                          seconds_after=args.clip_seconds_after)

    if args.merge:
        clip_merge(id, suffix=args.suffix)
