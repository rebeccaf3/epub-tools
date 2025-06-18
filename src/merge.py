from argparse import ArgumentParser
from pathlib import Path
from zipfile import ZipFile

from lxml import etree

from utils.epub_utils import (CONTAINER_XML_PATH, MIMETYPE_DATA, MIMETYPE_PATH,
                              add_prefix_to_file_path,
                              get_content_opf_xml_root,
                              get_location_of_content_opf_file, get_toc_ncx)


def epub_merge(files_to_merge: list[str], dst_file: str) -> bool:
    # Get "combined" metadata
    # Prepend for all files in <manifest> tags of content.opf the file index
    # Do the same with the ID which is referenced in the <spine> tags
    # Write to updated zip file.

    with ZipFile(dst_file, "w") as zip_out:
        # Write required mimetype file
        zip_out.writestr(MIMETYPE_PATH, MIMETYPE_DATA)

        # metadata = None
        namespace = {"ns": "*"}

        # The chosen location to store the content.opf in the output file.
        # This will be equivalent to the first content.opf location we
        # encounter in the list of files to merge.
        output_content_opf_location = None

        # The output content.opf etree
        output_content_opf_tree = None

        output_toc_path = None
        output_toc_navmap = None

        for input_file_index, input_file in enumerate(files_to_merge):
            with ZipFile(input_file, 'r') as zip_file:
                content_opf_path = get_location_of_content_opf_file(zip_file)
                if output_content_opf_location is None:
                    output_content_opf_location = content_opf_path
                    container_xml_contents = zip_file.read(CONTAINER_XML_PATH)
                    zip_out.writestr(CONTAINER_XML_PATH, container_xml_contents)

                content_opf_parent = Path(content_opf_path).parent

                content_opf_xml_root = get_content_opf_xml_root(
                    zip_file, content_opf_path
                )
                output_opf_xml_root = get_content_opf_xml_root(
                    zip_file, content_opf_path
                )
                if output_content_opf_tree is None:
                    output_content_opf_tree = etree.ElementTree(
                        output_opf_xml_root
                    )
                    output_manifest = output_content_opf_tree.find("ns:manifest", namespace)
                    if output_manifest is None:
                        print("No manifest tag found in content.opf")
                        return False
                    output_manifest.clear()

                    output_spine = output_content_opf_tree.find("ns:spine", namespace)
                    if output_spine is None:
                        print("No spine tag found in content.opf")
                        return False
                    else:
                        output_spine.clear()

                    # output_toc_navmap =


                # metadata = content_opf_xml_root.find("ns:metadata", namespace)
                # print(metadata)

                # Loop through <manifest> entries
                manifest = content_opf_xml_root.find("ns:manifest", namespace)
                for i in manifest:
                    # To ensure that all item IDs in the manifest block are
                    # unique, prepend the index of the input file.
                    current_id = i.get("id")
                    if not current_id:
                        print("ERROR - expected id tag in manifest")
                        return False

                    href_value = i.get("href")
                    path_i = str(content_opf_parent / href_value)

                    if i.get("media-type") in ("application/xhtml+xml", "text/css"):
                        file_prefix = str(input_file_index) + '_'
                        updated_id = file_prefix + current_id

                        i.set("id", updated_id)
                        
                        file_contents = zip_file.read(path_i)

                        updated_path = add_prefix_to_file_path(
                            file_prefix,
                            path_i
                        )
                        zip_out.writestr(updated_path, file_contents)
                        i.set("href", updated_path)
                
                        output_manifest.append(i)
                    elif i.get("media-type") == "application/x-dtbncx+xml": 
                        if output_toc_navmap is None:
                            # If this is the first toc.ncx file encountered,
                            # update the content.opf manifest to include the
                            # toc.ncx file and set the output toc navmap
                            output_manifest.append(i)
                            output_toc_path = path_i
                            output_toc_navmap = get_toc_ncx(zip_file, path_i)
                        else:
                            # If this is not the first toc.ncx, update the
                            # output toc navmap with the entries
                            toc_navmap = get_toc_ncx(zip_file, path_i)
                            navmap = toc_navmap.find("ns:navMap", namespace)
                            for navpoint in navmap:
                                new_playorder = str(int(navpoint.get("playOrder")) + len(output_toc_navmap))
                                navpoint.set("playOrder", new_playorder)
                                output_toc_navmap.append(navpoint)

                # Loop through <spine> entries
                spine = content_opf_xml_root.find("ns:spine", namespace)
                for i in spine:
                    current_id = i.get("idref")
                    if not current_id:
                        print("ERROR - expected id tag in manifest")
                        return False

                    file_prefix = str(input_file_index) + '_'
                    updated_id = file_prefix + current_id
                    i.set("idref", updated_id)
                    output_spine.append(i)

        output_opf_as_string = etree.tostring(output_content_opf_tree, pretty_print=True)
        zip_out.writestr(output_content_opf_location, output_opf_as_string)

        if output_toc_navmap is not None:
            toc_ncx_as_str = etree.tostring(output_toc_navmap, pretty_print=True)
            zip_out.writestr(output_toc_path, toc_ncx_as_str)

    return True


def main():
    parser = ArgumentParser()
    parser.add_argument(
        "src_file1", help="The path to the first EPUB file", type=str
    )
    parser.add_argument(
        "src_file2", help="The path to the second EPUB file", type=str
    )
    parser.add_argument(
        "dst_file", help="The destination to save the output EPUB to", type=str
    )

    args = parser.parse_args()

    epub_merge([args.src_file1, args.src_file2], args.dst_file)


if __name__ == "__main__":
    main()
