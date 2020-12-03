; --- Explanation of Bibligraphy database entry ---

; semicolon at the beginning of the line is a comment
; it is recommended to use Notepad++ to edit these files
; filename is the entry ID (author + year + short title) without spaces, use space + date (ZA000 format) for old files to be ignored

; begin with the metadata to the publication
AU Author name, author surname; other author name, other author surname; etc
Y year
T title (use "" to indicate articles)
T (optional) multi-line title
P (optional) publication
P (optional) multi-line publication


; before summary: @@@ + site abbreviation (L: Literature, P: Politics, R: Religion, A: Art, Lg: Linguistics)
; use semicolon for multiple site association to the same summary (eg. @@@L;R;A), if there are other summaries for the same publication use @@@ again after the summary/notes
@@@L
SA summary author (abbreviation); other summary author; etc
SD summary date (day Month year or Month year)
TO (optional) topic; other topic; etc

Here goes the summary (after a new line), every line now is part of the summary (until another @@@ or @NOTES).
Use two new lines for a new paragraph.

In here you can use [Markdown](https://github.com/adam-p/markdown-here/wiki/Markdown-Cheatsheet) and dashes, quotes, ellipses (e.g. *italics* , **bold** , ***italics & bold***, [text](link.htm), ![image text](image.png), <<quotation marks>>, -- en-dash, ... ellipses).  
For complex formatting you can use HTML (e.g. 10<sup>th</sup>, <small>small text</small>).

To reference another entry you can use {B}site/ID_of_the_entry (e.g. {B}R/Abusch2015Gilgamesh).



; notes: @NOTES site/note_number
; if there are other notes use @NOTES again
@NOTES L/1.1
NA note author (abbreviation); other note author; etc
ND note date (day Month year or Month year)
CT (optional) category (used for sorting)
TO (optional) topic; other topic; etc

Here goes the note text (after a new line), it works the same way as the summary.
If the note has here a reference to a bibliography entry (e.g. {B}R/Abusch2015Gilgamesh), the note reference will be automatically added to the bibliography.

