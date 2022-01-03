import importlib,os,sys,pickle
from collections import defaultdict
from mecabtools import mecabtools
from pythonlib_ys import main as myModule
importlib.reload(mecabtools)
import collections
import time
from pdb import set_trace
#importlib.reload(count_homophones)


def main(FPs,CHomStats,FileOutP=False,OutDir=None,InLineP=False,FixedFtLength=0,ThreshRate=0.1,unambiguousOnly=False,DebugLevel=0):
    FPs=sorted(FPs)
    fileCnt=len(FPs)
    failed=[]
    AvgHomOcc=sum([CHomStat.distrib.totalocc for CHomStat in CHomStats])/len(CHomStats)
    OccThresh=AvgHomOcc*ThreshRate
    OrgCHomStatCnt=len(CHomStats)
    sys.stderr.write('original homstat count:'+str(OrgCHomStatCnt)+'\n')
    KeyedSelectedCHomStats={tuple(CHomStat.cluster_on.items()):CHomStat for CHomStat in CHomStats if CHomStat.entropy>0.5 and CHomStat.distrib.totalocc>=OccThresh}
    if unambiguousOnly:
        KeyedSelectedCHomStats={Key:HStat for (Key,HStat) in KeyedSelectedCHomStats.items() if len(HStat.kanji_clusters)==1 or HStat.kanji_entropy<0.4}
    sys.stderr.write('filtered homstat count:'+str(len(KeyedSelectedCHomStats))+'\n')
    # structure by pos the CHoms for easier search
    KeyedCHomStatsNotEntirelySeen=defaultdict(dict);RelvProns=set()
    for FtsVals,CHom in KeyedSelectedCHomStats.items():
        PoS=FtsVals[0][1]
        Pron=FtsVals[4][1]
        RelvProns.add(Pron)
        CHomUnseenInds=(CHom,list(range(len(CHom.all_words_freqsorted))))
        if PoS not in KeyedCHomStatsNotEntirelySeen:
            KeyedCHomStatsNotEntirelySeen[PoS]={FtsVals:CHomUnseenInds}
        else:
            KeyedCHomStatsNotEntirelySeen[PoS].update({FtsVals:CHomUnseenInds})    
    FtsIDs={Key:Cntr for (Cntr,Key) in enumerate(KeyedSelectedCHomStats.keys())}
    NotSelectedCHomStats=sorted([CHomStat for CHomStat in CHomStats if CHomStat.entropy>0.5 and CHomStat.distrib.totalocc<OccThresh],key=lambda CHom:CHom.distrib.totalocc,reverse=True)
    Tops=[CHomStat.cluster_on for CHomStat in NotSelectedCHomStats[:50]]
    SeenIrrelvLines=set();SeenRelvLinesFtsVals=collections.defaultdict(int)
    Cache=(SeenIrrelvLines,SeenRelvLinesFtsVals)
    sys.stderr.write('we will do '+str(fileCnt)+' files\n')
    KeyedCHomStatsPair=(KeyedCHomStatsNotEntirelySeen,defaultdict(dict))
    RelvCats=KeyedCHomStatsNotEntirelySeen.keys()

    for cntr,FP in enumerate(FPs):
        sys.stderr.write('entirely unseen homstat counts: ')
        sys.stderr.write(str(sum([len(stats) for stats in KeyedCHomStatsNotEntirelySeen.values()])))
        sys.stderr.write('\n')
        if (cntr+1)%10==0:
            sys.stderr.write(str(cntr+1)+' files done\n')
        #sys.stderr.write(str(len(KeyedSelectedCHomStats))+'\n')
        sys.stderr.write(FP+'\n')
        if not FileOutP:
            OutFP=None
        else:
            OutDir=os.path.dirname(FP) if OutDir is None else OutDir
            OutFP=os.path.join(OutDir,os.path.basename(FP)+'.normed')
        try:
            Cache,KeyedCHomStatsPair=normalise_mecab_file(FP,KeyedCHomStatsNotEntirelySeen,OutFP,Cache,FtsIDs,RelvCats,RelvProns,FixedFtLength=FixedFtLength,DebugLevel=DebugLevel)
        except:
            normalise_mecab_file(FP,KeyedCHomStatsNotEntirelySeen,OutFP,Cache,FtsIDs,RelvCats,RelvProns)
            print('===FAILED==== '+FP)
            failed.append(FP)

def normalise_mecabline(Line,CHomStat,FtsIDs):
    #first bool is 'normalisable thanks to apparent unambiguousness or not', second 'as is or not' the second 'true' implies the first false so we don't have False,False
#    ZenNumInds=[Ind for (Ind,KInds) in enumerate(CHomStat.kanji_clusters) if any(ZenNum in CHomStat.all_words_freqsorted[KInds[0]].orth for ZenNum in ('１','２','３','４','５','６','７','８','９','０'))]
 #   for Ind in ZenNumInds[::-1]:
    #    CHomStat.kanji_clusters.remove(CHomStat.kanji_clusters[Ind])                                                      
                                                          
    # we say it's ambiguous if there are more than two kanji renderings
    if len(CHomStat.kanji_clusters)!=1:
        NewLine=Line;Normalisable=False;AsIs=True
    elif len(CHomStat.kanji_clusters[0])>=2:# and 0 not in CHomStat.kana_cluster:# and
        NewLine=Line;Normalisable=False;AsIs=True
    else:
        ChosenOrth=CHomStat.all_words_freqsorted[0].orth
#        if 0 in CHomStat.kana_cluster and (CHomStat.kanji_clusters and CHomStat.kanji_clusters[0]):
        KanjiInd=CHomStat.kanji_clusters[0][0]
        MostFreqKanjiStr=CHomStat.all_words_freqsorted[KanjiInd].orth
        #else:
        #    MostFreqKanjiStr=''
        ID=FtsIDs[tuple(CHomStat.cluster_on.items())]
        MWd=mecabtools.mecabline2mecabwd(Line,'corpus')
        Normalisable=True
        NewOrthCommonEls=['n',str(ID),MostFreqKanjiStr]
        if MWd.orth!=ChosenOrth:
            AsIs=False;
            NewOrthEls=[ChosenOrth]+NewOrthCommonEls+[MWd.orth]
        else:
            NewOrthEls=[MWd.orth]+NewOrthCommonEls
            AsIs=True

        NewOrth='_'.join(NewOrthEls)
        MWd.change_feats({'orth':NewOrth})
        NewLine=MWd.get_mecabline()

    return NewLine,Normalisable,AsIs

def pick_lemma(CHomStat):
    return 'aaa'
    
def normalise_mecab_file(FP,KeyedCHomStatsNotEntirelySeen,OutFP,Cache,FtsIDs,RelvCats,RelvProns,DebugLevel=1,FixedFtLength=None):
    SeenIrrelvLines,SeenRelvLinesFtsVals=Cache
    
    get_change_msg=lambda Normed,AsIs,OldOrth: 'normalisable:'+(' left unnormed due to ambiguity' if not Normed else ' normed')+','+( ' old orth: '+OldOrth if not AsIs else ' same form kept')
    Out=sys.stdout if OutFP is None else open(OutFP+'.tmp','wt')
    with open(FP,errors='replace') as FSr:
        for cntr,LiNe in enumerate(FSr):
            ToDo=False
            Msg=''
            if DebugLevel>=2:
                sys.stderr.write('Org: '+LiNe)
            Line=LiNe.strip()
            if irrelevant_p(Line,SeenIrrelvLines,RelvCats,RelvProns):
                Normed=False;AsIs=True
                SeenIrrelvLines.add(Line)
                Out.write(LiNe)
                continue
            elif Line in SeenRelvLinesFtsVals:
                (NewLine,Normed,AsIs)=SeenRelvLinesFtsVals[Line]
                if DebugLevel:
                    Msg=get_change_msg(Normed,AsIs,Line.split('\t')[0])
                    NewLine=NewLine+'\t'+Msg
                Out.write(NewLine+'\n')
                continue
            
            LineFtsVals=mecabtools.line2wdfts(Line,'corpus')
            FtLen=len(LineFtsVals)
            OrgOrth=LineFtsVals['orth'];  PoS=LineFtsVals['cat']
            OrgInfpat=LineFtsVals['infpat']
            LineFtsVals={Ft:Val for (Ft,Val) in LineFtsVals.items() if Ft in ('cat','subcat','subcat2','infpat','pronunciation')}

            LineFtsVals=tuple(LineFtsVals.items())
            TgtFtsVals=next((FtsVals for FtsVals in KeyedCHomStatsNotEntirelySeen[PoS].keys() if LineFtsVals==FtsVals),None)
                            
            if not TgtFtsVals:
                SeenIrrelvLines.add(Line)
                AsIs=True;Normed=False
                Out.write(LiNe)
                continue

            ToDo=True
            TgtCHomStat=KeyedCHomStatsNotEntirelySeen[PoS][LineFtsVals][0]
            FndInd=next((ind for (ind,wd) in enumerate(TgtCHomStat.all_words_freqsorted) if OrgOrth==wd.orth and OrgInfpat==wd.infpat),None)
            if FndInd in KeyedCHomStatsNotEntirelySeen[PoS][TgtFtsVals][1]:
                KeyedCHomStatsNotEntirelySeen[PoS][TgtFtsVals][1].remove(FndInd)
            
            if not KeyedCHomStatsNotEntirelySeen[PoS][TgtFtsVals][1]:
                del KeyedCHomStatsNotEntirelySeen[PoS][TgtFtsVals]
                SeenRelvLinesFtsVals[Line]=LineFtsVals
            try:
                NewLine,Normed,AsIs=normalise_mecabline(Line,TgtCHomStat,FtsIDs)
            except:
                normalise_mecabline(Line,TgtCHomStat,FtsIDs)
            ChosenOrth=NewLine.split('\t')[0]

                            #NewLine=NewLine if any(NewLine.endswith(Char) for Char in ('i','s')) else NewLine+','+LstStuff
            SeenRelvLinesFtsVals[Line]=(NewLine,Normed,AsIs)
                            #except:
                            #   sys.stderr.write(Line+' failed \n')
                            #  continue
            if DebugLevel:
                Msg=get_change_msg(Normed,AsIs,Line.split('\t')[0])
                OtherOrths=[Wd.orth for Wd in TgtCHomStat.all_words_freqsorted if Wd.orth!=ChosenOrth and Wd.orth!=OrgOrth]
                Msg=Msg+' / this is the first time for this cluster'+(' other orth(s): '+' '.join(OtherOrths) if OtherOrths else '')
            if AsIs and not Normed:
                NewLine=Line
            if DebugLevel and Msg:
                NewLine=NewLine+'\t'+Msg
            if DebugLevel>=2:
                sys.stderr.write('New: '+NewLine+'\n\n')
            Out.write(NewLine+'\n')


            #sys.stderr.write('')
    if OutFP:
        Out.close()
        os.rename(OutFP+'.tmp',OutFP)
    return (SeenIrrelvLines,SeenRelvLinesFtsVals),KeyedCHomStatsNotEntirelySeen

def irrelevant_p(Line,SeenIrrelvLines,RelvCats,RelvProns):        
    if Line=='EOS':
        return True
    elif Line.endswith('*'):
        return True
    elif Line in SeenIrrelvLines:
        return True
    else:
        Fts=Line.split('\t')[1].split(',')
        Cat,Pron=Fts[0],Fts[-1]
        if Cat not in RelvCats:
            return True
        if Pron not in RelvProns:
            return True
    return False

    
        
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
    import argparse,glob,re
    pser=argparse.ArgumentParser()
    pser.add_argument('input_dir')
    pser.add_argument('--debug-level',type=int,default=1)
    pser.add_argument('--homstat-dir')
    pser.add_argument('--out-dir',default=None)
    pser.add_argument('--mecab-ext',default='mecab')
    pser.add_argument('--feat-len',type=int,default=0)
    pser.add_argument('--homstat-fn',default='clustered_homs.pickle')
    pser.add_argument('--exclude-file-regex')
    pser.add_argument('--unambiguous-only',action='store_true')
    myArgs=pser.parse_args()

    if not myArgs.homstat_dir:
        myArgs.homstat_dir=myArgs.input_dir
#        regex=re.compile(myArgs.exclude_file_regex)
    FPs=[FP for FP in glob.glob(os.path.join(myArgs.input_dir,'*.'+myArgs.mecab_ext)) if os.path.isfile(FP) ]
    
    HomStatFP=os.path.join(myArgs.homstat_dir,myArgs.homstat_fn)

    if not FPs:
        print('no mecab files found (based on the ext "'+myArgs.mecab_ext+'")\n')
        sys.exit(1)
    if not os.path.isdir(myArgs.homstat_dir):
        print('homstat dir not found')
        sys.exit(1)
    if not os.path.isfile(HomStatFP):
        print('homstat file not found\n')
        sys.exit(1)
    HomStats,_=pickle.load(open(HomStatFP,'br'))
    FileOutP=True if myArgs.out_dir else False
    if myArgs.out_dir:
        if not os.path.isdir(os.path.dirname(myArgs.out_dir)):
            print('out dir (parent) does not exist\n')
            sys.exit(1)
        else:
            if not os.path.isdir(myArgs.out_dir):
                os.makedirs(myArgs.out_dir)        
    main(FPs,HomStats,FixedFtLength=myArgs.feat_len,OutDir=myArgs.out_dir,DebugLevel=myArgs.debug_level,FileOutP=FileOutP,unambiguousOnly=myArgs.unambiguous_only)
