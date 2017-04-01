import imp,sys,os,subprocess,glob
import compress_inflecting, normalise_mecab
from pythonlib_ys import main as myModule
imp.reload(compress_inflecting)
imp.reload(normalise_mecab)


def main0(StdJpTxtFP,DicLoc,StdModelLoc,ExemplarFP=None,FreqWdFP=None,Debug=0):
    # first do the compression on dic and corpus
    #CmpDicFPs=builbd_compressed_dic(StdModelLoc)

    DicFPsInf=[os.path.join(DicLoc,Cat+'.csv') for Cat in ('adjectives','verbs','auxiliaries')]
    DicFPNonInf=os.path.join(DicLoc,'non-inflecting.csv')
    CmpDicFPs=[ myModule.change_stem(DicFPInf,'.compressed',AddOrRemove='add') for DicFPInf in DicFPsInf ]
    for (DicFPInf,CmpDicFP) in zip(DicFPsInf,CmpDicFPs):
        Ret=myModule.ask_filenoexist_execute(CmpDicFPs,compress_inflecting.main0,([DicFPInf],{'CorpusOrDic':'dic','OutFP':CmpDicFP,'Debug':Debug}))
    FreshlyDoneP=True if Ret is None else False
    
    CmpMecabFP=myModule.change_ext(myModule.change_stem(StdJpTxtFP,'.compressed',AddOrRemove='add'),'mecab')
    FreshlyDoneP=myModule.ask_filenoexist_execute(CmpMecabFP,build_compressed_corpus,([StdJpTxtFP,StdModelLoc,CmpMecabFP],{'Debug':Debug}),LoopBackArg=(0,2),DefaultReuse=not FreshlyDoneP)

    # do normalisation of the corpus
    FinalMecabFP=myModule.change_stem(CmpMecabFP,'.normed')
    ExemplarFP=os.path.join(DicLoc,'compressed','exemplars.txt') if not ExemplarFP else ExemplarFP
    FreqWdFP=os.path.join(os.path.dirname(StdJpTxtFP),'freqwds.txt') if not FreqWdFP else FreqWdFP
    normalise_mecab.main0([DicFPNonInf]+CmpDicFPs,[CmpMecabFP],ProbExemplarFP=ExemplarFP,FreqWdFP=FreqWdFP,OutFP=FinalMecabFP,CorpusOnly=True,UnnormalisableMarkP=True,Debug=Debug)
    # do another mecab parsing with a compressed model
#    do_mecab_parse(GluedMecabFP,CNModelLoc,OutFP=FinalMecabFP)

def do_mecab_parse(InFP,ModelDir,OutFP,Format='standard'):
    if Format == 'standard':
        FormatArg=''
    else:
        if not any(Format!=FormatType for FormatType in ('wakati','dic')):
            sys.exit('mecab format not correct\n')
        elif Format=='dic':
            FormatArg='--node-format="%m,%phl,%phr,%c,%H\n"'
        elif Format=='wakati':
            FormatArg='--node-format="%m" --eos-format="\n"'
    Cmd=' '.join(['mecab -d',ModelDir,FormatArg,InFP,'>', OutFP])
    Proc=subprocess.Popen(Cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    (StdOut,StdErr)=Proc.communicate()
    Code=Proc.returncode
    SuccessP=True if Code==0 else False

    return SuccessP,StdOut,StdErr


def build_compressed_corpus(StdJpTxtFP,StdModelLoc,CmpMecabFP,Debug=0):
    # do mecab parsing with the standard text
    StdMecabFP=myModule.change_ext(StdJpTxtFP,'mecab')
    SuccessP,StdOut,StdErr=do_mecab_parse(StdJpTxtFP,StdModelLoc,Format='standard',OutFP=StdMecabFP)
    if not SuccessP:
        print('\nmecab process failed with the following error\n')
        print(StdErr)
        sys.exit()
    elif StdErr:
        print('\nmecab producing the following warning\n')
        print(StdErr.decode())
    # do compression of the above
    compress_inflecting.main0(StdMecabFP,CorpusOrDic='corpus',OutFP=CmpMecabFP,Debug=Debug)
    return CmpMecabFP
    
def main():
    import argparse
    ArgPsr=argparse.ArgumentParser(description='''
     to be written
    ''')
    ArgPsr.add_argument('raw_fp')
    ArgPsr.add_argument('dic_loc')
    ArgPsr.add_argument('--std-modeldir','-d')
    ArgPsr.add_argument('--exemplar-fp','-e')
    ArgPsr.add_argument('--freqwd-fp','-f')
    Args=ArgPsr.parse_args()

    if not os.path.isfile(Args.raw_fp):
        sys.exit('\n\n  source file not found \n')

    if not Args.std_modeldir:
        Args.std_modeldir=Args.dic_loc
    if not os.path.isdir(Args.std_modeldir):
        sys.exit('\n\n  model dir not found \n')

    if (Args.exemplar_fp is not None and not os.path.isfile(Args.exemplar_fp)) or (Args.freqwd_fp is not None and not os.path.isfile(Args.freqwd_fp)):
        sys.exit('\n\n one of the assisting files for normalisations (exemplar, freqwd) not found\n')
        
    
    main0(Args.raw_fp,Args.dic_loc,Args.std_modeldir,ExemplarFP=Args.exemplar_fp,FreqWdFP=Args.freqwd_fp)

if __name__=='__main__':
    main()
