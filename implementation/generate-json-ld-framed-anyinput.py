#!/usr/bin/env python3
import json
import argparse
from pathlib import Path

from rdflib import Graph
from rdflib.util import guess_format
from pyld import jsonld


def load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_rdf_as_jsonld(rdf_path: str, rdf_format: str | None = None) -> dict:
    """
    Load RDF (nt, ttl, rdf/xml, etc.) via rdflib and serialize to JSON-LD.
    JSON-LD is NOT compacted here; pyld will handle framing & compaction.
    """
    g = Graph()

    if rdf_format is None:
        rdf_format = guess_format(rdf_path)

    if rdf_format is None:
        raise ValueError(
            f"Cannot guess RDF format for {rdf_path}. "
            f"Specify explicitly using --input-format."
        )

    g.parse(rdf_path, format=rdf_format)

    jsonld_bytes = g.serialize(format="json-ld", encoding="utf-8")
    return json.loads(jsonld_bytes.decode("utf-8"))


def ensure_graph(doc: dict) -> dict:
    """
    Ensure the top-level JSON-LD document has @graph.
    If @graph is missing, wrap the single root node into @graph.
    """
    if "@graph" in doc:
        return doc

    # Extract context (if any)
    ctx = doc.get("@context")

    # Everything except @context becomes the single graph node
    node = {k: v for k, v in doc.items() if k != "@context"}

    wrapped = {}
    if ctx is not None:
        wrapped["@context"] = ctx
    wrapped["@graph"] = [node]

    return wrapped


def frame_like_playground_then_force_graph(input_doc: dict, frame_doc: dict) -> dict:
    """
    1) Frame with options that matched JSON-LD Playground in your previous test:
       - processingMode = 'json-ld-1.1'
       - requireAll = True
       - pruneBlankNodeIdentifiers = True
       (omitGraph left as default)

    2) Compact with frame's @context and compactArrays=True.

    3) Force @graph at top level by wrapping the compacted result if needed.
    """

    frame_options = {
        "processingMode": "json-ld-1.1",
        "requireAll": True,
        "pruneBlankNodeIdentifiers": True,
        # omitGraph: use default (True) like Playground – we'll wrap manually later
    }

    # Step 1: frame        
    framed = jsonld.frame(input_doc, frame_doc, options=frame_options)
    #print("=== DEBUG: FRAMED (before compact) ===")
    #print(json.dumps(framed, indent=2, ensure_ascii=False))


    # Step 2: compact using frame @context
    context = frame_doc.get("@context", {})
    compacted = jsonld.compact(
        framed,
        context,
        options={
            "processingMode": "json-ld-1.1",
            "compactArrays": True,
        },
    )   

    #print("=== DEBUG: COMPACTED (before ensure_graph) ===")
    #print(json.dumps(compacted, indent=2, ensure_ascii=False)) 

    # Step 3: force @graph
    with_graph = ensure_graph(compacted)
    return with_graph


def is_jsonld_file(path: str) -> bool:
    ext = Path(path).suffix.lower()
    return ext in {".jsonld", ".json", ".json-ld"}


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Frame RDF (JSON-LD, NT, Turtle, RDF/XML, etc.) with a JSON-LD frame, "
            "emulating JSON-LD Playground and ALWAYS adding top-level @graph."
        )
    )
    parser.add_argument("input_rdf", help="Input RDF file (jsonld, nt, ttl, rdf, etc.)")
    parser.add_argument("frame_jsonld", help="JSON-LD frame (must contain @context)")
    parser.add_argument(
        "-F", "--input-format",
        help="Explicit RDF format for rdflib (e.g., nt, turtle, xml, json-ld)",
        default=None,
    )
    parser.add_argument(
        "-o", "--output",
        help="Output JSON-LD file (default: stdout)",
        default="-",
    )
    args = parser.parse_args()

    # Load frame
    frame_doc = load_json(args.frame_jsonld)

    # Load input: JSON-LD directly, otherwise via rdflib
    if (args.input_format and args.input_format in ("json-ld", "jsonld")) or \
       (not args.input_format and is_jsonld_file(args.input_rdf)):
        input_doc = load_json(args.input_rdf)
    else:
        input_doc = load_rdf_as_jsonld(args.input_rdf, args.input_format)

    # Frame + compact + force @graph
    result = frame_like_playground_then_force_graph(input_doc, frame_doc)

    # Output
    if args.output == "-":
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()