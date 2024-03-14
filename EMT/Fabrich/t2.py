
def marsh_last(dfm, bm):
    query = f"bm=='{bm}' and (em2=='За' or em2=='На') and tm==1"
    return dfm.query(query)['em'].tolist()

def marsh_middle(dfm, bm):
    query = f"bm=='{bm}' and em2=='До' and tm==1"
    return dfm.query(query)['em'].tolist()

def marsh_all_bm(dfm, bm, ls1):
    ls = []

    ls_k = marsh_last(dfm, bm)
    for em in ls_k:
        ls.append(ls1 + [em])
    # return ls

    ls_p = marsh_middle(dfm, bm)
    if len(ls_p) == 0:
       return ls
    for pm in ls_p:
       ls_p_k = marsh_all_bm(dfm, pm, ls1 + [pm])
       if ls_p_k:
            ls.extend(ls_p_k)
    return ls


def marsh_all_em(em, ls_all_marsh):
    ls = []
    for lm in ls_all_marsh:
        if em in lm:
            ind1 = lm.index(em)
            l1 = lm[:ind1+1]
            if l1 not in ls:
                ls.append(l1)
    return ls

def marsh_bm_em(dfm, bm, em):
    ls = marsh_all_bm(dfm, bm, [bm])
    ls1 = marsh_all_em(em, ls)
    return ls1

def zip_marsh(dfm, ls):
    ls3 = []
    ls_id = []
    for ls1 in ls:
        ls2 = []
        ls_id1 = []
        count = len(ls1)
        for i in range(count):
            if i == count-1:
                break
            bm = ls1[i]
            em = ls1[i+1]
            marsh_id = dfm.query(f"bm=='{bm}' and em=='{em}'")['id'].iloc[0]
            ls2.append([bm, em])
            ls_id1.append(marsh_id)
        ls3.append(ls2)
        ls_id.append(ls_id1)
    return ls3, ls_id

def write_marsh(path, ls):
    file1 = open(path, "w", encoding='Windows-1251')
    for ss in ls:
        file1.write(ss +'\n')
    file1.close()

def marsh_sv_bm(dfm, bm):
    ls = marsh_all_bm(dfm, bm, [bm])
    ls7 = []
    for lm in ls:
        for m1 in lm:
            if m1 not in ls7:
                ls7.append(m1)
    write_marsh("marsh_sv_bm.txt", ls7)

def marsh_sv_bm1(dfm, bm):
    ls = marsh_all_bm(dfm, bm, [bm])
    ls7 = []
    for lm in ls:
        for m1 in lm:
            if m1 not in ls7:
                ls7.append(m1)
    return ls7