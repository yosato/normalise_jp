from pythonlib_ys import main as myModule
import re,os,sys

def main(fps,metafile):
    fnsMeta=get_file_metadata_mapping(metafile)
    for fp in fps:
        fnStem=os.path.basename(fp).split('.')[0]
        if fnStem not in fnsMeta:
            continue
        with open(fp) as fsr:
            for liNe in fsr:
                if re.match(r'.+_n\t',liNe):
                    orth,feats=liNe.strip().split('\t')[0:2]
                    mecabFeats=feats.split(',')[:3]
                    metaFeats=fnsMeta[fnStem]
                    relvMetaFeats=[myStr.strip().replace(' ','_') for (cntr,myStr) in enumerate(metaFeats) if cntr not in (3,6) ]
                    newFeats=mecabFeats+relvMetaFeats
                    kanjiOrNot='1' if myModule.all_of_chartypes_p(orth,['han']) else '0'
                    newFeats.append(kanjiOrNot)
                    sys.stdout.write(','.join([orth]+newFeats)+'\n')

def get_file_metadata_mapping(metafile):
    fnsMetas={}
    with open(metafile,'rt') as fsr:
        for cntr,liNe in enumerate(fsr):
            if cntr==0:
                continue
            lineEls=liNe.strip().split('\t')
            fn=os.path.basename(lineEls[0])
            fnsMetas[re.sub(r'^(.+)[0-9]+(_)0+([1-9])',r'\1\2\3',fn)]=tuple(lineEls[1:])
    return fnsMetas            

if __name__=='__main__':
    import argparse,glob
    psr=argparse.ArgumentParser()
    psr.add_argument('dir')
    psr.add_argument('meta_file')
    myArgs=psr.parse_args()
    fps=glob.glob(os.path.join(myArgs.dir,'*.normed'))
    if not fps:
        sys.exit()
    main(fps,myArgs.meta_file)
