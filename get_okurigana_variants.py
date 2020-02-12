import sys,os,imp
import count_homophones
imp.reload(count_homophones)

def main(GenHomStats,OutFP=None):
    if OutFP:
        Out=open(OutFP,'wt')
    for GenHomStat in sorted(GenHomStats,key=lambda x:x.pron):
        for Cat,HomStat in GenHomStat.homstats.items():
            if HomStat.okuriganavariant_stats:
                Cat=HomStat.cat
                for VarStat in HomStat.okuriganavariant_stats:
                    OrthFreqStrs=[];CatStrs=[]
                    for Ind,Variant,Freq in zip(VarStat.inds,VarStat.variants,VarStat.freqs):
                        OrthFreqStrs.append(Variant+' '+str(Freq))
                        CatStrs.append(','.join([HomStat.subcats[Ind],HomStat.homs[Ind].infpat,HomStat.infforms[Ind]]))
                    Out.write(' / '.join(OrthFreqStrs)+'\t')
                    Out.write(Cat+'('+' / '.join(CatStrs)+')\n')
    if OutFP:
        Out.close()

if __name__=='__main__':
    import argparse,glob,pickle
    Psr=argparse.ArgumentParser()
    Psr.add_argument('input_dir')
    Psr.add_argument('--lemmatise',action='store_true')
    Psr.add_argument('--tag-type',default='ipa')
    Psr.add_argument('--out-fp')
    Args=Psr.parse_args()
    MecabCorpusFPs=glob.glob(Args.input_dir+'/*.mecab')
    if not MecabCorpusFPs:
        print('stuff does not exist\n')
        sys.exit()

    GenHomStats=count_homophones.main(MecabCorpusFPs,TagType=Args.tag_type,LemmatiseP=Args.lemmatise)
    main(GenHomStats,OutFP=Args.out_fp)

    

