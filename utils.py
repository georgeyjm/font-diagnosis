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
    data = {}
    for glyph in font.glyphs:
        glyph_data = {'id': glyph.id}
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
            glyph_data[master_name] = {'lsb': lsb, 'rsb': rsb, 'bsb': bsb, 'tsb': tsb}
        # for tag in glyph.tags:
        #     print(tag)
        data[glyph.string] = glyph_data
    return data
