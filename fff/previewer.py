from IPython.display import Image, Audio, Video, display


def preview_audio(file):
    audio = Audio(data=file.data)
    display(audio)


def preview_video(file):
    video = Video(data=file.data)
    display(video)


def preview_image(file):
    img = Image(data=file.data)
    display(img)


PREVIEWERS = {
    'audio': preview_audio,
    'video': preview_video,
    'image': preview_image,
}


def preview(file):
    type = file.mime
    cat = type.split('/')[0]
    previewer = PREVIEWERS.get(cat)
    if previewer:
        previewer(file)
    else:
        print('No previewer found for "{}"'.format(file.mime))
