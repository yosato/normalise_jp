#/usr/bin/env python3

import imp,sys,os,subprocess,glob,shutil,re
import compress_inflecting, normalise_mecab
from mecabtools import mecabtools
from pythonlib_ys import main as myModule
imp.reload(compress_inflecting)
imp.reload(normalise_mecab)
imp.reload(mecabtools)

def insert_el(El,List,Pos):
    BinarySplits=(List[:Pos],List[Pos:])
    return BinarySplits[0]+[El]+BinarySplits[1]

def refresh_model(DicDir,ConfDir,ModelDir):
    #if not all(os.path.isfile(os.path.join(DicDir,DicFN)) for DicFN in ('non-inflecting.csv','inflecting.csv')):
        
    list(map(os.remove, glob.glob(ModelDir+'/*')))
    list(map(lambda x:shutil.copy(x,ModelDir), glob.glob(DicDir+'/*.csv')))
    list(map(lambda x:shutil.copy(x,ModelDir), glob.glob(ConfDir+'/*')))
    Cmd=' '.join(['mecab-dict-index -d',ModelDir,'-o',ModelDir])
    subprocess.call(Cmd,shell=True)

def main0(StdJpTxtFP,OrgDicLoc,ModelDir=None,DicSkip=True,ExemplarFP=None,FreqWdFP=None,ExtraIndsFts={},Debug=0):
    Fts=mecabtools.DefFts
    for (Ind,Ft) in ExtraIndsFts:
        Fts=insert_el(Ft,Fts,Ind+1)
    
    if not any(StdJpTxtFP.endswith(Ext) for Ext in ('.txt','mecab')):
        sys.exit('input filename has to have the extension of either .txt or .mecab (and has to be text or mecab respectively)')
    elif 'rawData' not in StdJpTxtFP:
        sys.exit('dirname \'rawData\' is required')
    else:
        # the new stuff will be in 'processedData'
        CmpMecabDir=os.path.dirname(StdJpTxtFP).replace('rawData','processedData')
        if not os.path.isdir(CmpMecabDir):
            os.makedirs(CmpMecabDir)
        CmpMecabFN=re.sub(r'(.txt|.mecab)','.compressed.mecab',os.path.basename(StdJpTxtFP))
        TextOrMecab='text' if StdJpTxtFP.endswith('.txt') else 'mecab'

    #################################
    ## compression on dic and corpus
    #################################
    ### dic first ###
    InfCats=('adjectives','verbs','auxiliaries')
    DicFPs=glob.glob(os.path.join(OrgDicLoc,'*.csv'))
    DicFPsInf=[ FP for FP in DicFPs if any(Cat in os.path.basename(FP) for Cat in InfCats) ]
    assert(DicFPsInf)
    NewDicLoc=OrgDicLoc.replace('rawData','processedData')
    CmpDicFPs=[ myModule.change_ext(os.path.join(NewDicLoc,os.path.basename(OrgDicFP)),'compressed.csv') for OrgDicFP in DicFPsInf ]
    if DicSkip:
        FreshlyDoneP=False
    else:
    # original dics to compress, inflecting categories only
        for (DicFPInf,CmpDicFP) in zip(DicFPsInf,CmpDicFPs):
            Ret=myModule.ask_filenoexist_execute(CmpDicFPs,compress_inflecting.main0,([DicFPInf],{'CorpusOrDic':'dic','OutFP':CmpDicFP,'Debug':Debug}))
        FreshlyDoneP=True if Ret is None else False

    # then the corpora
    CmpMecabFP=os.path.join(CmpMecabDir, CmpMecabFN)
    ModelDir=CmpMecabDir+'/models' if ModelDir is None else ModelDir
    if not os.path.isdir(ModelDir):
        os.makedirs(ModelDir)
    if not os.path.isfile(os.path.join(ModelDir,'dicrc')) or myModule.prompt_loop_bool('Refreshing the model?',TO=5):
        ConfLoc=os.path.join(os.path.dirname(OrgDicLoc),'models')
        refresh_model(OrgDicLoc,ConfLoc,ModelDir)
    
    FreshlyDoneP=myModule.ask_filenoexist_execute(CmpMecabFP,build_compressed_corpus,([StdJpTxtFP,ModelDir,CmpMecabFP],{'Fts':Fts,'TextOrMecab':TextOrMecab,'Debug':Debug}),LoopBackArg=(0,2),DefaultReuse=not FreshlyDoneP)
    ###################################
    ## normalisation of the corpus
    ##################################    
    # for normalisation you include non-inflecting dic as well
    DicFPNonInf=os.path.join(OrgDicLoc,'non-inflecting.csv')
    FinalMecabFP=myModule.change_stem(CmpMecabFP,'.normed')
    # an exemplar is a word with a single dominant normalisation case
    if not ExemplarFP:
        DefExemplarFP=os.path.join(OrgDicLoc,'exemplars.txt')
        if os.path.isfile(DefExemplarFP):
            ExemplarFP=DefExemplarFP
        else:
            sys.stderr.write('\nExemplar file is not found in the dic dir\n')
            ExemplarFP=None
    else:
        ExemplarFP=ExemplarFP
    # one could limit the targets to frequent words only
    FreqWdFP='/links/rawData/mecabStdJp/corpora/freqwds.txt' if not FreqWdFP else FreqWdFP
    # core part
    normalise_mecab.main0([DicFPNonInf]+CmpDicFPs,[CmpMecabFP],ProbExemplarFP=ExemplarFP,FreqWdFP=FreqWdFP,OutFP=FinalMecabFP,Fts=Fts,CorpusOnly=True,UnnormalisableMarkP=True,Debug=Debug)
    print('file outputted to '+FinalMecabFP)


def do_mecab_parse(InFP,ModelDir,OutFP,Format='standard'):
    if not os.path.isfile(os.path.join(ModelDir,'dicrc')):
        sys.exit('\n'+InFP+' is not a mecab modeldir')
    
    if not os.path.isfile(InFP) or os.path.getsize(InFP)==0:
        sys.exit('file nonexistent or empty')
    if Format == 'standard':
        FormatArg=''
    else:
        if not any(Format!=FormatType for FormatType in ('wakati','dic')):
            sys.exit('mecab format not correct\n')
        elif Format=='dic':
            FormatArg='--node-format="%m,%phl,%phr,%c,%H\n"'
        elif Format=='wakati':
            FormatArg='--node-format="%m" --eos-format="\n"'

    # file only if over 10mb else both file and stdout
    RedirectCmd='>' if os.path.getsize(InFP)/1000/1000>10 else '| tee'
    
    Cmd=' '.join(['mecab -d',ModelDir,FormatArg,InFP,RedirectCmd, OutFP])
    Proc=subprocess.Popen(Cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    (StdOut,StdErr)=Proc.communicate()
    Lines=StdOut.decode().strip().split('\n')
    if len(Lines)<=2 or Lines[-1]!='EOS':
        SuccessP=False
    else:
        Code=Proc.returncode
        SuccessP=True if Code==0 else False
#        SuccessP=False if StdErr else True
    return SuccessP,StdOut,StdErr


def build_compressed_corpus(StdJpTxtFP,StdModelLoc,CmpMecabFP,TextOrMecab='text',Debug=0,Fts=None):
    # do mecab parsing with the standard text if necessary
    if TextOrMecab=='text':
        StdMecabFP=myModule.change_ext(StdJpTxtFP,'mecab').replace('rawData','processedData')
        SuccessP,StdOut,StdErr=do_mecab_parse(StdJpTxtFP,StdModelLoc,Format='standard',OutFP=StdMecabFP)
        if not SuccessP:
            print('\nmecab process failed with the following error\n')
            print(StdErr)
            sys.exit()
        elif StdErr:
            print('\nmecab producing the following warning\n')
            print(StdErr.decode())
    elif TextOrMecab=='mecab':
        StdMecabFP=StdJpTxtFP
    # do compression of the above
    Out=CmpMecabFP
    #Out=None
    compress_inflecting.main0(StdMecabFP,CorpusOrDic='corpus',OutFP=Out,Debug=Debug,Fts=Fts)
    return CmpMecabFP
    
def main():
    import argparse
    ArgPsr=argparse.ArgumentParser(description='''
    to be written
    ''')
    ArgPsr.add_argument('raw_fp')
    ArgPsr.add_argument('dic_loc')
    ArgPsr.add_argument('--modeldir')
    ArgPsr.add_argument('--exemplar-fp','-e')
    ArgPsr.add_argument('--freqwd-fp','-f')
    ArgPsr.add_argument('--extra-indsfts',nargs='+')
    ArgPsr.add_argument('--debug',type=int,default=0)
    Args=ArgPsr.parse_args()

    if not os.path.isfile(Args.raw_fp):
        sys.exit('\n\n  source file not found \n')
    if Args.extra_indsfts:
        if len(Args.extra_indsfts)%2!=0:
            sys.exit('extra-indsfts option must consist of even num of args')
        Evens=[];Odds=[]
        for Cntr,El in enumerate(Args.extra_indsfts):
            if Cntr%2==0:
                if not El.isnumeric():
                    sys.exit('extra-indsfts option odd num args must be integer')
                Evens.append(int(El))
            else:
                Odds.append(El)
        ExtraIndsFts=list(zip(Evens,Odds))
        #if any(type(Key).__name__!='int' for Key in ExtraIndsFts.keys()):
         #   sys.exit('extra-indsfts option odd num args must be integer')
    else:
        ExtraIndsFts=[]

    if (Args.exemplar_fp is not None and not os.path.isfile(Args.exemplar_fp)) or (Args.freqwd_fp is not None and not os.path.isfile(Args.freqwd_fp)):
        sys.exit('\n\n one of the assisting files for normalisations (exemplar, freqwd) not found\n')
        
    
    main0(Args.raw_fp,Args.dic_loc,ModelDir=Args.modeldir,ExemplarFP=Args.exemplar_fp,FreqWdFP=Args.freqwd_fp,ExtraIndsFts=ExtraIndsFts,Debug=Args.debug)

if __name__=='__main__':
    main()
