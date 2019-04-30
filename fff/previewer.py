from .abstract_file import AbstractFile

from IPython.display import Image, Audio, display, DisplayObject
from binascii import b2a_base64


def preview_audio(file: AbstractFile):
    audio = Audio(data=file.data)
    display(audio)


class Video(DisplayObject):

    def __init__(self, data=None, url=None, filename=None, embed=False,
                 mimetype=None, width=None, height=None):
        if url is None and isinstance(data, str) and data.startswith(('http:', 'https:')):
            url = data
            data = None
        elif isinstance(data, str) and os.path.exists(data):
            filename = data
            data = None

        if data and not embed:
            msg = ''.join([
                "To embed videos, you must pass embed=True ",
                "(this may make your notebook files huge)\n",
                "Consider passing Video(url='...')",
            ])
            raise ValueError(msg)

        self.mimetype = mimetype
        self.embed = embed
        self.width = width
        self.height = height
        super(Video, self).__init__(data=data, url=url, filename=filename)

    def _repr_html_(self):
        width = height = ''
        if self.width:
            width = ' width="%d"' % self.width
        if self.height:
            height = ' height="%d"' % self.height

        # External URLs and potentially local files are not embedded into the
        # notebook output.
        if not self.embed:
            url = self.url if self.url is not None else self.filename
            output = """<video src="{0}" controls {1} {2}>
      Your browser does not support the <code>video</code> element.
    </video>""".format(url, width, height)
            return output

        # Embedded videos are base64-encoded.
        mimetype = self.mimetype
        if self.filename is not None:
            if not mimetype:
                mimetype, _ = mimetypes.guess_type(self.filename)

            with open(self.filename, 'rb') as f:
                video = f.read()
        else:
            video = self.data
        if isinstance(video, str):
            # unicode input is already b64-encoded
            b64_video = video
        else:
            b64_video = b2a_base64(video).decode('ascii').rstrip()

        output = """<video controls {0} {1}>
 <source src="data:{2};base64,{3}" type="{2}">
 Your browser does not support the video tag.
 </video>""".format(width, height, mimetype, b64_video)
        return output

    def reload(self):
        # TODO
        pass


def preview_video(file: AbstractFile):
    video = Video(file.data, embed=True, mimetype=file.mime)
    display(video)


def preview_image(file: AbstractFile):
    img = Image(data=file.data)
    display(img)


PREVIEWERS = {
    'audio': preview_audio,
    'video': preview_video,
    'image': preview_image,
}


def preview(file: AbstractFile):
    type = file.mime
    cat = type.split('/')[0]
    previewer = PREVIEWERS.get(cat)
    if previewer:
        previewer(file)
    else:
        print('No previewer found for "{}"'.format(file.mime))
