"""Update the _private_dict.py file using data from the GDCM private dict."""

import xml.etree.ElementTree as ET
from urllib.request import urlopen
from pathlib import Path
from collections import defaultdict


GDCM_PRIVATE_DICT = (
    r"https://raw.githubusercontent.com/malaterre/GDCM/"
    r"master/Source/DataDictionary/privatedicts.xml"
)
PYDICOM_DICT_NAME = (
    "private_dictionaries: dict[str, dict[str, tuple[str, str, str, str]]]"
)
_PKG_DIRECTORY = Path(__file__).parent.parent.parent / "src" / "pydicom"
PYDICOM_DICT_FILENAME = _PKG_DIRECTORY / "_private_dict.py"
PYDICOM_DICT_DOCSTRING = """DICOM private dictionary auto-generated by generate_private_dict.py.

Data generated from GDCM project\'s private dictionary.

The outer dictionary key is the Private Creator name ("owner"), while the inner
dictionary key is a map of DICOM tag to (VR, VM, name, is_retired).
"""


def parse_private_docbook(doc_root):
    """Return a dict containing the private dictionary data"""
    # Excerpt for understanding formatting, from GDCM file taken 2023-09
    # <?xml version="1.0" encoding="UTF-8"?>
    # <dict>
    # <entry group="0021" element="0010" vr="SQ" vm="1" name="?" owner="SIEMENS MR FMRI"/>
    # ...first "xx" element
    # <entry owner="1.2.840.113663.1" group="0029" element="xx00" vr="US" vm="1" name="?"/>
    # ...last element
    # <entry owner="syngoDynamics" group="0021" element="xxae" vr="OB" vm="1" name="?"/>
    # </dict>

    entries = defaultdict(dict)
    for entry in root:
        owner = entry.attrib["owner"]
        tag = entry.attrib["group"].upper() + entry.attrib["element"].upper()
        tag = tag.replace("XX", "xx")
        vr = entry.attrib["vr"]
        vm = entry.attrib["vm"]
        name = entry.attrib["name"].replace("\\", "\\\\")  # escape backslashes

        # Convert unknown element names to 'Unknown'
        if name == "?":
            name = "Unknown"

        entries[owner][tag] = (vr, vm, name)

    return entries


def write_dict(fp, dict_name, dict_entries):
    """Write the `dict_name` dict to file `fp`.

    Dict Format
    -----------
    private_dictionaries = {
        'CREATOR_1' : {
            '0029xx00': ('US', '1', 'Unknown', ''),
            '0029xx01': ('US', '1', 'Unknown', ''),
        },
        ...
        'CREATOR_N' : {
            '0029xx00': ('US', '1', 'Unknown', ''),
            '0029xx01': ('US', '1', 'Unknown', ''),
        },
    }

    Parameters
    ----------
    fp : file
        The file to write the dict to.
    dict_name : str
        The name of the dict variable.
    attributes : list of str
        List of attributes of the dict entries.
    """
    fp.write(f"\n{dict_name} = {{\n")
    for owner in sorted(dict_entries):
        fp.write(f"    '{owner}': {{\n")
        for tag in sorted(dict_entries[owner]):
            vr, vm, name = dict_entries[owner][tag]
            quote = '"' if "'" in name else "'"
            fp.write(
                f"""        '{tag}': ('{vr}', '{vm}', {quote}{name}{quote}, ''),  # noqa\n"""
            )
        fp.write("    },\n")
    fp.write("}\n")


if __name__ == "__main__":
    with urlopen(GDCM_PRIVATE_DICT) as response:
        root = ET.fromstring(response.read().decode("utf-8"))

    entries = parse_private_docbook(root)

    with open(PYDICOM_DICT_FILENAME, "w", encoding="utf8") as py_file:
        py_file.write('"""' + PYDICOM_DICT_DOCSTRING + '"""')
        py_file.write("\n\n")
        write_dict(py_file, PYDICOM_DICT_NAME, entries)
