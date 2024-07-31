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
    common_chars = set.intersection(*[set(sb_data[weight].keys()) for weight in weights])
    for weight1, weight2 in itertools.combinations(weights, 2): # Can shorten to combining weights.values()
        ranking1 = sorted(common_chars, key=lambda k: sb_data[weight1][k][direction], reverse=True)
        ranking2 = sorted(common_chars, key=lambda k: sb_data[weight2][k][direction], reverse=True)
        tau = stats.kendalltau(ranking1, ranking2)
        scores.append(tau.statistic)
    return scores


def get_outermost_points(layer):
    # Idea: any adjacent outermost point counts as one
    pass
