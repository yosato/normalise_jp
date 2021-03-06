import sys,os,imp
import count_homophones
from pythonlib_ys import main as myModule
imp.reload(count_homophones)

def all_hiragana_p(Strs):
            for Str in Strs:
                if not myModule.all_of_chartypes_p(Str,['hiragana']):
                    return False
            return True
def all_kanjikatakana_contained_p(Strs):
            for Str in Strs:
                if not myModule.at_least_one_of_chartypes_p(Str,['han','katakana']):
                    return False
            return True
def kanji_hiragana_combo(Strs):
            if len([Str for Str in Strs if myModule.at_least_one_of_chartypes_p(Str,['han'])])!=1:
                return False
            if not any(myModule.all_of_chartypes_p(Str,['hiragana']) for Str in Strs):
                return False
            if any(myModule.at_least_one_of_chartypes_p(Str,['katakana']) for Str in Strs):
                return False
            return True

def filter_and_output(GenHomStats,Criterion='probUnamb'):
    if Criterion=='probUnamb':
        filter_and_output_probunamb(GenHomStats)

def filter_and_output_probunamb(GenHomStats):
    OrthAmbStats=[];CatAmbStats=[];UnambStats=[];UniOrthStats=[]    
    for GenHomStat in GenHomStats:
        if len(GenHomStat.superorthsfreqs)==1:
            UniOrthStats.append(GenHomStat)
            continue
        if GenHomStat.domcat:
            DomCat=GenHomStat.domcat
            if len([Orth for Orth in GenHomStat.homstats[DomCat].orthsfreqs.keys() if myModule.at_least_one_of_chartypes_p(Orth,['han'])]) <= 1 and len([Orth for Orth in GenHomStat.homstats[DomCat].orthsfreqs.keys() if myModule.all_of_chartypes_p(Orth,['katakana'])]) == 0:
                UnambStats.append(GenHomStat)
            else:
                DomOrth=count_homophones.pseudo_unambiguous(GenHomStat.orthsfreqs[DomCat],500)
                if DomOrth:
                    UnambStats.append(GenHomStat)
                else:
                    OrthAmbStats.append(GenHomStat)
        else:
            CatAmbStats.append(GenHomStat)

    Out=open(Args.out_fp,'wt') if Args.out_fp else sys.stdout
        
    SortedUnambStats=sorted(UnambStats,key=lambda a:a.domcatfreq,reverse=True)        
    for UnambStat in SortedUnambStats:
        Out.write(repr(UnambStat.__dict__)+'\n')


if __name__=='__main__':
    import argparse,glob,pickle
    Psr=argparse.ArgumentParser()
    Psr.add_argument('input_dir')
    Psr.add_argument('--criterion',default='probUnamb')
    Psr.add_argument('--lemmatise',action='store_true')
    Psr.add_argument('--tag-type',default='ipa')
    Psr.add_argument('--filter-in',default=None)
    Psr.add_argument('--genstats-p',action='store_true')
    Psr.add_argument('--out-fp')
    Args=Psr.parse_args()
    MecabCorpusFPs=glob.glob(Args.input_dir+'/*.mecab')
    if not MecabCorpusFPs:
        print('stuff does not exist\n')
        sys.exit()

    HomStats=count_homophones.main(MecabCorpusFPs,TagType=Args.tag_type,LemmatiseP=Args.lemmatise)

    filter_and_output(HomStats,Criterion=Args.criterion)
