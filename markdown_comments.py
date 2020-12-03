from markdown.preprocessors import Preprocessor
from markdown.extensions import Extension


class CommentsExtension(Extension):
    def extendMarkdown(self, md):
        md.registerExtension(self)
        md.preprocessors.register(CommentRemover(md), 'comment_remover', 26)


class CommentRemover(Preprocessor):
    def run(self, lines):
        return [line for line in lines if not line.startswith(';')]
        # return [re.sub(r'<!---', PREFIX_PLACEHOLDER, line) for line in lines]


def makeExtension(*args, **kwargs):
    return CommentsExtension(**kwargs)
