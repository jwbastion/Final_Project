import pandas as pd

def load_all_infra(path='Data'):
    """
    data/{category}.csv 파일들을 읽어서
    {'health': DataFrame, 'health_care': DataFrame, ...} 반환
    """
    categories = ['health', 'health_care', 'life', 'play', 'safety', 'traffic']
    dfs = {}
    for cat in categories:
        dfs[cat] = pd.read_csv(f'{path}/{cat}.csv')
    return dfs

def load_subcategories(infra_dfs):
    """
    infra_dfs: {'life': df, ...}
    returns: {'life': ['편의점','대형마트',...], ...}
    """
    mapping = {}
    for parent, df in infra_dfs.items():
        mapping[parent] = df['category'].unique().tolist()
    return mapping
