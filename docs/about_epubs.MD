# About EPUB files

EPUB is an e-book file format that uses the ".epub" file extension.

<details>
<summary>Glossary</summary>
<b>EPUB:</b> Electronic Publication<br>
<b>NCX:</b> Navigation Control file for XML<br>
<b>OEB:</b> Open eBook<br>
<b>OEBPS:</b> Open eBook Publication Structure <br>
<b>OPF:</b> Open Package Format<br>
<b>OPS:</b> Open Publication Structure<br>
<b>XHTML:</b> Extensible HyperText Markup Language
</details>
<br>
An EPUB file is essentially a ZIP archive file. We can rename it to .zip and extract it.


## Overview
The example EPUB files I have looked at have this format.
```
MyFile.epub
¦   META-INF
¦   ¦   container.xml
¦   MyFile_split_000.xhtml
¦   MyFile_split_001.xhtml
¦   MyFile_split_002.xhtml
¦   MyFile_split_003.xhtml
¦   content.opf
¦   mimetype
¦   page_styles.css
¦   stylesheet.css
¦   toc.ncx
```

NOTE - according to Wikipedia the content is typically stored in an OEBPS folder as so (1)
```
--ZIP Container--
mimetype
META-INF/
  container.xml
OEBPS/
  content.opf
  chapter1.xhtml
  ch1-pic.png
  css/
    style.css
    myfont.otf
```

## container.xml
Contains a reference to the package document (.opf)
```xml
<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
   <rootfiles>
      <rootfile full-path="content.opf" media-type="application/oebps-package+xml"/>
   </rootfiles>
</container>
```

## XHTML files
The content is contained in the XHTML files. Here is an example skeleton (1)
```xhtml
<?xml version="1.0" encoding="UTF-8" ?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
  <head>
    <meta http-equiv="Content-Type" content="application/xhtml+xml; charset=utf-8" />
    <title>Pride and Prejudice</title>
    <link rel="stylesheet" href="css/main.css" type="text/css" />
  </head>
  <body>
    ...
  </body>
</html>
```

## content.opf
The content.opf file typically contains metadata, file manifest, and linear reading order.
It can contain the elements
- metadata including title, language, subject etc. (2)
- manifest
- spine
- guide


Here is the skeleton of the example I am using. Note it does not have the guide element.
```xml
<package>
    <metadata>
      <dc:title>Example Title</dc:title>
      <dc:language>en</dc:language>
      ...
    </metadata>

    <manifest>
      <item id="html2" href="MyFile_split_000.xhtml" media-type="application/xhtml+xml"/>
      <item id="html1" href="MyFile_split_001.xhtml" media-type="application/xhtml+xml"/>
      <item id="page_css" href="page_styles.css" media-type="text/css"/>
      <item id="css" href="stylesheet.css" media-type="text/css"/>
      <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>
    </manifest>

    <spine toc="ncx">
      <itemref idref="html2"/>
      <itemref idref="html1"/>
    </spine>
</package>
```

## mimetype
"The first file in the archive must be the mimetype file. It must be unencrypted and uncompressed so that non-ZIP utilities can read the mimetype. The mimetype file must be an ASCII file that contains the string "application/epub+zip". This file provides a more reliable way for applications to identify the mimetype of the file than just the .epub extension" (1).

Example mimetype file
```mimetype
application/epub+zip
```

## stylesheet.css
Contains the CSS that can be used in the xhtml files.

## toc.ncx
Contains hierarchical table of contents.
```xml
<?xml version='1.0' encoding='utf-8'?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1" xml:lang="en">
  <head>
    <meta name="dtb:uid" content="3d855474-2b03-4313-b727-ff6b08a91cdf"/>
    <meta name="dtb:depth" content="2"/>
    <meta name="dtb:generator" content="calibre (6.13.0)"/>
    <meta name="dtb:totalPageCount" content="0"/>
    <meta name="dtb:maxPageNumber" content="0"/>
  </head>
  <docTitle>
    <text>My File</text>
  </docTitle>
  <navMap>
    <navPoint id="uptfVODR44GwKPJcHJnEUB7" playOrder="1">
      <navLabel>
        <text>Preface</text>
      </navLabel>
      <content src="MyFile_split_000.xhtml"/>
    </navPoint>
    <navPoint id="uBrr6xveQbMotIkSC7te8A8" playOrder="2">
      <navLabel>
        <text>My File</text>
      </navLabel>
      <content src="MyFile_split_002.xhtml"/>
    </navPoint>
    <navPoint id="uPiKCjEZqwuvK7qOp5GqH75" playOrder="3">
      <navLabel>
        <text>Afterword</text>
      </navLabel>
      <content src="MyFile_split_003.xhtml"/>
    </navPoint>
  </navMap>
</ncx>

```

###### References
(1) https://en.wikipedia.org/wiki/EPUB <br>
(2) https://standardebooks.org/manual/1.6.0/9-metadata