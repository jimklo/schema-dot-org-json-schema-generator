#! /usr/bin/env python

   # Copyright 2013 SRI International

   # Licensed under the Apache License, Version 2.0 (the "License");
   # you may not use this file except in compliance with the License.
   # You may obtain a copy of the License at

   #     http://www.apache.org/licenses/LICENSE-2.0

   # Unless required by applicable law or agreed to in writing, software
   # distributed under the License is distributed on an "AS IS" BASIS,
   # WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   # See the License for the specific language governing permissions and
   # limitations under the License.

import urllib2, json, pprint, jsonschema, jsonpatch

all_schema_org = json.load(urllib2.urlopen("http://schema.rdfs.org/all.json"))

# all_schema_org = json.load(open("schemas/schema-rdfs-org.json"))

lrmi_mixin = json.load(open("schemas/backup-mixin.json"))

log = open("log.json", "w")

json_schema = json.load(open("schemas/schema-org-json-microdata.json"))


def get_prop_schema(prop_name):
    prop_def = all_schema_org["properties"][prop_name]
    prop_schema = {
        "title": prop_def["label"],
        "description": prop_def["comment_plain"],
        "type": "array"
    }

    if len(prop_def["ranges"]) > 1:
        prop_schema["items"] = {
            "oneOf": map(lambda x: { "$ref": "#/definitions/{0}".format(x)}, prop_def["ranges"])
        }
    elif len(prop_def["ranges"]) == 1:
        prop_schema["items"] = { "$ref": "#/definitions/{0}".format(prop_def["ranges"][0])}

    return prop_def["id"], prop_schema

def get_type_schema(type_def):
    type_schema = {
        "title": type_def["label"],
        "description": type_def["comment_plain"],
        
        
    }

    try:
        type_inst = {
            "enum":  map(lambda x: "http://schema.org/{0}".format(x), type_def["instances"]) 
        }

        type_schema.update(type_inst)
        
    except:
        type_schema.update({
            "properties": {
                "type": {
                    "type": "array",
                    "items": {
                        "enum": [ type_def["url"] ]
                    }
                },
                "id": { "$ref": "#/definitions/Text" }
            }
        })

        if len(type_def["specific_properties"]) > 0:
            type_schema["properties"]["properties"] = {
                "type": "object",
                "properties": { }
            }

        for spec_prop in type_def["specific_properties"]:
            prop_name, prop_def = get_prop_schema(spec_prop)
            type_schema["properties"]["properties"]["properties"][prop_name] = prop_def


    if len(type_def["supertypes"]) > 0:
        type_schema["allOf"] = map(lambda x: { "$ref": "#/definitions/{0}".format(x)}, type_def["supertypes"])

    return type_schema


def processDatatypes():
    for type_name, type_def in all_schema_org["datatypes"].items():
        if type_name not in json_schema["definitions"]:
            type_schema = get_type_schema(type_def)
            json_schema["definitions"][type_name] = type_schema

def processTypes():
    for type_name, type_def in all_schema_org["types"].items():
        type_schema = get_type_schema(type_def)     
        json_schema["definitions"][type_name] = type_schema
        if "enum" not in type_schema:

            if "anyOf" not in json_schema["properties"]["items"]["items"]:
                json_schema["properties"]["items"]["items"]["anyOf"] = []

            json_schema["properties"]["items"]["items"]["anyOf"].append(
                {
                    "$ref": "#/definitions/{0}".format(type_name)
                }
            )

# def mixin():
#     for schema_ref in lrmi_mixin["properties"]["items"]["items"]["oneOf"]:
#         if schema_ref not in json_schema["properties"]["items"]["items"]["anyOf"]:
#             json_schema["properties"]["items"]["items"]["anyOf"].append(schema_ref)

#     for schema_name, schema_def in lrmi_mixin["definitions"].items():
#         if schema_name in json_schema["definitions"]:
#             for mixin_name, mixin_def in schema_def["properties"]["properties"]["properties"].items():
#                 if mixin_name not in json_schema["definitions"][schema_name]["properties"]["properties"]["properties"]:
#                     json_schema["definitions"][schema_name]["properties"]["properties"]["properties"].update({ mixin_name: mixin_def })
#         else:
#             json_schema["definitions"].update( { schema_name: schema_def })

def patch():
    global json_schema
    json_schema = jsonpatch.apply_patch(json_schema, lrmi_mixin)


def main():
    validator = jsonschema.Draft4Validator(jsonschema.Draft4Validator.META_SCHEMA)

    print "##### initial #######"
    for err in validator.iter_errors(json_schema):
        pprint.pprint(err)

    processDatatypes()

    print "##### base datatypes #######"
    for err in validator.iter_errors(json_schema):
        pprint.pprint(err)


    processTypes()
    patch()

    log.write(json.dumps(json_schema, indent=2))

    print "##### populated #######"

    for err in validator.iter_errors(json_schema):
        pprint.pprint(err)
    # jsonschema.Draft4Validator.check_schema(json_schema)


def test():
    validator = jsonschema.Draft4Validator(jsonschema.Draft4Validator.META_SCHEMA)

    js_float = {
        "type": "number",
        "not": {
            "type": "integer"
        }
    }

    for err in validator.iter_errors(js_float):
        pprint.pprint(err)

# pprint.pprint(all_schema_org)

if __name__ == "__main__":

    main()



