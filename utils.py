import itertools

from scipy import stats


def read_side_bearings(font, weights=('ExtraLight','Regular','Black')):
    # Get baseline offset and height data
    baseline = {}
    height = {}
    for master in font.masters:
        if master.name not in weights:
            continue
        baseline[master.name] = master.descender
        height[master.name] = master.ascender - master.descender

    # Get side bearing data of all glyphs
    data = {weight: {} for weight in weights}
    for glyph in font.glyphs:
        for layer in glyph.layers:
            master_name = layer.master.name
            if master_name not in weights:
                continue 
            if layer.bounds is None:
                # Not drawn yet
                continue
            lsb = layer.bounds.origin.x
            rsb = layer.width - lsb - layer.bounds.size.width
            bsb = layer.bounds.origin.y - baseline[master_name]
            tsb = height[master_name] - bsb - layer.bounds.size.height
            data[master_name][glyph.string] = {'id': glyph.id, 'lsb': lsb, 'rsb': rsb, 'bsb': bsb, 'tsb': tsb}
        # for tag in glyph.tags:
        #     print(tag)
    return data


def dist_between_rankings(sb_data, direction):
    direction = direction.lower()
    assert direction in ('lsb', 'rsb', 'tsb', 'bsb')

    # Calculates Kendall's tau as a measure of distance between two rankings
    # An alternative to consider is Rank Biased Overlap (RBO)
    # IMPORTANT: We calculate Kendall's tau between ALL pairs of rankings.
    # This is to accommodate for one odd ranking in the middle having too much impact on the overall score.
    weights = list(sb_data.keys())
    scores = []
    common_chars = list(set.intersection(*[set(sb_data[weight].keys()) for weight in weights])) # List is important to guarantee stable sort
    for weight1, weight2 in itertools.combinations(weights, 2): # Can shorten to combining weights.values()
        ranking1 = sorted(common_chars, key=lambda k: sb_data[weight1][k][direction], reverse=True)
        ranking2 = sorted(common_chars, key=lambda k: sb_data[weight2][k][direction], reverse=True)
        tau = stats.kendalltau(ranking1, ranking2)
        scores.append(tau.statistic)
    return scores


def compare_node_to_record(node, record, direction):
    if direction == 'lsb':
        if node.position.x < record:
            return 1, node.position.x
        elif node.position.x == record:
            return 0, record
        return -1, record
    elif direction == 'rsb':
        if node.position.x > record:
            return 1, node.position.x
        elif node.position.x == record:
            return 0, record
        return -1, record
    elif direction == 'tsb':
        if node.position.y > record:
            return 1, node.position.y
        elif node.position.y == record:
            return 0, record
        return -1, record
    elif direction == 'bsb':
        if node.position.y < record:
            return 1, node.position.y
        elif node.position.y == record:
            return 0, record
        return -1, record


def get_midpoint(node_start, node_end, direction):
    if direction in ('lsb', 'rsb'):
        return (node_start.position.y + node_end.position.y) / 2
    else:
        return (node_start.position.x + node_end.position.x) / 2


def get_outermost_points(layer, direction):
    direction = direction.lower()
    assert direction in ('lsb', 'rsb', 'tsb', 'bsb')

    # Idea: any adjacent outermost point counts as one
    record = 0 # This needs changing
    outermost_points = []
    stroke_start = None
    stroke_end = None
    for path in layer.paths:
        for node in path.nodes:
            if node.type == 'offcurve':
                # Skip handle nodes
                # IMPORTANT: This assumes that outermost pixels are determined by nodes, rather than curves, which is also best practice
                continue
            comparison, new_record = compare_node_to_record(node, record, direction)
            if comparison == -1: # Does not break record
                if stroke_end is not None: # Record breaking stroke has ended
                    outermost_points.append(get_midpoint(stroke_start, stroke_end, direction))
                    stroke_start = None
                    stroke_end = None
            elif comparison == 1: # Breaks outermost record
                record = new_record
                outermost_points = []
                stroke_start = node
                stroke_end = node
            else: # Same with current record
                if stroke_start is None: # Another stroke with the same record
                    stroke_start = node
                stroke_end = node # Otherwise, currently on a record breaking stroke, still have to update end node
        if stroke_end is not None: # Record breaking stroke has ended
            outermost_points.append(get_midpoint(stroke_start, stroke_end, direction))
            stroke_start = None
            stroke_end = None
    return record, outermost_points


def get_glyph(font, char):
    for glyph in font.glyphs:
        if glyph.string == char or glyph.id == char:
            return glyph
