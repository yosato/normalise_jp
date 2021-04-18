import importlib,os,sys,pickle
from mecabtools import mecabtools
from pythonlib_ys import main as myModule
importlib.reload(mecabtools)
import collections
import time
#importlib.reload(count_homophones)

def main(FPs,CHomStats,FileOutP=False,OutDir=None,InLineP=False):
    KeyedSelectedCHomStats={tuple(CHomStat.cluster_on.items()):CHomStat for CHomStat in CHomStats if CHomStat.entropy>0.5 and CHomStat.distrib.totalocc>10}
    SeenIrrelvLines=set();SeenRelvLinesFtsVals=collections.defaultdict(int)
    Cache=(SeenIrrelvLines,SeenRelvLinesFtsVals)
    
    for FP in FPs:
        sys.stderr.write(FP+'\n')
        if not FileOutP:
            OutFP=None
        else:
            OutDir=os.path.dirname(FP) if OutDir is None else OutDir
            OutFP=os.path.join(OutDir,os.path.basename(FP)+'.normed')
        Cache=normalise_mecab_file(FP,KeyedSelectedCHomStats,OutFP,Cache)

def normalise_mecabline(Line,CHomStat):
    if len(CHomStat.kanji_clusters)<=1 or 0 in CHomStat.kana_cluster:
        ChosenOrth=CHomStat.all_words_freqsorted[0].orth
    else:
        if myModule.at_least_one_of_chartypes_p(Line.split('\t')[0],['han']):
            return Line,True,True
        else:
            return Line,False,True
    MWd=mecabtools.mecabline2mecabwd(Line,'corpus')
    if MWd.orth!=ChosenOrth:
        AsIs=False
        MWd.change_feats({'orth':ChosenOrth})
    else:
        AsIs=True
    return MWd.get_mecabline(),True,AsIs

def pick_lemma(CHomStat):
    return 'aaa'
    
def normalise_mecab_file(FP,KeyedCHomStats,OutFP,Cache,Debug=1):
    SeenIrrelvLines,SeenRelvLinesFtsVals=Cache
    get_change_msg=lambda Normed,AsIs,OldOrth: 'normalisable:'+(' left unnormed due to ambiguity' if not Normed else ' normed')+','+( ' old orth: '+OldOrth if not AsIs else ' same form kept')
    Out=sys.stdout if OutFP is None else open(OutFP+'.tmp','wt')
    with open(FP) as FSr:
        for LiNe in FSr:
            Msg=''
            Line=LiNe.strip()
            if Line=='EOS':
                continue
            if Line in SeenIrrelvLines:
                AsIs=True;Normed=False
            elif Line in SeenRelvLinesFtsVals:
                NewLine,Normed,AsIs=SeenRelvLinesFtsVals[Line]
                if Debug:
                    Msg=get_change_msg(Normed,AsIs,Line.split('\t')[0])
            else:
#                try:
                TgtFtsVals=next((FtsVals for FtsVals in KeyedCHomStats if mecabtools.featsvals_in_line_p(Line,FtsVals)),None)
                #except:
                 #   print(Line)
                if not TgtFtsVals:
                    SeenIrrelvLines.add(Line)
                    AsIs=True;Normed=False
                else:
                    LstStuff=Line.split(',')[-1]
                    OrgOrth=Line.split('\t')[0]
                    TgtCHomStat=KeyedCHomStats[TgtFtsVals]
                    try:
                        NewLine,Normed,AsIs=normalise_mecabline(Line,TgtCHomStat)
                        ChosenOrth=NewLine.split('\t')[0]

                        NewLine=NewLine if any(NewLine.endswith(Char) for Char in ('i','s')) else NewLine+','+LstStuff
                    
                        SeenRelvLinesFtsVals[Line]=(NewLine,Normed,AsIs)
                    except:
                        sys.stderr.write(Line+' failed \n')
                        continue
                    if Debug:
                        Msg=get_change_msg(Normed,AsIs,Line.split('\t')[0])
                        OtherOrths=[Wd.orth for Wd in TgtCHomStat.all_words_freqsorted if Wd.orth!=ChosenOrth and Wd.orth!=OrgOrth]
                        Msg=Msg+' / this is the first time for this cluster'+(' other orth(s): '+' '.join(OtherOrths) if OtherOrths else '')
            if AsIs:
                NewLine=Line
            if Debug and Msg:
                NewLine=NewLine+'\t'+Msg
            Out.write(NewLine+'\n')
    if OutFP:
        Out.close()
    return (SeenIrrelvLines,SeenRelvLinesFtsVals)

            
    
        
def normalise_chars_file(FP,CHomStat):
    with open(FP) as FSr:
        for LiNe in FSr:
            if LiNe=='EOS\n':
                continue
            FtsVals=mecabtools.mecabline2featsvals(LiNe.strip())
            RelvFtsVals={Ft:Val for (Ft,Val) in FtsVals.items() if Ft in ('cat','subcat','subcat2','infpat','pronunciation')}
            if RelvFtsVals not in TgtFtsVals:
                continue
            
            
            
    
    

if __name__=='__main__':
    import argparse,glob
    pser=argparse.ArgumentParser()
    pser.add_argument('input_dir')
    pser.add_argument('--hom-dir')
    pser.add_argument('--mecab-ext',default='mecab')
    pser.add_argument('--homstat-fn',default='clustered_homs.pickle')
    myArgs=pser.parse_args()

    if not myArgs.hom_dir:
        myArgs.hom_dir=myArgs.input_dir
    FPs=[FP for FP in glob.glob(os.path.join(myArgs.input_dir,'*'+myArgs.mecab_ext)) if os.path.isfile(FP)]
    if not FPs:
        print('no mecab files found (based on the ext "'+myArgs.mecab_ext+'")\n')
        sys.exit(1)
    HomStatFPs=glob.glob(os.path.join(myArgs.hom_dir,'*'+myArgs.homstat_fn))
    if len(HomStatFPs)!=1:
        print('sth wrong for homstat\n')
        sys.exit(1)
    HomStat=pickle.load(open(HomStatFPs[0],'br'))  
    main(FPs,HomStat)
