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
RANGE_COL_NAMES = {'lsb': '最左笔画范围', 'rsb': '最右笔画范围', 'tsb': '最上笔画范围', 'bsb': '最下笔画范围'}


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
    for weight in WEIGHTS:
        layer = get_layer_by_name(glyph, weight)
        glyph_sb = sb_data[weight].get(glyph.string) # TODO: key should be ID instead of string
        if glyph_sb is None:
            row += [None] * len(DIRECTIONS) * 3
        else:
            row += list(map(lambda direction: glyph_sb[direction], DIRECTIONS))
            row += list(chain(*map(lambda direction: get_outermost_range(layer, direction)[0], DIRECTIONS)))
    df.loc[i] = row

print('Exporting to excel file...')
writer = ExcelWriter(OUTPUT_FILE, engine='xlsxwriter')
workbook = writer.book
worksheet = workbook.add_worksheet('字符数据')
worksheet.set_default_row(18)
writer.sheets['字符数据'] = worksheet
df.to_excel(writer, sheet_name='字符数据', index=False, startrow=1)

# Make header pretty
merge_format = workbook.add_format({'align': 'center', 'bold': True})
header_format = workbook.add_format({'bold': True})
merge_format.set_align('vcenter')
# header_format.set_align('vcenter')
worksheet.set_row(1, 30, header_format)
worksheet.set_row(1, 30, header_format)
worksheet.merge_range('A1:A2', columns[0], merge_format)
worksheet.merge_range('B1:B2', columns[1], merge_format)
for i, weight in enumerate(WEIGHTS):
    weight_col = i * len(DIRECTIONS) * 3 + 2
    worksheet.merge_range(0, weight_col, 0, weight_col + len(DIRECTIONS) * 3 - 1, weight, merge_format)
    for j, direction in enumerate(DIRECTIONS):
        worksheet.write(1, weight_col + j, DIRECTIONS[j].upper())
        dir_col = weight_col + len(DIRECTIONS) + j * 2
        col_name = RANGE_COL_NAMES[direction]
        worksheet.merge_range(1, dir_col, 1, dir_col + 1, col_name, merge_format)
vcenter_format = workbook.add_format()
vcenter_format.set_align('vcenter')
worksheet.set_column('A:XFD', None, vcenter_format)
writer.close()

# fixed_columns = ['ID', '字符']
# weight_columns = [d.upper() for d in DIRECTIONS] + list(chain([f'{d}-range1', f'{d}-range2'] for d in DIRECTIONS))
# data_columns = MultiIndex.from_product([WEIGHTS, weight_columns], names=['weight', 'metric'])
