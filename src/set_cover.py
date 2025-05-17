from pathlib import Path
from zipfile import ZipFile

from lxml import etree

# The path where the `mimetype` file should be stored.
MIMETYPE_PATH = "mimetype"

# The data that the file `mimetype` should contain.
MIMETYPE_DATA = b"application/epub+zip"

# The expected path to the container.xml file
CONTAINER_XML_PATH = "META-INF/container.xml"

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


def validate_file_exists(file_path: str):
    """Validate the file `file_path` exists. Raise an error otherwise.

    Args:
        file_path (str): Path of the file to check.

    Raises:
        Exception: Exception is the file does not exist.
    """
    if not Path(file_path).exists():
        raise RuntimeError(f"No such file {file_path}")


def copy_zip_with_replacements(
    source_zip_path: str,
    destination_zip_path: str,
    file_replacements: dict,
    files_to_add: dict
):
    """Copy source_zip_path to destination_zip_path but replace all files
    in file_replacements with the contents as the corresponding value and add
    each entry from files_to_add to the destination specified by the
    corresponding value.

    Args:
        source_zip_path (str): Source path of the EPUB to copy.
        destination_zip_path (str): Destination to write the updated EPUB to.
        file_replacements (dict, optional): All replacements to make from
            source_zip_path to destination_zip_path where the key is the
            file name and the value is the updated file contents.
        files_to_add (dict, optional): All files to add to output_zip_file
        where the key is the path to the file to copy and the value is the
        destination in the EPUB to write to.
    """
    replacements_made = 0

    with ZipFile(source_zip_path, 'r') as zip_src:
        with ZipFile(destination_zip_path, 'w') as zip_out:
            for item in zip_src.infolist():
                if item.filename in files_to_add.values():
                    print(
                        f"## WARNING!! ## {item.filename} is already present "
                        f"in src file. Are you sure a cover image has not "
                        f"already been set? Overwriting the file..."
                    )
                    # Skip writing this file to zip_out so that files_to_add
                    # overwrites the current file.
                    continue

                if item.filename in file_replacements:
                    zip_out.writestr(
                        item.filename,
                        file_replacements[item.filename]
                    )
                    replacements_made += 1
                else:
                    original_file_contents = zip_src.read(item.filename)
                    zip_out.writestr(item, original_file_contents)

            for file_name, file_destination in files_to_add.items():
                zip_out.write(file_name, file_destination)

    if replacements_made != len(file_replacements):
        print(
            f"WARNING - expected {len(file_replacements)} replacements "
            f"but made {replacements_made}"
        )


def _check_item_tag_present_in_manifest(manifest) -> bool:
    """Determine if the expected item tag is present in the manifest Element.
    <item href="cover.jpg" id="cover" media-type="image/jpeg"/>

    Args:
        manifest (lxml.etree._Element): etree Element of manifest tag.

    Returns:
        bool: Returns True if the expected item tag is present in manifest
            and False otherwise.
    """
    for item in manifest.findall(".//{*}item"):
        if all((
            item.get("href") == COVER_NAME,
            item.get("id") == "cover",
            item.get("media-type") == "image/jpeg",
        )):
            return True
    return False


def _check_meta_tag_present_in_metadata(metadata) -> bool:
    """Determine if the expected meta tag is present in the metadara Element.
    <meta name="cover" content="cover"/>

    Args:
        manifest (lxml.etree._Element): etree Element of manifest tag.

    Returns:
        bool: Returns True if the expected meta tag is present in manifest
            and False otherwise.
    """
    for meta in metadata.findall(".//{*}meta"):
        if (meta.get("name") == "cover") and (meta.get("content") == "cover"):
            return True
    return False


def set_cover(src_file: str, dst_file: str, img_to_add) -> bool:
    """Set the cover of the src_file EPUB to have the cover img_to_add and
    write the output to dst_file.

    Args:
        src_file (str): The source EPUB to set the cover of.
        dst_file (str): The output EPUB.
        img_to_add (str): The path to the cover image to use.

    Raises:
        Exception: Cannot find container.xml in the src_file.

    Returns:
        bool: Return True if the EPUB output was created successfully
            and False otherwise.
    """
    validate_file_exists(src_file)
    validate_file_exists(img_to_add)

    if Path(dst_file).exists():
        continue_str = input(
            f"WARNING: The output_file: {dst_file} already exists. "
            f"Continuing will OVERWRITE this file. "
            f"Would you like to continue? "
        )
        if continue_str.upper() != "Y" and continue_str.upper() != "YES":
            return False

    with ZipFile(src_file) as zip_file:
        validate_mimetype(zip_file)
        content_opf_path = get_location_of_content_opf_file(zip_file)

        try:
            content_opf_xml = zip_file.read(content_opf_path)
        except KeyError as exception:
            raise KeyError("Cannot find {content_opf_path}") from exception

        parser_remove_blank_text = etree.XMLParser(remove_blank_text=True)
        content_opf_xml_root = etree.fromstring(
            content_opf_xml,
            parser_remove_blank_text
        )

        path_to_cover_in_zipfile = str(
            Path(content_opf_path).parent / COVER_NAME
        )

        namespace = {"ns": "*"}
        manifest = content_opf_xml_root.find("ns:manifest", namespace)
        if manifest is not None:
            # Add <item href="cover.jpg" id="cover" media-type="image/jpeg"/>
            # to <manifest> </manifest> if not present.
            if not _check_item_tag_present_in_manifest(manifest):
                cover_item = etree.Element("item", {
                    "href": path_to_cover_in_zipfile,
                    "id": "cover",
                    "media-type": "image/jpeg",
                })

                manifest.append(cover_item)
        else:
            print("## WARNING!! ## Unable to find manifest tag")

        metadata = content_opf_xml_root.find("ns:metadata", namespace)
        if metadata is not None:
            # Add <meta name="cover" content="cover"/>
            # to <metadata> </metadata> if not present.
            if not _check_meta_tag_present_in_metadata(metadata):
                meta_tag_cover = etree.Element("meta", {
                    "name": "cover",
                    "content": "cover"
                })
                metadata.append(meta_tag_cover)
        else:
            print("## WARNING!! ## Unable to find metadata tag")

    tree = etree.ElementTree(content_opf_xml_root)

    # Update with the updated content.opf file and add the cover.jpg file
    file_replacements = {
        content_opf_path: etree.tostring(tree, pretty_print=True)
    }
    files_to_add = {img_to_add: path_to_cover_in_zipfile}

    copy_zip_with_replacements(
        src_file,
        dst_file,
        file_replacements,
        files_to_add
    )
    return True


def main():
    src_file = "test_epubs/input.epub"
    dst_file = "test_epubs/output.epub"
    cover_image = "test_epubs/cover.jpg"
    if set_cover(src_file, dst_file, cover_image):
        print(f"Written output to {dst_file}")
    else:
        print("Aborted")


if __name__ == "__main__":
    main()
