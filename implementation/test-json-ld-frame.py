#!/usr/bin/env python3
from pyld import jsonld
import json

# ---------------------------
# Input JSON-LD document
# ---------------------------
input_doc = {
    "@context": {
        "name": "http://schema.org/name",
        "knows": "http://schema.org/knows",
        "Person": "http://schema.org/Person"
    },
    "@id": "http://example.com/alice",
    "@type": "Person",
    "name": "Alice",
    "knows": {
        "@id": "http://example.com/bob",
        "@type": "Person",
        "name": "Bob"
    }
}

# ---------------------------
# Frame document
# (select Bob as the framed root)
# ---------------------------
frame_doc = {
    "@context": input_doc["@context"],
    "@type": "Person",
    "name": "Bob"
}

# ---------------------------
# Run framing
# ---------------------------
framed = jsonld.frame(
    input_doc,
    frame_doc,
    options={
        "embed": "@always",
        "explicit": False,
        "requireAll": False,
        "omitGraph": False
    }
)

# ---------------------------
# Print result
# ---------------------------
print(json.dumps(framed, indent=2))