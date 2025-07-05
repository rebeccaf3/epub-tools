from pathlib import Path

from lxml import etree

CONTAINER_XML_PARENT = "META-INF/"

# The expected path to the container.xml file
CONTAINER_XML_PATH = "META-INF/container.xml"

# The path where the `mimetype` file should be stored.
MIMETYPE_PATH = "mimetype"

# The data that the file `mimetype` should contain.
MIMETYPE_DATA = b"application/epub+zip"

# The default file name to write the the cover image to.
COVER_NAME = "cover.jpg"


def validate_mimetype(zip_file):
    """Validate that an opened ZIP archive contains the expected mimetype file.
    Raise an exception if this is not the case.

    Args:
        zip_file zipfile.ZipFile: File handle to open EPUB file to test it
        contains the expected mimetype file.

    Raises:
        Exception: mimetype file is not found.
        Exception: mimetype file is found
            but it does not contain the expected contents.
    """
    try:
        mimetype = zip_file.read(MIMETYPE_PATH)
    except KeyError as e:
        raise KeyError(
            f"{MIMETYPE_PATH} file not found. Is this definitely an EPUB file?"
        ) from e

    if MIMETYPE_DATA != mimetype:
        raise RuntimeError(
            f"Found {MIMETYPE_PATH} file but it contains {mimetype}. "
            f"Expected: {MIMETYPE_DATA!r}"
        )
    

def merge_metadata(output_opf_root, current_opf_root):
    """
    Merge metadata from current_opf_root to the metadata in output_opf_root.
    This will add all unique subject tags and combine the titles.

    Args:
        output_opf_root: The output content.opf xml root to be written to.
        current_opf_root: The content.opf xml root to merge into output.
    """
    if output_opf_root is None:
        return current_opf_root

    namespace = {"ns": "*"}

    output_metadata = output_opf_root.find("ns:metadata", namespace)
    metadata = current_opf_root.find("ns:metadata", namespace)

    # Add all unique subject tags
    subject_tags = metadata.findall("ns:subject", namespace)
    for i in subject_tags:
        if i.text not in [j.text for j in output_metadata.findall("ns:subject", namespace)]:
            output_metadata.append(i)

    # The string to delimit the title with
    title_delimiter = " & "

    # Update title tag to include both titles
    output_title = output_metadata.find("ns:title", namespace)
    metadata_title_text = metadata.find("ns:title", namespace).text
    output_title.text = output_title.text + title_delimiter + metadata_title_text


def get_location_of_content_opf_file(zip_file):
    """Get the location of the content.opf from the container.xml file.

    Args:
        zip_file (zipfile.ZipFile): File handle to open EPUB file.

    Raises:
        Exception: Cannot find container.xml file.
        Exception: container.xml is not in the expected format.

    Returns:
        str: Returns the path to the content.opf file
            obtained from the container.xml file.
    """
    try:
        container_xml = zip_file.read(CONTAINER_XML_PATH)
    except KeyError as exception:
        raise KeyError("Cannot find {CONTAINER_XML_PATH}") from exception

    container_root = etree.fromstring(container_xml)

    namespace = {"ns": "urn:oasis:names:tc:opendocument:xmlns:container"}
    rootfile = container_root.find("ns:rootfiles/ns:rootfile", namespace)

    if rootfile is None:
        raise RuntimeError(
            "Unable to find <rootfiles> <rootfile> in {CONTAINER_XML_PATH}"
        )

    return rootfile.get("full-path")


def get_toc_ncx(zip_file, toc_ncx_path):
    try:
        toc_ncx_xml = zip_file.read(toc_ncx_path)
    except KeyError as exception:
        raise KeyError("Cannot find {toc_ncx_path}") from exception

    parser_remove_blank_text = etree.XMLParser(remove_blank_text=True)
    return etree.fromstring(toc_ncx_xml, parser_remove_blank_text)


def get_content_opf_xml_root(zip_file, content_opf_path): 
    try:
        content_opf_xml = zip_file.read(content_opf_path)
    except KeyError as exception:
        raise KeyError("Cannot find {content_opf_path}") from exception

    parser_remove_blank_text = etree.XMLParser(remove_blank_text=True)
    return etree.fromstring(content_opf_xml, parser_remove_blank_text)


def replace_all_hrefs(file_contents, updated_hrefs) -> str:
    root = etree.fromstring(file_contents)
    elements_with_href = [root] if "href" in root.attrib else []
    elements_with_href.extend(root.findall('.//*[@href]'))
    for e in elements_with_href:
        current_href_value = e.attrib["href"]
        if current_href_value in updated_hrefs:
            e.set("href", updated_hrefs[current_href_value])
    return etree.tostring(root, pretty_print=True)


def replace_all_src_element(root, updated_src):
    elements_with_src = [root] if "src" in root.attrib else []
    elements_with_src.extend(root.findall('.//*[@src]'))
    for e in elements_with_src:
        current_src_value = e.attrib["src"]
        if current_src_value in updated_src:
            e.set("src", updated_src[current_src_value])
    return root


def replace_all_src(file_contents, updated_src) -> str:
    root = replace_all_src_element(etree.fromstring(file_contents), updated_src)
    return etree.tostring(root, pretty_print=True)


def add_prefix_to_file_path(prefix: str, file_path: str) -> str:
    # For example if prefix is "0_" and file_path is "C:/Users/test.txt"
    # The return value is "C:/Users/0_test.txt"
    return str(Path(file_path).parent / (prefix + Path(file_path).name))
