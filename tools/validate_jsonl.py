import json
import argparse
import sys
from jsonschema import Draft202012Validator, ValidationError, validators

def extend_with_default(validator_class):
    validate_props = validator_class.VALIDATORS["properties"]
    def set_defaults(validator, properties, instance, schema):
        for prop, subschema in properties.items():
            if "default" in subschema:
                instance.setdefault(prop, subschema["default"])
        for error in validate_props(validator, properties, instance, schema):
            yield error
    return validators.extend(validator_class, {"properties": set_defaults})

DefaultValidatingDraft202012Validator = extend_with_default(Draft202012Validator)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--schema", required=True)
    ap.add_argument("--input", required=True)
    args = ap.parse_args()

    with open(args.schema) as f:
        schema = json.load(f)
    v = DefaultValidatingDraft202012Validator(schema)
    ok = True
    with open(args.input) as f:
        for i, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
                v.validate(obj)
            except ValidationError as e:
                sys.stderr.write(f"Line {i}: {e.message}\n")
                ok = False
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
