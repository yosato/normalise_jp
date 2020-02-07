import sys,os,imp,bidict,math,copy
from collections import defaultdict,OrderedDict
if '/home/yosato/myProjects/myPythonLibs' not in sys.path:
    sys.path=['/home/yosato/myProjects/myPythonLibs']+sys.path
#import mecabtools
from mecabtools import mecabtools
from pythonlib_ys import main as myModule
from pythonlib_ys import jp_morph
#from pandas import DataFrame as df
imp.reload(mecabtools)

def char_composition(Str):
    CharComp=set()
    for Char in Str:
        CharComp.add(myModule.identify_chartype(Char))
    return CharComp

def infform_variants_p(Wd1,Wd2):
    return Wd1.lemma==Wd2.lemma and Wd1.infpat==Wd2.infpat and Wd1.infform!=Wd2.infform and Wd1.subcat==Wd2.subcat

def chain_partition(ListOrg,relation,IndsOnly=False):
    Partitions=set()
    List=copy.copy(list(enumerate(ListOrg)))
    while List:
        TgtEl=List[0]
        Partition={TgtEl}
        for El in List[1:]:
            if relation(TgtEl[1],El[1]):
                Partition.add(El)

        Partitions.add(frozenset(Partition))
        for ElInPart in Partition:
            List.remove(ElInPart)
    if IndsOnly:
        RedPartitions=set()
        for Part in Partitions:
            RedPart=[Ind for (Ind,_) in Part]
            RedPartitions.add(frozenset(RedPart))
        Partitions=RedPartitions
    return Partitions

def subcat_variants_p(Wd1,Wd2):
    return Wd1.subcat==Wd2.subcat and Wd1.sem==Wd2.sem
            
class VariantStat:
    def __init__(self,IndsVars,Freqs):
        SortedIndsVars=OrderedDict(sorted(IndsVars.items(),key=lambda x:x[0]))
        self.inds=list(SortedIndsVars.keys())
        self.variants=list(IndsVars.values())
        self.freqs=Freqs
        self.overallfreq=sum(Freqs)

class CatHomStat:        
    def __init__(self,PronCat,HomsFreqs):
        self.pron=PronCat[0]
        self.cat=PronCat[1]
        self.homs=list(HomsFreqs.keys())
        self.freqs=list(HomsFreqs.values())
        self.overallfreq=sum(self.freqs)
        self.orths=[Hom.orth for Hom in HomsFreqs.keys()]
        self.subcats=[Hom.subcat for Hom in HomsFreqs.keys()]
        self.infforms=[Hom.infform for Hom in HomsFreqs.keys()]
        self.orthtypes=[char_composition(Orth) for Orth in self.orths]
        self.orthsfreqs=self.count_orths()
        self.okuriganavariant_stats=self.get_variantstats(self.identify_variants(self.orths,jp_morph.okurigana_variants_p)) if len([Comp for Comp in self.orthtypes if Comp == {'hiragana','han'}])>=2 else []
        
    def count_orths(self):
        OrthsCounts=defaultdict(int)
        for Cntr,Orth in enumerate(self.orths):
            OrthsCounts[Orth]+=self.freqs[Cntr]
        return OrthsCounts

    def get_variantstats(self,Partitions):
        VStats=[]
        for Part in Partitions:
            Inds=[Ind for (Ind,_) in Part]
            Freqs=[Freq for (Cntr,Freq) in enumerate(self.freqs) if Cntr in Inds]
            IndsVars={IndVar[0]:IndVar[1] for IndVar in Part}
            VStats.append(VariantStat(IndsVars,Freqs))
        return VStats
        
    def identify_variants(self,TgtList,bool_func,MultipleOnly=True):
        Partitions=chain_partition(TgtList,bool_func)
        Thresh=1 if MultipleOnly else 0
        return {Part for Part in Partitions if len(Part)>Thresh}
            
class PlainCatHomstat(CatHomStat):
    def __init__(self,PronCat,HomsFreqs):
        super().__init__(PronCat,HomsFreqs)
    
class LemmatisedCatHomstat(CatHomStat):
    def __init__(self,PronCat,HomsFreqs):
        super().__init__(PronCat,HomsFreqs)

        self.okuriganavariant_stats=self.get_variantstats(self.identify_variants(self.orths,jp_morph.okurigana_variants_p)) if len([Comp for Comp in self.orthtypes if Comp == {'hiragana','han'}])>=2 else []
        
        self.infformvariant_stats=self.get_variantstats(self.identify_variants(self.homs,infform_variants_p))
        SubcatStats=self.get_variantstats(self.identify_variants(self.homs,subcat_variants_p,MultipleOnly=False))
        self.subcat_stats={Stat.variants[0].subcat:Stat for Stat in SubcatStats}
        


class GeneralHomStat:    
    def __init__(self,HomStats):
        self.pron=list(HomStats.values())[0].pron
        self.catsfreqs={Cat:HomStat.freqs for (Cat,HomStat) in HomStats.items()}
        self.overallfreq=sum([HomStat.overallfreq for HomStat in HomStats.values()])
        self.supercatsfreqs={Cat:sum(Freqs) for (Cat,Freqs) in self.catsfreqs.items()}
        self.catsorths={Cat:HomStat.orths for (Cat,HomStat) in HomStats.items()}
        self.catssubcats={Cat:HomStat.subcats for (Cat,HomStat) in HomStats.items()}
        self.catsinfforms={Cat:HomStat.infforms for (Cat,HomStat) in HomStats.items()}
        self.orthsfreqs={Cat:HomStat.orthsfreqs for (Cat,HomStat) in HomStats.items()}
        self.homstats=HomStats
        self.superorthsfreqs=self.count_orths()
        self.domcat=pseudo_unambiguous(self.supercatsfreqs,500)
        self.domcatfreq=self.supercatsfreqs[self.domcat] if self.domcat else self.overallfreq

    def count_orths(self):
        OrthsCounts={}
        for (Cat,OrthsFreqs) in self.orthsfreqs.items():
            for Orth,Freq in OrthsFreqs.items():
                if Orth not in OrthsCounts:
                    OrthsCounts[Orth]={Cat:Freq}
                else:
                    if Cat in OrthsCounts:
                        OrthsCounts[Orth][Cat]+=Freq
                    else:
                        OrthsCounts[Orth].update({Cat:Freq})
        return OrthsCounts
    
def load_pickle(PickledFP):
    return pickle.load(open(PickledFP,'rb'))

def main(MecabCorpusFPs,TagType='ipa',FreqCutOffRate=0,LemmaBaseP=True,Debug=False,StrictP=False,LemmatiseP=False):
    #Homs=defaultdict(dict)
    OrderedFNs=[]
    # consider the first of the sorted FPs' dir as OrgDir
    OrgDir=os.path.dirname(sorted(MecabCorpusFPs)[0])
    PickleFPStem=myModule.merge_filenames([os.path.basename(FP) for FP in MecabCorpusFPs])
    WdObjsFreqs,_=myModule.ask_filenoexist_execute_pickle(os.path.join(OrgDir,PickleFPStem+'_wdobjs.pickle'),mecabtools.collect_wdobjs_with_freqs,([MecabCorpusFPs],{'StrictP':False,'TagType':TagType}))

    HomStats,_=myModule.ask_filenoexist_execute_pickle(os.path.join(OrgDir,PickleFPStem+'_homs_'+('lemmatised' if LemmatiseP else 'plain')+'.pickle'),collect_homstats,([WdObjsFreqs],{'LemmatiseP':LemmatiseP}))
    SeenProns=set();SuperHomStats={}
    for PronreprCat,HomStat  in HomStats.items():
        Pronrepr,Cat=PronreprCat
        if Pronrepr not in SeenProns:
            SuperHomStats[Pronrepr]={Cat:HomStat}
            SeenProns.add(Pronrepr)
        else:
            assert (Cat not in SuperHomStats[Pronrepr])
            SuperHomStats[Pronrepr][Cat]=HomStat

    GenHomStats=[]        
    for HomStats in SuperHomStats.values():
        GenHomStats.append(GeneralHomStat(HomStats))

    return GenHomStats

def collect_homstats(WdObjsFreqs,LemmatiseP=True):
    ReprsHoms=collate_homophones(WdObjsFreqs,LemmatiseP)
    HomStats={}
    for PronreprCat,Homs in ReprsHoms.items():
        if LemmatiseP:
            HomStats[PronreprCat]=LemmatisedCatHomstat(PronreprCat,dict(Homs))
        else:
            HomStats[PronreprCat]=PlainCatHomstat(PronreprCat,dict(Homs))
    return HomStats
    
def collate_homophones(WdObjsFreqs,LemmatiseP):
    Homs=defaultdict()
    OverallCnt=sum(WdObjsFreqs.values())
    for (Wd,Freq) in WdObjsFreqs.items():
                if Wd.pronunciation=='*':
                    continue
                # PronRepr is lemmatised pron
                if LemmatiseP and Wd.cat in ('形容詞','動詞'):
                    PronRepr=Wd.derive_lemma_pronunciation()
                    if myModule.at_least_one_of_chartypes_p(PronRepr,['roman']):
                        sys.stderr.write(PronRepr+'\n')
                        Wd.divide_stem_suffix()
                        PronRepr=Wd.derive_lemma_pronunciation()
                                                                     
                    Orth=Wd.lemma
                else:
                    PronRepr=Wd.pronunciation
                    Orth=Wd.orth
                if (PronRepr,Wd.cat) not in Homs:
                    Homs[(PronRepr,Wd.cat)]=[(Wd,Freq)]
                else:
                    Homs[(PronRepr,Wd.cat)].append((Wd,Freq))

    return Homs
                    
def mymeasure(Freqs):
    return entropy(Freqs)+sum(Freqs)/100

    


def print_stuff(SortedHoms,CutOff=None,filter_out=None,filter_in=None):
    for AmbCnt,Homs in SortedHoms.items():
        sys.stdout.write('Orth variability: '+str(AmbCnt)+'\n\n')
        for (ReprCat,OrthsWdFreqsScores) in Homs:
            OrthsWdFreqs=OrthsWdFreqsScores[0]
            if filter_in and not filter_in(OrthsWdFreqs.keys()):
                continue
            if filter_out and filter_out(OrthsWdFreqs.keys()):
                continue
            if CutOff and sum([Stuff[1] for Stuff in OrthsWdFreqs.values()])<=CutOff:
                continue
            OrthsFreqsStr=' / '.join([Orth+' '+str(Freq) for (Orth,(_Wd,Freq)) in OrthsWdFreqs.items()])+'\t'+str(OrthsWdFreqsScores[1])
            sys.stdout.write(repr(ReprCat)+': '+OrthsFreqsStr+'\n')
        sys.stdout.write('\n')

def entropy(Freqs):
    Probs=[Freq/sum(Freqs) for Freq in Freqs]
    return -sum([Prob*math.log(Prob,2) for Prob in Probs])

def pseudo_unambiguous(CatsFreqs,Ratio,MaxRequired=None):
    MaxInData=max(CatsFreqs.values())
    if MaxRequired is None:
        MaxRequired=Ratio
    if MaxInData<MaxRequired:
        return None
    for Cat,Freq in CatsFreqs.items():
        if Freq==MaxInData:
            MaxCat=Cat
        else:
            if Freq>(MaxInData/Ratio):
                return None

    return MaxCat

if __name__=='__main__':
    import argparse,glob,pickle
    Psr=argparse.ArgumentParser()
    Psr.add_argument('input_dir')
    Psr.add_argument('--lemmatise',action='store_true')
    Psr.add_argument('--tag-type',default='ipa')
    Psr.add_argument('--filter-in',default=None)
    Args=Psr.parse_args()
    MecabCorpusFPs=glob.glob(Args.input_dir+'/*.mecab')
    if not MecabCorpusFPs:
        print('stuff does not exist\n')
        sys.exit()

    GenHomStats=main(MecabCorpusFPs,TagType=Args.tag_type,LemmatiseP=Args.lemmatise)

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

    for GenHomStat in sorted(GenHomStats,key=lambda x:x.pron):
        for Cat,HomStat in GenHomStat.homstats.items():
            if HomStat.okuriganavariant_stats:
                Cat=HomStat.cat
                for VarStat in HomStat.okuriganavariant_stats:
                    Strs=[]
                    for Variant,Freq in zip(VarStat.variants,VarStat.freqs):
                        Strs.append(Variant+' '+str(Freq))
                    sys.stdout.write(Cat+': '+' / '.join(Strs)+'\n')
        
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
                DomOrth=pseudo_unambiguous(GenHomStat.orthsfreqs[DomCat],500)
                if DomOrth:
                    UnambStats.append(GenHomStat)
                else:
                    OrthAmbStats.append(GenHomStat)
        else:
            CatAmbStats.append(GenHomStat)

    SortedUnambStats=sorted(UnambStats,key=lambda a:a.domcatfreq,reverse=True)        
    for UnambStat in SortedUnambStats:
        print(UnambStat.__dict__)
            
            
#    print_stuff(HomStats,filter_in=eval(Args.filter_in))p


