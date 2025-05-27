### Specifics of EPUBs downloaded from AO3
Observations about the EPUB files downloaded from AO3.

### Layout
The EPUB files I have seen from AO3 do not contain the OEBPS folder. The files that are typically stored in this directory are instead stored in the root.
An EPUB that I downloaded from Project Gutenberg *does* contain the OEBPS folder.
So long as the file `META-INF/container.xml` file correctly identifies the location of the content.opf file, the EPUB is still valid and should still display on an e-reader.

### XHTML files layout
| .xhtml File Name | Description |
| ---- | ---- |
| My_File_split_000.xhtml | Contains title, tags, stats etc. |
| My_File_split_001.xhtml | Contains title, summary, "see the end of the work for more notes" |
| My_File_split_002.xhtml | Contains the first chapter |
| My_File_split_NNN.xhtml | Contains end notes, works inspired by this, hyperlink to the work on AO3. |

Therefore, for a work with exactly one chapter we expect there to be 4 xhtml files. (Title/tags, Summary, Content, End Notes).