from lxml import etree
from pathlib import Path
from zipfile import ZipFile


# The path where the `mimetype` file should be stored.
MIMETYPE_PATH = "mimetype"

# The data that the file `mimetype` should contain.
MIMETYPE_DATA = b"application/epub+zip"

# The expected path to the container.xml file
CONTAINER_XML_PATH = "META-INF/container.xml"

# The default file name to write the the cover image to.
COVER_NAME = "cover.jpg"


def validate_mimetype(zObject):
    """Validate that an opened ZIP archive contains the expected mimetype file.
    Raise an exception if this is not the case.

    Args:
        zObject zipfile.ZipFile: File handle to open EPUB file to test it contains the expected mimetype file.

    Raises:
        Exception: mimetype file is not found.
        Exception: mimetype file is found but it does not contain the expected contents.
    """
    try:
        mimetype = zObject.read(MIMETYPE_PATH)
    except KeyError:
        raise Exception(f"{MIMETYPE_DATA} file not found. Is this definitely an EPUB file?")
    
    if MIMETYPE_DATA != mimetype:
        raise Exception(f"Found {MIMETYPE_PATH} file but it contains {mimetype}. Expected: {MIMETYPE_DATA}")
    
def get_location_of_content_opf_file(zObject):
    """Get the location of the content.opf from the container.xml file.

    Args:
        zObject (zipfile.ZipFile): File handle to open EPUB file.

    Raises:
        Exception: Cannot find container.xml file.
        Exception: container.xml is not in the expected format.

    Returns:
        str: Returns the path to the content.opf file obtained from the container.xml file.
    """
    try:
        container_xml = zObject.read(CONTAINER_XML_PATH)
    except KeyError:
        raise Exception("Cannot find {CONTAINER_XML_PATH}")
    
    container_root = etree.fromstring(container_xml)

    namespace = {"ns": "urn:oasis:names:tc:opendocument:xmlns:container"}
    rootfile = container_root.find("ns:rootfiles/ns:rootfile", namespace)

    if rootfile is None:
        raise Exception("Unable to find <rootfiles> <rootfile> in {CONTAINER_XML_PATH}")
    
    return rootfile.get("full-path")
        

def validate_file_exists(file_path: str):
    """Validate the file `file_path` exists. Raise an error otherwise.

    Args:
        file_path (str): Path of the file to check.

    Raises:
        Exception: Exception is the file does not exist.
    """
    if not Path(file_path).exists():
        raise Exception(f"No such file {file_path}")

def copy_zip_with_replacements(source_zip_path: str, destination_zip_path: str, file_replacements: dict = {}, files_to_add: dict = {}):
    """Copy source_zip_path to destination_zip_path but replace all files 
    in file_replacements with the contents as the corresponding value and add each entry
    from files_to_add to the destination specified by the corresponding value.

    Args:
        source_zip_path (str): The source path of the EPUB to copy.
        destination_zip_path (str): The destination path to write the updated EPUB to.
        file_replacements (dict, optional): All replacements to make from source_zip_path to 
            destination_zip_path where the key is the file name and the value is the 
            updated file contents. Defaults to {}.
        files_to_add (dict, optional): All files to add to copy to output_zip_file where the
        key is the path to the file to copy and the value is the destination in the
        EPUB to write to. Defaults to {}.
    """
    replacements_made = 0
    
    with ZipFile(source_zip_path, 'r') as zip_src:
        with ZipFile(destination_zip_path, 'w') as zip_out:
            for item in zip_src.infolist():
                if item.filename in files_to_add.values(): 
                    print(f"## WARNING!! ## {item.filename} is already present in src file. Are you sure a cover image has not already been set? Overwriting the file...")
                    # Skip writing this file to zip_out so that files_to_add overwrites the current file.
                    continue

                if item.filename in file_replacements:
                    zip_out.writestr(item.filename, file_replacements[item.filename])
                    replacements_made += 1
                else:
                    original_file_contents = zip_src.read(item.filename)
                    zip_out.writestr(item, original_file_contents)
        
            for file_name, file_destination in files_to_add.items():
                zip_out.write(file_name, file_destination)
    
    if replacements_made != len(file_replacements):
        print(f"WARNING - expected {len(file_replacements)} replacements but made {replacements_made}")


def _check_item_tag_present_in_manifest(manifest) -> bool:
    """Determine if the tag expected item tag is present in the manifest Element.
    <item href="cover.jpg" id="cover" media-type="image/jpeg"/>
    
    Args:
        manifest (lxml.etree._Element): etree Element of manifest tag.

    Returns:
        bool: Returns True if the expected item tag is present in manifest and False otherwise.
    """
    for item in manifest.findall("item"):
        if all((
            item.get("href") == COVER_NAME,
            item.get("id") == "cover",
            item.get("media-type") == "image/jpeg",
        )):
            return True
    return False

def _check_meta_tag_present_in_manifest(manifest) -> bool:
    """Determine if the expected meta tag is present in the manifest Element. 
    <meta name="cover" content="cover"/>

    Args:
        manifest (lxml.etree._Element): etree Element of manifest tag.

    Returns:
        bool: Returns True if the expected meta tag is present in manifest and False otherwise.
    """
    for meta in manifest.findall("meta"):
        if (meta.get("name") == "cover") and (meta.get("content") == "cover"):
            return True
    return False

def set_cover(src_file: str, dst_file:str, img_to_add) -> bool:
    """Set the cover of the src_file EPUB to have the cover img_to_add and write the output to dst_file.

    Args:
        src_file (str): The source EPUB to set the cover of.
        dst_file (str): The output EPUB.
        img_to_add (str): The path to the cover image to use.

    Raises:
        Exception: Cannot find container.xml in the src_file.

    Returns:
        bool: Return True if the EPUB output was created successfully and False otherwise.
    """
    validate_file_exists(src_file)
    validate_file_exists(img_to_add)
    
    if Path(dst_file).exists():
        continue_str = input(f"WARNING: The output_file: {dst_file} already exists. Continuing will OVERWRITE this file. Would you like to continue? ")
        if continue_str.upper() != "Y" and continue_str.upper() != "YES":
            return False

    with ZipFile(src_file) as zObject:
        validate_mimetype(zObject)
        content_opf_path = get_location_of_content_opf_file(zObject)

        try:
            content_opf_xml = zObject.read(content_opf_path)
        except KeyError:
            raise Exception("Cannot find {content_opf_path}")

        parser_remove_blank_text = etree.XMLParser(remove_blank_text=True)
        content_opf_xml_root = etree.fromstring(content_opf_xml, parser_remove_blank_text)
        
        path_to_cover_in_zipfile = str(Path(content_opf_path).parent / COVER_NAME)

        namespace = {"ns": "http://www.idpf.org/2007/opf"}
        manifest = content_opf_xml_root.find("ns:manifest", namespace)
        if manifest is not None:
            # Add <item href="cover.jpg" id="cover" media-type="image/jpeg"/> to <manifest> </manifest> if not present.
            if not _check_item_tag_present_in_manifest(manifest):
                cover_item = etree.Element("item", {
                    "href": path_to_cover_in_zipfile,
                    "id": "cover",
                    "media-type": "image/jpeg",
                })

                manifest.append(cover_item)

        metadata = content_opf_xml_root.find("ns:metadata", namespace)
        if metadata is not None:
            # Add <meta name="cover" content="cover"/> to <metadata> </metadata> if not present.
            if not _check_meta_tag_present_in_manifest(manifest):
                meta_tag_cover = etree.Element("meta", {
                    "name": "cover",
                    "content": "cover"
                })
                metadata.append(meta_tag_cover)

    tree = etree.ElementTree(content_opf_xml_root)

    # For the output EPUB update with the updated content.opf file and add the cover.jpg file.
    file_replacements = {content_opf_path: etree.tostring(tree, pretty_print=True)}
    files_to_add = {img_to_add: path_to_cover_in_zipfile}

    copy_zip_with_replacements(src_file, dst_file, file_replacements, files_to_add)
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