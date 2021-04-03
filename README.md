# Chat-aided Auto HIC Clipper

Clip the HICcup moment in vtuber's stream by reading "HIC" text in chat-room.

## Install

``` shell
git clone https://github.com/linnil1/chat-aided-hic-clipper
cd chat-aided-hic-clipper
pip3 install -r requirements.txt
```

Require python>3.7

## Example

I test on two vtubers whose HIC is cute and 助かる

* [Ubye(Taiwanese vtuber)](https://www.youtube.com/channel/UC-o-1qjKkMLq-ZFxXIzOUBQ)
* [Amelia Watson(Hololive)](https://www.youtube.com/channel/UCyl1z3jo3XHR1riLFKG5UAg)

Example videos

* [ejGH1BC1l98](https://www.youtube.com/watch?v=ejGH1BC1l98)
* [TgEX7HFqTYc](https://www.youtube.com/watch?v=TgEX7HFqTYc)

Result Clips

* [Auto-HIC-Clip-Example](https://www.youtube.com/watch?v=jLGqqvTqPCU&list=PLYWUpWR5imovoPNxMCQQ3jTjstBQGoZKE)

## Usage

### Download

Download video(via youtube-dl) and chats(pytchat)

`python3 auto_hic_clip.py ejGH1BC1l98 --download`

If you have downloaded the video already, you can just download chat-room(Takes times)

`python3 auto_hic_clip.py ejGH1BC1l98 --download-chat`

### Clip

The HIC keyword detector function is written in `config.py`.

Two functions are already implemented `hic_ame_keyword` and `hic_ubye_keyword`.

`python3 auto_hic_clip.py TgEX7HFqTYc --clip --keyword_func=hic_ame_keyword --keyword_threshold=10`

If the dryrun is specific,
it will show the timecode and HIC histogram instead of clipping.
The example histogram of ejGH1BC1l98(Saved in `./data/ejGH1BC1l98.hic.png`):

![hic-historgram](https://raw.githubusercontent.com/linnil1/chat-aided-hic-clipper/data/ejGH1BC1l98.hic.png)

`python3 auto_hic_clip.py TgEX7HFqTYc --clip-dryrun --keyword_func=hic_ame_keyword --keyword_threshold=10`

### Tune and Merge

Sometimes chat is not synchronize with video or the chat did not response to HIC at the same time.

You can manually fix by adding or removing the clips in `data/id.hic*`

I think it's more convenient to edit by Video Software or some visualization tool instead of command line.

#### 1

e.g. Clip 3:54:42-3:54:55 sections and add it as last one.

``` shell
python3 auto_hic_clip.py ejGH1BC1l98 --clip_timecode 3:54:42 \
    --clip_seconds_before=0 --clip_seconds_after=13
mv ./data/ejGH1BC1l98.3_54_4200.mp4 ./data/ejGH1BC1l98.hic99.mp4
```

#### 2

Or re-clip if the `clip_seconds` is not correct

e.g. The `clip_seconds_before` is not long enough for 25th HIC.

We can load the timecode from `data/TgEX7HFqTYc.hic.time.csv` by `--load_timecode`,
which the file is generated after `--clip` or `--clip_dryrun`

``` shell
python3 auto_hic_clip.py TgEX7HFqTYc --load_timecode --reclip_index=24 \
    --clip_seconds_before=7 --clip_seconds_after=-2
```

#### 3

Finally, merge the clips

`python3 auto_hic_clip.py TgEX7HFqTYc --merge`

### Summary

All in one line

``` shell
python3 auto_hic_clip.py ejGH1BC1l98 --download --clip --merge
python3 auto_hic_clip.py TgEX7HFqTYc --download --clip --keyword_func=hic_ame_keyword --keyword_threshold=10 --clip_seconds_before=3 --clip_seconds_after=2 --merge
```

## Method

1. The HIC text is filtered from the chat-room by a text comparing function in `config.py`.

3. The HIC event are grouped with elaped time by hierarchical clustering.
I assume the HIC event cannot occur twice within 60 seconds, thus 60 is the distance to separate the clusters.

3. The number of reports in the event are thresholded because some false alarms.

4. Clip the video by the HIC event with time-shift. -10s for Ubye and -3s for Ame.

Note: The values calculated by elapsed time and datetime are given almost same result in clustering.

## LICENSE

Welcome to use, fork or PR.

MIT
