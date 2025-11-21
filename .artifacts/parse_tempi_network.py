"""Parse network_data from power-structure1.txt without exec()."""

import re
import json
from pathlib import Path

def parse_network_safe(file_path):
    """Parse network_data by extracting node/edge dicts safely."""

    content = Path(file_path).read_text(encoding='utf-8')

    # Find network_data section
    start = content.find("network_data = {")
    end = content.find("\n}", content.find("'edges':", start)) + 2

    if start == -1 or end == -1:
        raise ValueError("Cannot find network_data boundaries")

    section = content[start:end]

    # Extract nodes
    nodes_start = section.find("'nodes': [")
    nodes_end = section.find("\n    ],", nodes_start)
    nodes_section = section[nodes_start:nodes_end]

    # Extract individual node dicts
    nodes = []
    # Find all {... } blocks within nodes section
    node_blocks = re.findall(r'\{[^{}]+?\}', nodes_section, re.DOTALL)

    for block in node_blocks:
        try:
            # Parse each field
            node = {}
            if "'id':" in block:
                id_match = re.search(r"'id':\s*'([^']+)'", block)
                if id_match:
                    node['id'] = id_match.group(1)

            label_match = re.search(r"'label':\s*'([^']+)'", block)
            if label_match:
                node['label'] = label_match.group(1).replace("\\'", "'")

            type_match = re.search(r"'type':\s*'([^']+)'", block)
            if type_match:
                node['type'] = type_match.group(1)

            layer_match = re.search(r"'layer':\s*(\[?[0-9,\s]+\]?|'[^']+')", block)
            if layer_match:
                layer_str = layer_match.group(1).strip()
                if layer_str.startswith('['):
                    node['layer'] = eval(layer_str)
                elif layer_str.isdigit():
                    node['layer'] = int(layer_str)
                else:
                    node['layer'] = layer_str.strip("'")

            role_match = re.search(r"'role':\s*'([^']+)'", block)
            if role_match:
                node['role'] = role_match.group(1)

            size_match = re.search(r"'size':\s*(\d+)", block)
            if size_match:
                node['size'] = int(size_match.group(1))

            power_match = re.search(r"'power':\s*(\d+)", block)
            if power_match:
                node['power'] = int(power_match.group(1))

            if 'id' in node:
                nodes.append(node)

        except Exception as e:
            print(f"Warning: Failed to parse node block: {e}")
            continue

    # Extract edges (similar approach)
    edges_start = section.find("'edges': [")
    edges_section = section[edges_start:]

    edges = []
    edge_blocks = re.findall(r'\{[^{}]+?\}', edges_section, re.DOTALL)

    for block in edge_blocks:
        try:
            edge = {}

            source_match = re.search(r"'source':\s*'([^']+)'", block)
            if source_match:
                edge['source'] = source_match.group(1)

            target_match = re.search(r"'target':\s*'([^']+)'", block)
            if target_match:
                edge['target'] = target_match.group(1)

            type_match = re.search(r"'type':\s*'([^']+)'", block)
            if type_match:
                edge['type'] = type_match.group(1)

            strength_match = re.search(r"'strength':\s*(\d+)", block)
            if strength_match:
                edge['strength'] = int(strength_match.group(1))

            label_match = re.search(r"'label':\s*'([^']+)'", block)
            if label_match:
                edge['label'] = label_match.group(1).replace("\\'", "'")

            if 'source' in edge and 'target' in edge:
                edges.append(edge)

        except Exception as e:
            print(f"Warning: Failed to parse edge block: {e}")
            continue

    return {'nodes': nodes, 'edges': edges}


# Parse and save
source_file = Path(__file__).parent.parent / 'docs' / 'power-structures' / 'power-structure1.txt'
output_file = Path(__file__).parent / 'tempi-network-parsed.json'

print("Parsing network_data from power-structure1.txt...")
network_data = parse_network_safe(source_file)

print(f"Parsed {len(network_data['nodes'])} nodes, {len(network_data['edges'])} edges")

# Save
output_file.write_text(json.dumps(network_data, indent=2), encoding='utf-8')
print(f"Saved to {output_file}")

# Show sample
print("\nSample nodes:")
for node in network_data['nodes'][:5]:
    print(f"  {node.get('label', node.get('id'))}: layer {node.get('layer')}")

print("\nSample edges:")
for edge in network_data['edges'][:5]:
    print(f"  {edge['source']} -> {edge['target']} ({edge.get('type')})")
