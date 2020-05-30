from torch import tensor

def main(Seq,ModelType,ModelPath):
    if ModelType=='bert':
        from transformers import BertModel,BertTokenizer

        BTsr=BertTokenizer.from_pretrained(ModelPath)
        BModel=BertModel.from_pretrained(ModelPath)
        Embs=get_bert_embeddings(Seq,BModel,BTsr)
    return Embs

def get_bert_embeddings(Orths,BModel,BTsr):
    Toks=BTsr.wordpiece_tokenizer.tokenize(''.join(Orths))
    Embs=BModel(tensor(BTsr.convert_tokens_to_ids(Toks)).unsqueeze(0))[0][0]
    return Embs,Toks


if __name__=='__main__':
    import argparse
    Psr=argparse.ArgumentParser()
    Psr.add_argument('seq')
    Psr.add_argument('model_type')
    Psr.add_argument('model_path')
    Args=Psr.parse_args()
    main(Args.seq,Args.model_type,Args.model_path)
