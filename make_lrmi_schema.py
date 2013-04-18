#! /usr/bin/env python

import urllib2, json, pprint, jsonschema, jsonpatch

all_schema_org = json.load(urllib2.urlopen("http://schema.rdfs.org/all.json"))

# all_schema_org = json.load(open("schemas/schema-rdfs-org.json"))

lrmi_mixin = json.load(open("schemas/lrmi-json-microdata-mixin.json"))

log = open("lrmi.json", "w")

json_schema = json.load(open("schemas/microdata-json-schema.json"))


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


def find_subtypes(type_def, type_list=[]):
    if "url" in type_def and type_def["url"] not in type_list:
        type_list.append(type_def["url"])

    try:
        for subtype in type_def["subtypes"]:
            subtype_def = all_schema_org["types"][subtype]
            type_list = find_subtypes(subtype_def, type_list)
    except:
        pass

    return type_list



def get_type_schema(type_def):
    type_schema = {
        "title": type_def["label"],
        "description": type_def["comment_plain"],
        "allOf":
            [ { "$ref": "#/definitions/microdata" } ]
        
    }
    

    if "instances" in type_def:
        type_inst = {
            "enum":  map(lambda x: "http://schema.org/{0}".format(x), type_def["instances"]) 
        }

        type_schema.update(type_inst)
        
    else:
        this_schema = {
            "properties": {
                "type": {
                    "type": "array",
                    "items": {
                        "enum": find_subtypes(type_def, [])
                    }
                },
                "properties": { }
            }
        }

        if len(type_def["specific_properties"]) > 0:
            this_schema["properties"]["properties"]["properties"] = { }

        for spec_prop in type_def["specific_properties"]:
            prop_name, prop_def = get_prop_schema(spec_prop)
            this_schema["properties"]["properties"]["properties"][prop_name] = prop_def

        type_schema["allOf"].append(this_schema)

    if len(type_def["supertypes"]) > 0:
        type_schema["anyOf"] = map(lambda x: { "$ref": "#/definitions/{0}".format(x)}, type_def["supertypes"])

    return type_schema


def init():
    global json_schema

    json_schema["properties"]["items"]["items"][0]["allOf"][0]["anyOf"] = []
    microdata = json_schema["definitions"]["microdata"]
    json_schema["definitions"] = { "microdata": microdata }

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
            json_schema["properties"]["items"]["items"][0]["allOf"][0]["anyOf"].append(
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

    init()

    print "##### initial #######"
    for err in validator.iter_errors(json_schema):
        pprint.pprint(err)

    processDatatypes()

    # print "##### base datatypes #######"
    # for err in validator.iter_errors(json_schema):
    #     pprint.pprint(err)


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
    # print(find_subtypes(all_schema_org["types"]["CreativeWork"]))



