from markdown.treeprocessors import Treeprocessor
from markdown.extensions import Extension


# ! currently NOT in use !

# add <Back to Top> for each last <p>
class BacktotopExtension(Extension):
    def extendMarkdown(self, md):
        md.registerExtension(self)
        md.treeprocessors.register(BacktotopTreeprocessor(md), 'backtotop', 1000)


class BacktotopTreeprocessor(Treeprocessor):
    def run(self, root):
        is_paragraph = False
        item_old = ''
        last_p = []
        for item in root.iter():
            last_p += [item_old] if is_paragraph and item.tag[0] == 'h' else []
            is_paragraph = True if item.tag == 'p' else False
            item_old = item
        else:
            last_p += [item_old] if is_paragraph else []
        for item in last_p:
            item.text += '\n<small><a href="#0">Back to top</a></small><br><br>'


def makeExtension(*args, **kwargs):
    return BacktotopExtension(**kwargs)



# [TOC]: see md.toc extension


