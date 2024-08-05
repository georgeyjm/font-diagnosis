import json
from itertools import chain

from glyphsLib import GSFont
from pandas import DataFrame, ExcelWriter, MultiIndex
from tqdm import tqdm

from utils import read_side_bearings, get_outermost_range, get_layer_by_name, dist_between_rankings


GLYPHS_FILE = '3type-sy-9169字符_2.glyphs'
STROKE_LABELS_FILE = 'char-labels.json'
WEIGHTS = ('ExtraLight', 'Regular', 'Heavy')
DIRECTIONS = ('lsb', 'rsb', 'tsb', 'bsb')
OUTPUT_FILE = 'glyphs_data.xlsx'
RANGE_COL_NAMES = {'lsb': '最左树枝笔画范围', 'rsb': '最右树枝笔画范围', 'tsb': '最上树枝笔画范围', 'bsb': '最下树枝笔画范围'}
LABEL_DIRECTION_TRANSLATE = {'lsb': 'left', 'rsb': 'right', 'tsb': 'top', 'bsb': 'bottom'}
OUTPUT_ALL_RANGES = False


print('Reading Glyphs file...')
font = GSFont(GLYPHS_FILE)
sb_data = read_side_bearings(font, weights=WEIGHTS)
with open(STROKE_LABELS_FILE) as f:
    char_labels = json.load(f)
# score = dist_between_rankings(sb_data, 'lsb')

# Initialize dataframe
columns = ['ID', '字符']
for weight in WEIGHTS:
    for direction in DIRECTIONS:
        columns.append(f'{weight}-{direction}')
    for direction in DIRECTIONS:
        columns.append(f'{weight}-{direction}-range1')
        columns.append(f'{weight}-{direction}-range2')
df = DataFrame(columns=columns)
df['ID'] = df['ID'].astype(str)
df['字符'] = df['字符'].astype(str)

print('Populating dataframe...')
for i, glyph in enumerate(tqdm(font.glyphs)):
    row = [glyph.id, glyph.string]
    if not OUTPUT_ALL_RANGES:
        labels = char_labels.get(glyph.string)
        glyph_labels = {}
        if labels is None:
            # Maybe we should notify this
            pass
        else:
            for direction in DIRECTIONS:
                strokes = labels.get(LABEL_DIRECTION_TRANSLATE[direction])
                if not strokes:
                    continue
                glyph_labels[direction] = True # Don't need to store strokes for now
                # glyph_labels[direction] = strokes
    for weight in WEIGHTS:
        layer = get_layer_by_name(glyph, weight)
        glyph_sb = sb_data[weight].get(glyph.string) # TODO: key should be ID instead of string
        if glyph_sb is None:
            row += [None] * len(DIRECTIONS) * 3
            print(row)
            continue
        row += list(map(lambda direction: glyph_sb[direction], DIRECTIONS))
        # Output all ranges of all directions
        if OUTPUT_ALL_RANGES:
            row += list(chain(*map(lambda direction: get_outermost_range(layer, direction)[0], DIRECTIONS)))
            continue
        # Output only ranges which correspond to directions with branch strokes
        for direction in DIRECTIONS:
            if glyph_labels.get(direction):
                row += get_outermost_range(layer, direction)[0]
            else:
                row += [None] * 2
    df.loc[i] = row

print('Exporting to excel file...')
writer = ExcelWriter(OUTPUT_FILE, engine='xlsxwriter')
workbook = writer.book
worksheet = workbook.add_worksheet('字符数据')
worksheet.set_default_row(18)
writer.sheets['字符数据'] = worksheet
df.to_excel(writer, sheet_name='字符数据', index=False, startrow=1)

# Make header pretty
header_format = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'bold': True, 'border': 0})
vcenter_format = workbook.add_format({'valign': 'vcenter'})
# border_format = workbook.add_format({'right': 2})
worksheet.merge_range('A1:A2', columns[0], header_format)
worksheet.merge_range('B1:B2', columns[1], header_format)
for i, weight in enumerate(WEIGHTS):
    weight_col = i * len(DIRECTIONS) * 3 + 2
    worksheet.merge_range(0, weight_col, 0, weight_col + len(DIRECTIONS) * 3 - 1, weight, header_format)
    for j, direction in enumerate(DIRECTIONS):
        worksheet.write(1, weight_col + j, DIRECTIONS[j].upper())
        dir_col = weight_col + len(DIRECTIONS) + j * 2
        col_name = RANGE_COL_NAMES[direction]
        worksheet.merge_range(1, dir_col, 1, dir_col + 1, col_name, header_format)
worksheet.set_row(0, 30, header_format)
worksheet.set_row(1, 30, header_format)
worksheet.set_column('A:XFD', None, vcenter_format)
# for i in range(len(WEIGHTS)):
#     col = 1 + i * len(DIRECTIONS) * 3
#     worksheet.set_column(col, col, None, border_format)
writer.close()
print('Done.')

# fixed_columns = ['ID', '字符']
# weight_columns = [d.upper() for d in DIRECTIONS] + list(chain([f'{d}-range1', f'{d}-range2'] for d in DIRECTIONS))
# data_columns = MultiIndex.from_product([WEIGHTS, weight_columns], names=['weight', 'metric'])
