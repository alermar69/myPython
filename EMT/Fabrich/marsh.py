from sys import argv
import pandas as pd
import numpy as np
import pyodbc as pc
import warnings

warnings.filterwarnings('ignore')
path_start = 'c:/tt/'

script, func, bm, em, pm = argv

dfm = pd.read_csv(f'{path_start}marsh_fabr.csv')
df_free = pd.read_csv(f"{path_start}marsh_free_elem.csv", encoding='Windows-1251')


def to_txt_ls(namefile, ls):
    path = path_start + namefile
    with open(path, "w", encoding='Windows-1251') as f:
        for ss in ls:
            f.write(ss + '\n')


def to_txt_ls2(namefile, ls):
    path = path_start + namefile
    with open(path, "w", encoding='Windows-1251') as f:
        for ss in ls:
            s1 = ''
            for ss1 in ss:
                s1 += str(ss1) + ','
            if len(s1) > 0:
                s1 = s1[:-1]
                f.write(s1)
                f.write('\n')


def read_txt_ls2(namefile):
    path = path_start + namefile
    ls = []
    with open(path, "r", encoding='Windows-1251') as f:
        for line in f:
            ls1 = line.strip().split(',')
            ls1 = [int(x) for x in ls1]
            ls.append(ls1)
    return ls


def df_id(df, id1):
    return df[df['id'] == id1]


def df_name(df, name):
    return df[df['name'] == name]


def df_col(df, col, val):
    return df[df[col] == val]


# ------------------------------------------------------------------------------------------------------


def marsh_last(dfm, bm):
    query = f"bm=='{bm}' and (em2=='За' or em2=='На') and tm==1"
    return dfm.query(query)['id'].tolist()


def marsh_middle(dfm, bm):
    query = f"bm=='{bm}' and em2=='До' and tm==1"
    return dfm.query(query)['id'].tolist()


def marsh_all_bm(dfm, bm, ls_id):
    ls = []

    ls_k = marsh_last(dfm, bm)
    for id_em in ls_k:
        ls.append(ls_id + [id_em])

    ls_p = marsh_middle(dfm, bm)
    if len(ls_p) == 0:
        return ls
    for pm in ls_p:
        em = dfm[dfm['id'] == pm]['em'].iloc[0]
        ls_p_k = marsh_all_bm(dfm, em, ls_id + [pm])
        if ls_p_k:
            ls.extend(ls_p_k)
    return ls


def marsh_all_bm_exclude(ls_marsh_all_bm):
    dfmarsh = pd.read_csv(f'{path_start}marsh_dev.csv')

    ls_free_sv = df_free[df_free['typ']=='sv']['name'].tolist()
    ls_free_rs = df_free[df_free['typ']=='rs']['name'].tolist()
    ls_free_str = df_free[df_free['typ']=='str']['name'].tolist()
    ls_free_str_plus = df_free[df_free['typ']=='str_plus']['name'].tolist()

    ls_marsh = []
    for lsm in ls_marsh_all_bm:
        ls_marsh1 = []
        for m_id in lsm:
            dfm1 = df_col(dfmarsh, 'marshrut_id', m_id)
            # dfm2 = dfm1[(dfm1['telm'] == 'Светофор') | (dfm1['telm'] == 'РЦ')].iloc[1:]
            dfm2 = dfm1[(dfm1['pnisp'] != 1)]
            fl = 0
            for index, row in dfm2.iterrows():
                if row['telm'] == 'Светофор':
                    if row['elm'] not in ls_free_sv:
                        fl = 1
                if row['telm'] == 'РЦ' and not row['elm'].endswith('ТП'):
                    if row['elm'] not in ls_free_rs:
                        fl = 1
                if row['telm'] == 'Стрелка':
                    if row['elm'] not in ls_free_str:
                        if row['elm'] not in ls_free_str_plus :
                            fl = 1
                        else:
                            if row['pnisp'] == 0:
                                 fl = 1
            if fl == 0:
                ls_marsh1.append(m_id)
            else:
                break
        if len(ls_marsh1) > 0:
            ls_marsh.append(ls_marsh1)
    return ls_marsh


def marsh_elem(dfm, ls_all_marsh, is_txt=True):
    ls_sv = []
    ls_str = []
    ls_rs = []
    for lm in ls_all_marsh:
        for id_m in lm:
            df1 = dfm[dfm['id'] == id_m]
            # SV ------------------------
            bm1 = df1['bm'].iloc[0]
            if bm1 not in ls_sv:
                ls_sv.append(bm1)
            # STR ------------------------
            st1 = df1['sm1'].iloc[0]
            if st1 is not np.nan:
                ls_st = st1.split(',')
                for st2 in ls_st:
                    # st3 = st2[1:]
                    if st2 not in ls_str:
                        ls_str.append(st2)
            # RS ------------------------
            rs1 = df1['rs'].iloc[0]
            if rs1 is not np.nan:
                ls_st = rs1.split(',')
                for rs in ls_st:
                    if rs not in ls_rs:
                        ls_rs.append(rs)

        id_m = lm[-1]
        em = dfm[dfm['id'] == id_m]['em'].iloc[0]
        if em not in ls_sv:
            ls_sv.append(em)
    if is_txt:
        to_txt_ls("marsh_sv_bm.txt", ls_sv)
        to_txt_ls("marsh_str_bm.txt", ls_str)
        to_txt_ls("marsh_rs_bm.txt", ls_rs)
        to_txt_ls2("marsh_all_bm.txt", ls_all_marsh)
        to_txt_ls("marsh_is_sel.txt", [])
    else:
        return ls_all_marsh, ls_sv, ls_str, ls_rs


def marsh_all_bm_in_elem(dfm, bm):
    ls_all_marsh = marsh_all_bm(dfm, bm, [])
    to_txt_ls2("marsh_all_bm.txt", ls_all_marsh)
    to_txt_ls("marsh_is_sel.txt", [])
    # ls_all_marsh = marsh_all_bm_exclude(ls_all_marsh)
    # marsh_elem(dfm, ls_all_marsh)


# ------------------------------------------------------------------------------------------------------


def marsh_all_em(dfm, em, ls_marsh_id):
    ls_marsh_id1 = []
    for ls1 in ls_marsh_id:
        ls2 = []
        for mars_id in ls1:
            ls2.append(mars_id)
            em1 = df_id(dfm, mars_id)['em'].iloc[0]
            if em == em1:
                if ls2 not in ls_marsh_id1:
                    ls_marsh_id1.append(ls2)
                break
    ls_marsh_id1 = sorted(ls_marsh_id1, key=lambda x: len(x))
    return ls_marsh_id1


def marsh_all_pm(dfm, pm, em, ls_marsh_id):
    ls_marsh_id1 = []
    if pm == em:
        ls_marsh_id1.append(ls_marsh_id[0])
    else:
        for ls1 in ls_marsh_id:
            for mars_id in ls1:
                em1 = df_id(dfm, mars_id)['em'].iloc[0]
                if pm == em1:
                    ls_marsh_id1.append(ls1)
                    break
    return ls_marsh_id1


def marsh_all_em_in_elem(dfm, em):
    ls_marsh_id = read_txt_ls2("marsh_all_bm.txt")
    ls_marsh_id = marsh_all_em(dfm, em, ls_marsh_id)
    to_txt_ls2("marsh_all_bm.txt", ls_marsh_id)
    to_txt_ls("marsh_is_sel.txt", [])
    # marsh_elem(dfm, ls_marsh_id)


def marsh_all_pm_in_elem(dfm, pm, em):
    ls_marsh_id = read_txt_ls2("marsh_all_bm.txt")
    ls_marsh_id = marsh_all_pm(dfm, pm, em, ls_marsh_id)
    to_txt_ls2("marsh_all_bm.txt", ls_marsh_id)
    to_txt_ls("marsh_is_sel.txt", [])
    # marsh_elem(dfm, ls_marsh_id)


# ------------------------------------------------------------------------------------------------------

if func == 'marsh_all_bm_in_elem':
    marsh_all_bm_in_elem(dfm, bm)

if func == 'marsh_all_em_in_elem':
    marsh_all_em_in_elem(dfm, em)

if func == 'marsh_all_pm_in_elem':
    marsh_all_pm_in_elem(dfm, pm, em)

