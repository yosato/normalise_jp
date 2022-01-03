from pythonlib_ys import main as myModule
import re,os,sys,json,time
from bidict import bidict
from collections import defaultdict

def main(fps,metaFile,kanjiFiles=[],genre_replace=False,authorCutoff=float('inf')):
#    fnsMeta=get_file_metadata_mapping(metaFile) if metaFile else {}
    metaIDsFtvals=json.load(open(metaFile))
    authorsDataCnts=defaultdict(int)
    IDsFNs=bidict({fn.split('_')[0]:fn for fn in [os.path.basename(fp) for fp in fps] })
    fnsMeta={IDsFNs[ID]:FtsVals for (ID,FtsVals) in metaIDsFtvals.items() if ID in IDsFNs }
#    kanjisComplexities,kanjisFreqs=get_kanji_features(kanjiFiles[0],kanjiFiles[1]) if kanjiFiles else ({},{})
    tokenCnt=0;cumNotFndKanjis=set();clusterIDsCnts=defaultdict(int)
    homFtNs=['normedForm','clusterID','kanjiRep','orgForm']
    mecabFtNs=['PoS','subcat','subcat2']
    sakuhinFtNs=['classification','publicationYear']
    authorFtNs=['authorName','yearBorn']
    metaFtNs=['ID']+sakuhinFtNs+authorFtNs
    newFtNs=homFtNs+mecabFtNs+metaFtNs+['kanaKanji']
    sys.stdout.write(','.join(newFtNs)+'\n')
    for fileCntr,fp in enumerate(fps):
        if fileCntr!=0 and fileCntr%100==0:
            sys.stderr.write(str(fileCntr)+'\n')
            time.sleep(0.5)
        fn=os.path.basename(fp)
        ID=IDsFNs.inverse[fn]
        metaFeatsOrg=metaIDsFtvals[ID]
        author=metaFeatsOrg['作家データ']
        yearBorn='*' if '生年' not in author else author['生年'][0]
        authorName=author['作家名']
        if authorName in authorsDataCnts and authorsDataCnts[authorName]>authorCutoff:
            continue
#        metaFeatsOrg=fnsMeta[fnStem] if fnStem in fnsMeta else ('*','*','*','*','*',os.path.basename(fp)[:2],'*')
        with open(fp) as fsr:
            for liNe in fsr:
                if re.match(r'.+_n_',liNe):
                    orthEtcStr,feats=liNe.strip().split('\t')[0:2]
                    orthEtc=orthEtcStr.split('_')
                    assert len(orthEtc)==4 or len(orthEtc)==5
                    normedOrth,_,clusterID,kanjiStr=orthEtc[:4]
                    if len(orthEtc)==4:
                        orgOrth=orthEtc[0]
                    else:
                        orgOrth=orthEtc[-1]
                    if not myModule.at_least_one_of_chartypes_p(orgOrth,['han','katakana','hiragana']):
                        sys.stderr.write(orgOrth+' ignored\n')
                        continue
#                    kanjiStr=orth if len(orthEtc)==3 else orthEtc[3]
                    homFeats=[normedOrth,clusterID,kanjiStr,orgOrth]
                    #homFtNs=['actualForm','clusterID','kanjiStr']
                    mecabFeats=feats.split(',')
                    mecabFeats=mecabFeats[:2]+[mecabFeats[-4]]
                    #mecabFtNs=['PoS','subcat','subcat2']
                    #docID=os.path.basename(fp).replace('.mecab.normed','')

                    sakuhin=metaFeatsOrg['作品データ']
                    if '初出' in sakuhin:
                        pubYearStrM=re.search(r'([12][0-9][0-9][0-9])',sakuhin['初出'])
                        if pubYearStrM:
                            pubYear=pubYearStrM.groups()[0]
                    else:
                        if '親本データ' in metaFeatsOrg and '初版発行日' in metaFeatsOrg['親本データ']:
                            pubDate=metaFeatsOrg['親本データ']['初版発行日']
                            typeN=type(pubDate).__name__
                            if typeN=='list':
                                pubYear=pubDate[0]
                            elif typeN=='str':
                                pubYearStrM=re.search(r'([12][0-9][0-9][0-9])',pubDate)
                                if pubYearStrM:
                                    pubYear=pubYearStrM.groups()[0]
                                else:
                                    break
                            else:
                                break
                        else:
                            break
                    sakuhinFts=[sakuhin['分類'].split()[-1],pubYear]
                    #sakuhinFtNs=['classification','publicationYear']
                    #authorFtNs=['authorName','yearBorn']
                    authorFts=[authorName,yearBorn]
                    metaFeats=[ID]+sakuhinFts+authorFts
                    #metaFtNs=['ID']+sakuhinFtNs+authorFtNs
                    #if genre_replace and metaFeats[-2]=='PB':
                    #    metaFeats[-2]=metaFeats[3].replace(' ','_')
                    #relvMetaFeats=[myStr.strip().replace(' ','_') for (cntr,myStr) in enumerate(metaFeats) ]
                    newFeats=homFeats+mecabFeats+metaFeats
                    #newFtNs=homFtNs+mecabFtNs+metaFtNs.append('kanaKanji')
                    if myModule.at_least_one_of_chartypes_p(orgOrth,['han']):
                        OrthCat='kanji'
                    elif myModule.at_least_one_of_chartypes_p(orgOrth,['katakana']):
                        OrthCat='katakana'
                        kanjiFts=[]
                    elif myModule.at_least_one_of_chartypes_p(orgOrth,['hiragana']):
                        OrthCat='hiragana'
                    else:
                        OrthCat='others'

                    '''
                    if OrthCat=='others':
                        continue
                    else:
                        fndKanjis=[char for char in kanjiStr if myModule.of_chartypes_p(char,['han'])]
                        if not fndKanjis:
                            continue
                        elif any(fndKanji not in kanjisComplexities for fndKanji in fndKanjis):
                            notFndKanjis=[fndKanji for fndKanji in fndKanjis if fndKanji not in kanjisComplexities]
                            sys.stderr.write('kanji not found in complexity list for '+repr(notFndKanjis)+'\n')
                            cumNotFndKanjis.update(notFndKanjis)
                            continue
                        notFndInFreqs=[fndKanji for fndKanji in fndKanjis if fndKanji not in kanjisFreqs]
                        if notFndInFreqs:
                            sys.stderr.write('kanji not found in freq list for '+repr(notFndInFreqs)+'\n')
                            for notFnd in notFndInFreqs:
                                kanjisFreqs[notFnd]=5
                        aveFndKanjiComplexity=sum([kanjisComplexities[fndKanji] for fndKanji in fndKanjis])/len(fndKanjis)
                        aveFndKanjiFreq=sum([kanjisFreqs[fndKanji] for fndKanji in fndKanjis])/len(fndKanjis)
                    OrthFts=[str(aveFndKanjiComplexity),str(aveFndKanjiFreq),OrthCat,'1' if OrthCat=='kanji' else '0']
                    newFeats.extend(OrthFts)
                    '''
                    if not (fileCntr==0 and tokenCnt==0):
                        assert len(newFeats)==prvFeatsLen
                    
                    sys.stdout.write(','.join([str(Ft) for Ft in newFeats+[OrthCat]])+'\n')
                    tokenCnt+=1
                    prvFeatsLen=len(newFeats)
        authorsDataCnts[authorName]=+tokenCnt


def get_kanji_features(complexity_fp,frequency_fp):
    kanjisComplexities=json.load(open(complexity_fp))
    kanjisFreqs=json.load(open(frequency_fp))
    return kanjisComplexities,kanjisFreqs
    
def get_file_metadata_mapping0(metafile):
    fnsMetas={}
    with open(metafile,'rt') as fsr:
        for cntr,liNe in enumerate(fsr):
            if cntr==0:
                continue
            lineEls=liNe.strip().split(',')
            fn=os.path.basename(lineEls[0])
            newFn=re.sub(r'^(.+)[0-9]+(_)0+([1-9])',r'\1\2\3',fn)
            if '_0' in newFn:
                pass
                #print(newFn)
            else:
                fnsMetas[newFn]=tuple(lineEls[1:])
    return fnsMetas        

if __name__=='__main__':
    import argparse,glob
    psr=argparse.ArgumentParser()
    psr.add_argument('dir')
    psr.add_argument('meta_file_json')
    psr.add_argument('--kanji-complexity-file',default='')
    psr.add_argument('--kanji-freq-file')
    psr.add_argument('--genre-replace',action='store_true')
    psr.add_argument('--author-cutoff',type=float,default=float('inf'))
    myArgs=psr.parse_args()
    fps=glob.glob(os.path.join(myArgs.dir,'*.normed'))
    if not os.path.isdir(myArgs.dir):
        print(myArgs.dir+' does not exist')
        sys.exit()
    if not fps:
        print('no file found')
        sys.exit()
    if not myArgs.meta_file_json.endswith('.json') or not (os.path.isfile(myArgs.meta_file_json)):
        print('no json meta file found')
        sys.exit()
        
    main(fps,myArgs.meta_file_json,kanjiFiles=[myArgs.kanji_complexity_file,myArgs.kanji_freq_file],authorCutoff=myArgs.author_cutoff,genre_replace=myArgs.genre_replace)
