Schema.org JSON Schema Generator
================================

Python script that generates a Draft 4 JSON Schema for `HTML Microdata`_ encoded in JSON using Schema.org vocabulary, which includes LRMI extensions.

Author
------
Jim Klo


What This Does
--------------

This project generates a rather large and monolithic `JSON Schema`_  by using the `JSON version`_ of the `Schema.org`_ vocabulary encoded into `HTML Microdata`_ in JSON. The result is then patched with some extensions for better validation of `LRMI`_ properties. The output of this script is ```lrmi.json```.



Dependencies
------------
`jsonschema`_ : a `JSON Schema`_ validation module.

`jsonpatch`_  : a `JSON Patch`_ module


Installation
------------

I prefer to use `virtualenv`_ and I highly recommend you install and create a virtual python environment first and activated.

To install dependencies:

.. sourcecode::

    pip install jsonschema=1.3.0 jsonpatch==1.0

and then you're done.


Usage
-----

.. sourcecode::

    $ ./make_lrmi_schema.py -h
    usage: make_lrmi_schema.py [-h] [--regen] [--test]

    optional arguments:
      -h, --help   show this help message and exit
      --regen, -r  regen schema
      --test, -t   test schema


License
-------

.. sourcecode::

    Copyright 2013 SRI International

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.

.. _HTML Microdata: http://www.w3.org/TR/microdata/#json

.. _LRMI: http://lrmi.net

.. _jsonpatch: https://github.com/stefankoegl/python-json-patch

.. _JSON Patch: http://tools.ietf.org/html/rfc6902

.. _Schema.org: http://schema.org

.. _JSON Schema: http://json-schema.org

.. _JSON version: http://schema.rdfs.org/all.json

.. _jsonschema: https://github.com/Julian/jsonschema

.. _virtualenv: https://pypi.python.org/pypi/virtualenv 