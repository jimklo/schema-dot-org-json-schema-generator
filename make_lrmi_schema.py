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
        "type": "array",
        "additionalItems": False
    }

    if prop_name == "acceptedPaymentMethod":
        import pdb; pdb.set_trace()

    prop_schema["items"] = get_schemas_for_ranges(prop_def["ranges"])
    return prop_def["id"], prop_schema

def get_schemas_for_ranges(ranges=[]):
    schemas = []
    instances = []
    for r in ranges:
        if r not in schemas:
            schemas.append(r)
            if r in all_schema_org["types"]:
                subids, subinstances = find_subids(all_schema_org["types"][r], [])
                if len(subinstances)>0:
                    for inst in subinstances:
                        if inst not in instances:
                            instances.append(inst)
                else:
                    for i in subids:
                        if i not in schemas:
                            schemas.append(i)
    
    result = []
    
    if len(instances)>0:
        result.append({
            "enum": map("http://schema.org/{0}".format, instances)   
        })
    if len(schemas)>0:
       result += map(lambda x: { "$ref": "#/definitions/{0}".format(x)}, schemas)

    if len(result) == 1:
        return result[0]
    else:
        return {
            "oneOf": result
        }
    

def unique(seq):
    return {}.fromkeys(seq).keys()

def find_subids(type_def, type_list=[]):

    instance_list=[]

    # if type_def["id"] == "Thing":
    #     import pdb; pdb.set_trace()


    try: 

        if len(type_def["instances"]) > 0:
            instance_list += type_def["instances"]
            return [], instance_list
    except:
        pass


    if "id" in type_def and type_def["id"] not in type_list:
        type_list.append(type_def["id"])

    try:
        for subtype in type_def["subtypes"]:
            subtype_def = all_schema_org["types"][subtype]
            type_list, new_instance_list = find_subids(subtype_def, type_list)
            instance_list += new_instance_list

    except:
        pass

    return type_list, unique(instance_list)

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
        del type_schema["allOf"]
        
    else:
        this_schema = {
            "properties": {
                "type": {
                    "type": "array",
                    "items": {
                        "enum": [type_def["url"]]
                    },
                    "additionalItems": False
                },
                "properties": { }
            }
        }

        if len(type_def["properties"]) > 0:
            this_schema["properties"]["properties"]["properties"] = { }

        for spec_prop in type_def["properties"]:
            prop_name, prop_def = get_prop_schema(spec_prop)
            this_schema["properties"]["properties"]["properties"][prop_name] = prop_def

        type_schema["allOf"].append(this_schema)

    # if len(type_def["supertypes"]) > 0:
    #     type_schema["anyOf"] = map(lambda x: { "$ref": "#/definitions/{0}".format(x)}, type_def["supertypes"])

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



