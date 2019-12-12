import sys,os,imp
from collections import defaultdict,OrderedDict
sys.path.append('/home/yosato/myProjects/myPythonLibs/mecabtools')
from mecabtools import mecabtools
imp.reload(mecabtools)

def load_pickle(PickledFP):
    return pickle.load(open(PickledFP,'rb'))

def main(MecabCorpusFPs,FreqCutOff=10,LemmaBaseP=True):
    Homs=defaultdict(dict)
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
                try:
                    Wd=mecabtools.mecabline2mecabwd(LiNe.strip(),CorpusOrDic='corpus')
                except:
                    mecabtools.mecabline2mecabwd(LiNe.strip(),CorpusOrDic='corpus')
                if Wd.cat=='記号':
                    continue

                if 'pronunciation' in Wd.__dict__:
                    Repr=Wd.lemma if LemmaBaseP else Wd.orth
                    if Repr not in Homs[Wd.pronunciation]:
                        Homs[Wd.pronunciation].update({Repr:[Wd,1]})
                    else:
                        Homs[Wd.pronunciation][Repr][1]+=1
                            
    AmbIndexedHoms=defaultdict(dict)
    for Reading,HomsCnts in Homs.items():
        AmbCnt=len(HomsCnts)
        HomCnt=sum([Value[1] for Value in HomsCnts.values()])
        if HomCnt>=FreqCutOff:
            AmbIndexedHoms[AmbCnt].update({Reading:HomsCnts})
    AmbSortedHoms=OrderedDict(sorted(AmbIndexedHoms.items(),key=lambda x:x[0]))
    return AmbSortedHoms
                    

if __name__=='__main__':
    import argparse,glob,pickle
    Psr=argparse.ArgumentParser()
    Psr.add_argument('input_dir')
    Args=Psr.parse_args()
    MecabCorpusFPs=glob.glob(Args.input_dir+'/*.mecab')
    if not MecabCorpusFPs:
        print('stuff does not exist\n')
        sys.exit()
    #Homs=main(MecabCorpusFPs)
    #with open('hello.pickle','wb') as FSw:
    #    pickle.dump(Homs,FSw)
    Homs=load_pickle('hello.pickle')
    print()
