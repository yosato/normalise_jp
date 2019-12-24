import sys,os,imp,bidict,math
from collections import defaultdict,OrderedDict
if '/home/yosato/myProjects/myPythonLibs' not in sys.path:
    sys.path=['/home/yosato/myProjects/myPythonLibs']+sys.path
#import mecabtools
from mecabtools import mecabtools
from pythonlib_ys import main as myModule
imp.reload(mecabtools)

def load_pickle(PickledFP):
    return pickle.load(open(PickledFP,'rb'))

def main(MecabCorpusFPs,FreqCutOffRate=0.0001,LemmaBaseP=True,Debug=False):
    Homs=defaultdict(dict)
    WdObjsFreqs=collect_wdobjs_with_freqs(MecabCorpusFPs)
    OverallCnt=sum(WdObjsFreqs.values())
    for (Wd,Freq) in WdObjsFreqs.items():
                #print(Wd.orth)
                if Wd.pronunciation=='*':
                    continue
                if LemmaBaseP and Wd.cat in ('形容詞','動詞'):
                    if Debug:
                        sys.stdout.write(Wd.orth+'\n')
                    Repr=Wd.derive_lemma_pronunciation()
                    if Debug:
                        sys.stdout.write(Repr+'\n')
                    Orth=Wd.lemma
                else:
                    Repr=Wd.pronunciation
                    Orth=Wd.orth
                if Wd.cat in Homs[Repr]:
                    if Orth not in Homs[Repr][Wd.cat]:
                        Homs[Repr][Wd.cat].update({Orth:[Wd,Freq]})
                    else:
                        Homs[Repr][Wd.cat][Orth][1]+=Freq
                else:
                    Homs[Repr]={Wd.cat:{Orth:[Wd,Freq]}}
                            
    AmbIndexedHoms=defaultdict(dict)
    FreqCutOff=OverallCnt*FreqCutOffRate
    for Reading,CatsHomsCnts in Homs.items():
        for Cat,HomsCnts in CatsHomsCnts.items():
            AmbCnt=len(HomsCnts)
            HomCnt=sum([Value[1] for Value in HomsCnts.values()])
            if not (HomCnt<FreqCutOff and AmbCnt==1):
                AmbIndexedHoms[AmbCnt].update({(Reading,Cat):HomsCnts})
    AmbSortedHoms=OrderedDict(sorted(AmbIndexedHoms.items(),key=lambda x:x[0]))
    SortedHoms=OrderedDict()
    SortedVars=sorted(AmbIndexedHoms.keys())
    for Variability in SortedVars:
        OrderedStuff=OrderedDict()
        SortedHoms[Variability]=sorted(AmbSortedHoms[Variability],key=lambda x:mymeasure(x),reverse=True)

    return SortedHoms
                    

    
def collect_wdobjs_with_freqs(MecabCorpusFPs):
    HomsProto={}#=defaultdict(dict)
    NonParseables=set()
    MemoiseTable=dict()
    for FP in MecabCorpusFPs:
        with open(FP) as FSr:
            for LiNe in FSr:
                if LiNe=='EOS\n':
                    continue
                
                OrthFtStr=LiNe.strip().split('\t')
                if len(OrthFtStr)!=2:
                    continue
                else:
                    FtEls=OrthFtStr[1].split(',')
                    if len(FtEls)<9 or FtEls[0]=='記号':
                        continue
                WdFtsVals=mecabtools.line2wdfts(LiNe,'corpus')
                WdVals=tuple(WdFtsVals.values())
                if WdVals not in MemoiseTable:
                    try:
                        Wd=mecabtools.MecabWdParse(WdFtsVals)
                    except:
                    #    mecabtools.MecabWdParse(WdFtsVals)
                        NonParseables.add(LiNe.strip())
                    MemoiseTable[WdVals]=Wd
                    HomsProto[Wd]=1
                else:
                    HomsProto[MemoiseTable[WdVals]]+=1
    if len(NonParseables)>len(HomsProto)*.1:
        sys.stderr.write('Too many unparsables, we are returning them insteads\n\n')
        return NonParseables
    return HomsProto

def entropy(Freqs):
    Probs=[Freq/sum(Freqs) for Freq in Freqs]
    return -sum([Prob*math.log(Prob,2) for Prob in Probs])

if __name__=='__main__':
    import argparse,glob,pickle
    Psr=argparse.ArgumentParser()
    Psr.add_argument('input_dir')
    Args=Psr.parse_args()
    MecabCorpusFPs=glob.glob(Args.input_dir+'/*.mecab')
    if not MecabCorpusFPs:
        print('stuff does not exist\n')
        sys.exit()
    #AmbSortedHoms=main(MecabCorpusFPs)
    AmbSortedHoms,_=myModule.ask_filenoexist_execute_pickle(os.path.join(Args.input_dir,'homophone_stats.pickle'),main,([MecabCorpusFPs],{}))
        
    for AmbCnt,Homs in AmbSortedHoms.items():
        sys.stdout.write('Orth variability: '+str(AmbCnt)+'\n\n')
        FreqSortedHoms=sorted(Homs.items(),key=lambda x:entropy([Freq for (_,Freq) in  x[1].values()]),reverse=True)
        for (ReprCat,OrthsWdFreqs) in FreqSortedHoms:
            OrthsFreqsStr=' / '.join([Orth+' '+str(Freq) for (Orth,(_Wd,Freq)) in OrthsWdFreqs.items()])
            sys.stdout.write(repr(ReprCat)+': '+OrthsFreqsStr+'\n')
        sys.stdout.write('\n')
