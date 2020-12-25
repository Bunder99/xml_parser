Simple XML parser version 0.1
---
Tested on python 3.7.3

Installation:
---
git clone https://github.com/Bunder99/xml_parser.git && cd xml_parser

python3 -m venv env

source env/bin/activate

pip install -r requirements.txt

Usage:
---
python xml_parser.py -h

Testing with pytest on included test.xml:
---
  pytest test_xml_parser.py
