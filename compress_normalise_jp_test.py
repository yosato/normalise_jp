import unittest,imp,sys,os
from pdb import set_trace

import compress_normalise_jp
imp.reload(compress_normalise_jp)

TestPairs=[
    # case of unique rendering
    ('かゆがからく成る','粥 が 辛 く なr u'),
    # case of exemplar
    ('そういわれても','そう 言w a れ て も'),
    # case of kana rendering
    ('サッパリとしたリンゴ', 'さっぱり と し た りんご'),
    # case of suffix-kana change
    ('サボったらどうなるかな','さぼr t たら どう なr u かな'),
    # case of elongation
    ('どーなってもいーや','どうなってもいいや'),
    #
    ('切込みを入れる','切り込み を 入れ る')

]


class TestCompressNormalise(unittest.TestCase):
    def setUp(self):
        HomeDir=os.getenv('HOME')
        DataDir=os.path.join(HomeDir,'links/mecabStdJp')
        self.testpairs=TestPairs
        self.testorgsents=[TestPair[0] for TestPair in TestPairs]
        self.testfp=os.path.join(DataDir,'corpora/raw/compress_normalise_test.txt')

        with open(self.testfp,'tw') as FSw:
            FSw.write('\n'.join(self.testorgsents)+'\n')

        self.exemplarfp=os.path.join(DataDir,'dics/compressed/exemplars.txt')
        self.dicloc=os.path.join(DataDir,'dics')
        self.stdmodelloc=os.path.join(DataDir,'models/standard')

    def test_compress_normalise(self):
        for (OrgLine,ExpNewLine) in self.testpairs:
            set_trace()
            ResultNewLine=compress_normalise_jp.main0(self.testfp, self.dicloc, self.stdmodelloc, ExemplarFP=self.exemplarfp)
            self.assertEqual(ResultNewLine,ExpNewLine)

if __name__=='__main__':
    unittest.main()

    
