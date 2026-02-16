import csv
import xml.etree.ElementTree as ET
from xml.dom import minidom
import argparse
import os

def create_xml_structure(csv_data):
    """
    Creates the XML structure from the given CSV data.
    """
    glossary = ET.Element("GLOSSARY")
    info = ET.SubElement(glossary, "INFO")

    # Static INFO elements based on the example XML
    ET.SubElement(info, "NAME").text = "Fogalomtár"
    ET.SubElement(info, "INTRO").text = ""
    ET.SubElement(info, "INTROFORMAT").text = "1"
    ET.SubElement(info, "ALLOWDUPLICATEDENTRIES").text = "0"
    ET.SubElement(info, "DISPLAYFORMAT").text = "dictionary"
    ET.SubElement(info, "SHOWSPECIAL").text = "1"
    ET.SubElement(info, "SHOWALPHABET").text = "1"
    ET.SubElement(info, "SHOWALL").text = "1"
    ET.SubElement(info, "ALLOWCOMMENTS").text = "0"
    ET.SubElement(info, "USEDYNALINK").text = "1"
    ET.SubElement(info, "DEFAULTAPPROVAL").text = "1"
    ET.SubElement(info, "GLOBALGLOSSARY").text = "0"
    ET.SubElement(info, "ENTBYPAGE").text = "10"

    entries = ET.SubElement(info, "ENTRIES")

    # Skip header row
    next(csv_data)

    for row in csv_data:
        concept, definition, tags = row

        entry = ET.SubElement(entries, "ENTRY")
        ET.SubElement(entry, "CONCEPT").text = concept
        
        # Wrap definition in the required HTML paragraph
        definition_html = f'<p dir="ltr" style="text-align: left;">{definition}<br/></p>'
        ET.SubElement(entry, "DEFINITION").text = definition_html
        
        # Static ENTRY elements
        ET.SubElement(entry, "FORMAT").text = "1"
        ET.SubElement(entry, "DEFINITIONTRUST").text = "0"
        ET.SubElement(entry, "USEDYNALINK").text = "0"
        ET.SubElement(entry, "CASESENSITIVE").text = "0"
        ET.SubElement(entry, "FULLMATCH").text = "0"
        ET.SubElement(entry, "TEACHERENTRY").text = "1"

        aliases = ET.SubElement(entry, "ALIASES")
        # Split tags into a list and create a separate ALIAS for each
        tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
        for tag_name in tag_list:
            alias = ET.SubElement(aliases, "ALIAS")
            ET.SubElement(alias, "NAME").text = tag_name

    return glossary

def main():
    """
    Main function to convert CSV to XML.
    """
    parser = argparse.ArgumentParser(description="Convert a CSV file to a Moodle-compatible XML glossary file.")
    parser.add_argument("input_csv", help="Path to the input CSV file.")
    parser.add_argument("output_xml", nargs='?', help="Optional: Path for the output XML file. Defaults to the input file name with an .xml extension.")
    args = parser.parse_args()

    output_xml_path = args.output_xml
    if not output_xml_path:
        base, _ = os.path.splitext(args.input_csv)
        output_xml_path = base + '.xml'

    try:
        with open(args.input_csv, 'r', encoding='utf-8') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=';')
            xml_data = create_xml_structure(csv_reader)

        # Pretty print the XML
        xml_string = ET.tostring(xml_data, 'utf-8')
        reparsed = minidom.parseString(xml_string)
        pretty_xml = reparsed.toprettyxml(indent="  ", encoding="UTF-8").decode()

        with open(output_xml_path, 'w', encoding='utf-8') as xml_file:
            xml_file.write(pretty_xml)
        
        print(f"Successfully converted '{args.input_csv}' to '{output_xml_path}'")

    except FileNotFoundError:
        print(f"Error: Input file not found at '{args.input_csv}'")

if __name__ == "__main__":
    main()

