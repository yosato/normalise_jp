import imp,sys,os,subprocess,glob,shutil
import compress_inflecting, normalise_mecab
from pythonlib_ys import main as myModule
imp.reload(compress_inflecting)
imp.reload(normalise_mecab)

def refresh_model(DicDir,ConfDir,ModelDir):
    list(map(os.remove, glob.glob(ModelDir+'/*')))
    list(map(lambda x:shutil.copy(x,ModelDir), glob.glob(DicDir+'/*.csv')))
    list(map(lambda x:shutil.copy(x,ModelDir), glob.glob(ConfDir+'/*')))
    Cmd=' '.join(['mecab-dict-index -d',ModelDir,'-o',ModelDir])
    subprocess.call(Cmd,shell=True)

def main0(StdJpTxtFP,OrgDicLoc,ModelDir=None,ExemplarFP=None,FreqWdFP=None,Debug=0):
    #################################
    ## compression on dic and corpus
    #################################
    ### dic first ###
    # original dics to compress, inflecting categories only
    InfCats=('adjectives','verbs','auxiliaries')
    DicFPsInf=[os.path.join(OrgDicLoc,Cat+'.csv') for Cat in InfCats ]
    NewDicLoc=OrgDicLoc.replace('rawData','processedData')
    CmpDicFPs=[os.path.join(NewDicLoc,Cat+'.compressed.csv') for Cat in InfCats ]
    for (DicFPInf,CmpDicFP) in zip(DicFPsInf,CmpDicFPs):
        Ret=myModule.ask_filenoexist_execute(CmpDicFPs,compress_inflecting.main0,([DicFPInf],{'CorpusOrDic':'dic','OutFP':CmpDicFP,'Debug':Debug}))
    FreshlyDoneP=True if Ret is None else False
    # then the corpora
    # the new stuff will be in 'processedData'
    CmpMecabDir=os.path.dirname(StdJpTxtFP).replace('rawData','processedData')
    CmpMecabFN=os.path.basename(StdJpTxtFP).replace('.txt','.compressed.mecab')
    CmpMecabFP=os.path.join(CmpMecabDir, CmpMecabFN)
    ModelDir=os.path.dirname(CmpMecabDir)+'/models' if ModelDir is None else ModelDir
    if not os.path.isdir(ModelDir):
        os.path.mkdirs(ModelDir)
    if not os.path.isfile(os.path.join(ModelDir,'dicrc')) or myModule.prompt_loop_bool('Refreshing the model?',Default=True):
        ConfLoc=os.path.join(os.path.dirname(OrgDicLoc),'models')
        refresh_model(OrgDicLoc,ConfLoc,ModelDir)
    
    FreshlyDoneP=myModule.ask_filenoexist_execute(CmpMecabFP,build_compressed_corpus,([StdJpTxtFP,ModelDir,CmpMecabFP],{'Debug':Debug}),LoopBackArg=(0,2),DefaultReuse=not FreshlyDoneP)
    ###################################
    ## normalisation of the corpus
    ##################################    
    # for normalisation you include non-inflecting dic as well
    DicFPNonInf=os.path.join(OrgDicLoc,'non-inflecting.csv')
    FinalMecabFP=myModule.change_stem(CmpMecabFP,'.normed')
    # an exemplar is a word with a single dominant normalisation case
    ExemplarFP=os.path.join(OrgDicLoc,'exemplars.txt') if not ExemplarFP else ExemplarFP
    # one could limit the targets to frequent words only
    FreqWdFP=os.path.join(os.path.dirname(StdJpTxtFP),'freqwds.txt') if not FreqWdFP else FreqWdFP
    # core part
    normalise_mecab.main0([DicFPNonInf]+CmpDicFPs,[CmpMecabFP],ProbExemplarFP=ExemplarFP,FreqWdFP=FreqWdFP,OutFP=FinalMecabFP,CorpusOnly=True,UnnormalisableMarkP=True,Debug=Debug)


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


def build_compressed_corpus(StdJpTxtFP,StdModelLoc,CmpMecabFP,Debug=0):
    # do mecab parsing with the standard text
    StdMecabFP=myModule.change_ext(StdJpTxtFP,'mecab').replace('rawData','processedData')
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
    ArgPsr.add_argument('--modeldir')
    ArgPsr.add_argument('--exemplar-fp','-e')
    ArgPsr.add_argument('--freqwd-fp','-f')
    Args=ArgPsr.parse_args()

    if not os.path.isfile(Args.raw_fp):
        sys.exit('\n\n  source file not found \n')

    if (Args.exemplar_fp is not None and not os.path.isfile(Args.exemplar_fp)) or (Args.freqwd_fp is not None and not os.path.isfile(Args.freqwd_fp)):
        sys.exit('\n\n one of the assisting files for normalisations (exemplar, freqwd) not found\n')
        
    
    main0(Args.raw_fp,Args.dic_loc,ModelDir=Args.modeldir,ExemplarFP=Args.exemplar_fp,FreqWdFP=Args.freqwd_fp)

if __name__=='__main__':
    main()
