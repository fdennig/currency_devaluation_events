import gzip, json
import pandas as pd

# mfmod file path
file_path = 'models_most_recent_2025_SP.wf2'

# Open and read the gzip file
with gzip.open(file_path, 'rt', encoding='utf-8') as f:
    data = json.load(f)

# implement Ib's extraction code
pages = data['_pages']
first_page = pages[0]
object_all = [o for o in first_page['_objects']]
types_set = {o['_type'] for o in object_all}
object_dict = {_type : [o for o in object_all if o['_type'] == _type ] for _type in types_set}
# index = [int(d[:4]) for d in object_dict['index'][0]['data']]
index = [d for d in object_dict['index'][0]['data']]
series_list = object_dict['series_double']
series_data = [pd.Series(s['data'],name=s['_name'],index=index) for s in series_list]
df = pd.concat(series_data, axis=1)
selected_cols = [col for col in df.columns if col.endswith("PANUSATLS") or col.endswith("NECONPRVTXN")]
df_extracted = df[selected_cols]
df_extracted.to_csv('priceIndex_and_exchangeRate_series_2025_SP.csv', index=True)