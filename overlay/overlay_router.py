from datetime import timedelta, datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, Form, Query
from gtts import gTTS
from pydub import AudioSegment
from starlette.responses import FileResponse

from overlay.dub_request import DubRequest

overlay_router = APIRouter()


@overlay_router.post(
    '/dub',
    description='Overdub an mp3 file with text at specified points in the file',
    name='Dub',
)
async def add_dubs(song_file: UploadFile,
                   intro: str = Query('0:00', alias='Intro', description='Timestamp of intro, e.g. 0:01'),
                   verse_1: str = Query(None, alias='Verse 1'), chorus_1: str = Query(None, alias='Chorus 1'),
                   instrumental: str = Query(None, alias='Instrumental'), verse_2: str = Query(None, alias='Verse 2'),
                   chorus_2: str = Query(None, alias='Chorus 2'), bridge: str = Query(None, alias='Bridge'),
                   bridge_2: str = Query(None, alias='Bridge 2'), chorus_3: str = Query(None, alias='Chorus 3'),
                   ending: str = Query(None, alias='Ending'), extra: list[str] = Form(['Chorus 4 - 2:45.00'])):
    dubs = []
    extra = extra[0].split(',')
    if intro:
        _, timestamp = parse_request_text(intro)
        dubs.append(DubRequest(text='Intro', timestamp=timestamp))
    if verse_1:
        _, timestamp = parse_request_text(verse_1)
        dubs.append(DubRequest(text='Verse 1', timestamp=timestamp))
    if chorus_1:
        _, timestamp = parse_request_text(chorus_1)
        dubs.append(DubRequest(text='Chorus 1', timestamp=timestamp))
    if instrumental:
        _, timestamp = parse_request_text(instrumental)
        dubs.append(DubRequest(text='Instrumental', timestamp=timestamp))
    if verse_2:
        _, timestamp = parse_request_text(verse_2)
        dubs.append(DubRequest(text='Verse 2', timestamp=timestamp))
    if chorus_2:
        _, timestamp = parse_request_text(chorus_2)
        dubs.append(DubRequest(text='Chorus 2', timestamp=timestamp))
    if bridge:
        _, timestamp = parse_request_text(bridge)
        dubs.append(DubRequest(text='Bridge', timestamp=timestamp))
    if bridge_2:
        _, timestamp = parse_request_text(bridge_2)
        dubs.append(DubRequest(text='Bridge 2', timestamp=timestamp))
    if chorus_3:
        _, timestamp = parse_request_text(chorus_3)
        dubs.append(DubRequest(text='Chorus 3', timestamp=timestamp))
    if ending:
        _, timestamp = parse_request_text(ending)
        dubs.append(DubRequest(text='Ending', timestamp=timestamp))
    for dub_request in extra:
        if dub_request:
            text, timestamp = parse_request_text(dub_request)
            dubs.append(DubRequest(text=text, timestamp=timestamp))

    song = AudioSegment.from_mp3(song_file.file)
    dubbed_song = overlay(song, dubs)
    song_path = Path(song_file.filename)
    new_path = song_path.with_stem(song_path.stem + ' - with Guide')
    dubbed_song.export(new_path, format='mp3', bitrate='128k')
    return FileResponse(new_path, media_type='audio/mpeg', filename=str(new_path))


def parse_request_text(request: str):
    request = request.split(' - ', maxsplit=1)
    text = request[0] if len(request) == 2 else ''
    timestamp = request[-1]
    try:
        timestamp = datetime.strptime(timestamp, '%M:%S')
    except ValueError:
        try:
            timestamp = datetime.strptime(timestamp, '%M:%S.%f')
        except ValueError:
            raise HTTPException(status_code=422, detail=f'could not parse timestamp {timestamp}')
    delta = timedelta(minutes=timestamp.minute, seconds=timestamp.second, microseconds=timestamp.microsecond)
    return text, delta.total_seconds() * 1000


def overlay(song: AudioSegment, dubs: list[DubRequest]):
    for dub_request in dubs:
        dub_path = Path('dubs') / (dub_request.text + '.mp3')
        if not dub_path.exists():
            gTTS(dub_request.text).save(dub_path)
        dub = AudioSegment.from_file(dub_path)
        lower_bound = max(0, int(dub_request.timestamp - len(dub)))
        upper_bound = min(len(song), int(dub_request.timestamp + (2 * len(dub))))
        sample = song[lower_bound:upper_bound]
        # make the dub slightly quieter than the average volume during the period shortly before and after the dub
        gain = max(sample.dBFS - dub.dBFS - 12, -30)
        dub = dub.apply_gain(gain)

        song = song.overlay(dub, position=dub_request.timestamp)

    return song
